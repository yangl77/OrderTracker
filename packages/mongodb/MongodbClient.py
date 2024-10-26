import os
import json
from datetime import datetime
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from ..serviceStatus.ServiceStatus import ServiceStatus


class MongodbClient():
    def __init__(self):
        self.__client = None
        self.__order_details = None
        self.__order_shippment = None

    def __start(self):
        """Authorize mongodb and test connection

        Returns:
            enum object: service status code
        """
        try:
            dir = os.path.dirname(os.path.abspath(__file__))
            with open(dir+'/authorization/password.json', 'r') as file:
                password = json.load(file)
            uri = f"mongodb+srv://fred7liu:{password["password"]}@order.dg7r9.mongodb.net/?retryWrites=true&w=majority&appName=order"
            self.__client = MongoClient(uri, server_api=ServerApi('1'))
        except Exception as e:
            print(f"Load password.json failed: {e}")
            return ServiceStatus.ERROR_MONGODB_PASSWORD

        try:  # test connection
            self.__client.admin.command('ping')
            print("MongoDB connected.")

            order_status_db = self.__client["order-status"]
            self.__order_details = order_status_db["order-details"]   
            self.__order_shippment = order_status_db["order-shippment"]

            item_db = self.__client['item']
            self.__item_details = item_db['item-details']

            return ServiceStatus.SUCCESS
        except Exception as e:
            print(f"Connect MongoDB failed: {e}")
        
        return ServiceStatus.ERROR_MONGODB_CONNECTION

    def start(self):
        """Authorize mongodb and test connection. Retry up to five times if failed

        Returns:
            enum object: service status code
        """
        for i in range(5):
            code = self.__start()
            if code is ServiceStatus.SUCCESS:
                break
            print(f"MongoDB connection retry {i}")
        
        return code

    def __closeClient(self):
        """Close MongoDB client

        Returns:
            enum object: service status code
        """
        try:
            self.__client.close()
        except Exception as e:
            print(f"Close MongoDB failed: {e}")
            return ServiceStatus.ERROR_MONGODB_CLOSE

        return ServiceStatus.SUCCESS

    def closeClient(self):
        """Close MongoDB client. Retry up to five times if failed.

        Returns:
            enum object: service status code
        """
        for i in range(5):
            code = self.__closeClient()
            if code is ServiceStatus.SUCCESS:
                break
            print(f"Close MongoDB client retry {i}")
        
        return code

    def __insert(self, collection, data):  #only support insert one so far to avoid insert by mistake.
        """Insert data into MongoDB

        Args:
            collection (mongo db object): mongodb collection
            data (dict): data to be inserted

        Returns:
            enum object: service status code
        """
        try:
            if collection.insert_one(data).acknowledged:
                return ServiceStatus.SUCCESS
        except Exception as e:
            print(f"Insert MongoDB failed: {e}")
        
        return ServiceStatus.ERROR_MONGODB_INSERT

    def __update(self, collection, filter, date):  #only support update one so far to avoid updating many by mistake.
        """Update the data in mongodb

        Args:
            collection (mongodb object): mongodb database collection
            filter (dict): used for filtering the data you want to update
            date (dict): the data part you want to update

        Returns:
            enum: service status code
        """
        try:
            if collection.update_one(filter, { '$set' : date}).acknowledged:
                return ServiceStatus.SUCCESS
        except Exception as e:
            print(f"Update MongoDB failed: {e}")
        
        return ServiceStatus.ERROR_MONGODB_UPDATE

    def __find_one(self, collection, filter):
        """Get data from MongoDB

        Args:
            collection (mongodb object): MongoDB database collection
            filter (dict): Used for filtering the data you want to get

        Returns:
            tuple: (data from mongodb, service status code)
        """
        try:
            result = collection.find_one(filter, max_time_ms=10000)  #  10s
            return result, ServiceStatus.SUCCESS
        except Exception as e:
            print(f"Find order failed: {e}")
        
        return None, ServiceStatus.ERROR_MONGODB_FIND
        
    def __get_order_shippment_by_order_number(self, order_number):
        """Get data from order shippment collection by using order number. Retry up to five times if failed

        Args:
            order_number (str): order number

        Returns:
            tuple: (order data, service status code)
        """
        filter = {"number": order_number}
        for i in range(5):
            data, code = self.__find_one(self.__order_shippment, filter)
            if code is ServiceStatus.SUCCESS:
                break
            print(f"Find previous order retry {i}")

        return data, code
    
    def upload_order(self, order):
        is_new_order = True

        order_previous, code = self.__get_order_shippment_by_order_number(order["number"])
        if code is not ServiceStatus.SUCCESS:
            #  Do not return code directly because we wanna emphasized we cannot decide whether it is new order.
            #  We do not wanna add or update data if we cannot figure out it existence in database. 
            return ServiceStatus.ERROR_MONGODB_CANNOT_DECIDE_NEW_ORDER
        if order_previous is not None:
            is_new_order = False
        
        if is_new_order:
            code = self.__add_new_order(order)
        else:
            code = self.__update_order(order_previous, order)

        return code

    def __valid_order_sequence(self, order_previous, order):
        """Validate order sequence to avoid old status cover new status

        Args:
            order_previous (dict): existed order info in MongoDB
            order (dict): current oder info

        Returns:
            Bool: Return True is sequence is valid
        """
        status_sequence = {"confirmed": 0, "canceled": 1, "shipped": 2, "delivered": 3}
        if datetime.strptime(order["date"], "%m/%d/%y") < datetime.strptime(order_previous['Last update'], "%m/%d/%y"):
            print(f"Order {order["number"]} is already in latest status.")
            return False
        
        if status_sequence[order["status"]] < status_sequence[order_previous["status"]]:
            print(f"Order {order["number"]} is already in latest status.")
            return False
        
        return True

    def __update_order(self, order_previous, order):
        if not self.__valid_order_sequence(order_previous, order):
            return ServiceStatus.SUCCESS

        for i in range(5):
            code_details = self.__update_order_details(order_previous, order)
            if code_details is ServiceStatus.SUCCESS:
                break
        for i in range(5):
            code_shippment = self.__update_order_shippment(order_previous, order)
            if code_shippment is ServiceStatus.SUCCESS:
                break
        
        if code_details is not ServiceStatus.SUCCESS or code_shippment is not ServiceStatus.SUCCESS:
            print(f"Update order {order["number"]} failed. Please check manually.")
            return ServiceStatus.ERROR_MONGODB_UPDATE_ORDER

        return ServiceStatus.SUCCESS

    def __update_order_details(self, order_previous, order):
        """Update order details

        Args:
            order_previous (dict): existed order info in MongoDB
            order (dict): current order info

        Returns:
            enum object: service status number
        """
        filter = {"number": order["number"]}
        update = {}
        if order_previous["status"] != order["status"]:
            update["status"] = order["status"]

        code = self.__update(self.__order_details, filter, update)
        return code
    
    def __update_order_shippment(self, order_previous, order):
        """Update order shippemt 

        Args:
            order_previous (dict): existed order info in MongoDB
            order (dict): current order info

        Returns:
            enum object: service status number
        """
        filter = {"number": order["number"]}
        update = {}
        update["Last update"] = order["date"]

        if order_previous["status"] != order["status"]:
            update["status"] = order["status"]
        if order_previous["tracking number"] == "Unknown" and order["tracking number"] != "Unknown":
            update["tracking number"] = order["tracking number"]
            update["carrier"] = order["carrier"]

        code = self.__update(self.__order_shippment, filter, update)
        return code

    def __add_new_order(self, order):
        """Add order to order details and shippemt collection

        Args:
            order (dict): order info

        Returns:
            enum object: service status number
        """
        for i in range(5):
            code_details = self.__add_order_details(order)
            if code_details is ServiceStatus.SUCCESS:
                break
        for i in range(5):
            code_shippment = self.__add_order_shippment(order)
            if code_shippment is ServiceStatus.SUCCESS:
                break
        
        if code_details is not ServiceStatus.SUCCESS or code_shippment is not ServiceStatus.SUCCESS:
            print(f"Add a new order {order["number"]} failed. Please check manually.")
            return ServiceStatus.ERROR_MONGODB_ADD_ORDER
        
        return ServiceStatus.SUCCESS
    
    def __add_order_details(self, order):
        """Add order details to order details collection

        Args:
            order (dict): order info

        Returns:
            enum object: service status number
        """
        order_details = {
            "brand": order["brand"],
            "date": order["date"],
            "number": order["number"],
            "total": order["total"],
            "item": order["item"],
            "status": order["status"]
        }
        code = self.__insert(self.__order_details, order_details)
        return code
    
    def __add_order_shippment(self, order):
        """Add order details to order shippment collection

        Args:
            order (dict): order info

        Returns:
            enum object: service status number
        """
        order_shippment = {
            "number": order["number"],
            "Last update": order["date"],
            "status": order["status"],
            "tracking number": order["tracking number"],
            "carrier": order["carrier"],
            "Trans carrier": "Unknown",
            "Package number": "Unknown"
        }
        code = self.__insert(self.__order_shippment, order_shippment)
        return code

    def find_shippment_menually(self, filter):
        """Find shippment menually

        Args:
            filter (dict): filter for getting specific order shippment info

        Returns:
            tuple: (order shippment info, code)
        """
        return self.__find(self.__order_shippment, filter)
    
    def update_order_transshippment_menually(self, order_number, trans_carrier, package_number):
        """Update order transshipment info

        Args:
            order_number (str): order number
            trans_carrier (str): transshioment carrier name
            package_number (str): package number from transshipment carrier

        Returns:
            enum object: service status code
        """
        filter = {"order number": order_number}
        update = {
            "trans carrier": trans_carrier,
            "package number": package_number
        }

        return self.__update(self.__order_shippment, filter, update)
    