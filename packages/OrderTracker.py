from packages.gmail.GmailClient import GmailClient
from packages.gpt.GptClient import GptClient
from packages.mongodb.MongodbClient import MongodbClient
from packages.serviceStatus.ServiceStatus import ServiceStatus
from packages.logger.Logger import Logger
import json
import os


class OrderTracker():
    def __init__(self):
        self.__prompt = """Retrieve the inforation from the following email. 
        You should get the brand name, order number, date, order total, item name, item color, item size, item quantity, order status, tracking number, and carrier. For the order status, you only have four options: canceled, confirmed, shipped, delivered. For the carrier, you only have three options: UPS, Fedex, None.
        Here are procedures: 
            1. Anything you cannot get from email, set as Unknown.
            2. Collect brand name, order number, date, order total, item name, item color, item size, item quantity from email.
            3. Check whether there is a tracking number in email. Use Fedex and UPS tracking number principles, Fedex tracking number is consist of 12 digits and UPS tracking number is consist of 18 characters starting with 1Z, as assistance.
            4. If there is a tracking number in email: set order status as shipped, set tracking number as the tracking number you find. If the tracking number is only consist of 12 digits, set carrier as Fedex. If the tracking number is consist of 18 characters starting with 1Z, set carrier as UPS
            5. If there is not a tracking number in email: set tracking number as Unknown, set carrier as Unknown. You should not set order status as shipped if there is not tracking number in email.
            6. Set the order status according to the context of email. Remember if there is not tracking number, do not set the order status as shipped.
            7. Set the date as the date receiving email with mm/dd/yy format.
        Your response should follow the following json format:
        {
            "brand": brand name,
            "date": date(format: mm/dd/yy),
            "number": order number,
            "total": order total,
            "status": order status,
            "tracking number": tracking number,
            "carrier": carrier,
            "item": [
            {
                "name": item name,
                "color": item color,
                "size": item size,
                "quantity": item quantity
            },
            ...
            ]
        }
"""
        self.__gmail_client = None
        self.__gpt_client = None
        self.__mongodb_client = None

        dir = os.path.dirname(os.path.abspath(__file__))
        self.__logger = Logger(logger_dir=dir+"/logger")

    def __activate_client(self):
        """Activate Gmail client, Gpt Client, and MongoDB client

        Returns:
            enum object: service status code
        """
        self.__gmail_client = GmailClient()
        code = self.__gmail_client.start()
        if code is not ServiceStatus.SUCCESS:
            print("Gmail connection failed. Please check network and open VPN.")
            return code

        self.__gpt_client = GptClient()
        code = self.__gpt_client.start()
        if code is not ServiceStatus.SUCCESS:
            print("Gpt connection failed. Please check network and open VPN.")
            return code
        
        self.__mongodb_client = MongodbClient()
        code = self.__mongodb_client.start()
        if code is not ServiceStatus.SUCCESS:
            print("MongoDB connection failed. Please check network and open VPN.")
            return code
        
        return code

    def __query(self, email_text, output=False):
        """Query Gpt with prompt

        Args:
            email_text (str): email text
            output (bool, optional): print gpt answer in json format if True. Defaults to False.

        Returns:
            tuple: (Gpt answer in json format, service status code)
        """
        answer, code = self.__gpt_client.query(self.__prompt + "\n" + email_text)
        if code is not ServiceStatus.SUCCESS:
            return {}, code

        answer = answer.replace("```json\n", "").replace("\n```", "")
        if output:
            print(answer)
        
        return json.loads(answer), ServiceStatus.SUCCESS
    
    def run(self):
        """Only api for external to run the whole service from getting email, then querying gpt, and upload to MongoDB finally.
        """
        self.__logger.info(f"Service start")
        code = self.__activate_client()
        if code is not ServiceStatus.SUCCESS:
            self.__logger.error(code)
            return code
        
        message_ids, code = self.__gmail_client.get_message_ids()
        if code is not ServiceStatus.SUCCESS:
            self.__logger.error(code)
            return code
        
        failed_ids = []
        for id in message_ids:
            self.__logger.info(f"Dealing with email {id}")
            email_text, code = self.__gmail_client.decode_message(id)
            if code is not ServiceStatus.SUCCESS:
                failed_ids.append(id)
                self.__logger.warning(f"Decoding failed - {code}")
                continue

            order_info, code = self.__query(email_text, output=False)
            if code is not ServiceStatus.SUCCESS:
                failed_ids.append(id)
                self.__logger.warning(f"Query gpt failed - {code}")
                continue
            
            code = self.__mongodb_client.upload_order(order_info)
            if code is not ServiceStatus.SUCCESS:
                failed_ids.append(id)
                self.__logger.warning(f"Upload to MongoDB failed - {code}")
                continue
            
        self.__logger.info("Completed")

        self.__logger.critical(f"Failed email id - {failed_ids}")

        code = self.__mongodb_client.closeClient()
        if code is not ServiceStatus.SUCCESS:
            self.__logger.error(code)
        self.__logger.info(f"Service end")
        return code
    
    def find_menually(self, filter = {"$and": [{"Transshipment": "Unknown"}, {"$or": [{"status":"shipped"}, {"status": "delivered"}]}]}):
        """Find order menually using customized filter

        Args:
            filter (dict, optional): _description_. Defaults to {"": [{"Transshipment": "Unknown"}, {"": [{"status":"shipped"}, {"status": "delivered"}]}]}.
            ## Get shipped or delivered but not transshipped order to check transshipped status: {"$and": [{"Transshipment": "Unknown"}, {"$or": [{"status":"shipped"}, {"status": "delivered"}]}]}
        Returns:
            enum object: service status code
        """
        self.__mongodb_client = MongodbClient()
        code = self.__mongodb_client.start()
        if code is not ServiceStatus.SUCCESS:
            print("MongoDB connection failed. Please check network and open VPN.")
            return code
        
        orders, code = self.__mongodb_client.find_shippment_menually()
        if code is not ServiceStatus.SUCCESS:
            return code
        
        for order in orders:
            print(order["number"])
        


  