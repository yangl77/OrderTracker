import os
import httplib2
import json
import google_auth_httplib2
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.errors import HttpError
from .decoder.GmailDecoder import GmailDecoder
from ..serviceStatus.ServiceStatus import ServiceStatus
# from ..logger.Logger import Logger


class GmailClient:
    def __init__(self):
        self.__service = None
        self.__user_id = 'me'
        self.__scopes = ["https://www.googleapis.com/auth/gmail.readonly"]
        self.__decoder = GmailDecoder()

        # dir = os.path.dirname(os.path.abspath(__file__))
        # dir = os.path.dirname(os.path.abspath(dir))
        # self.__logger = Logger(logger_dir=dir+"/logger")

    def __authorization(self):
        """Create gmail api authorization token and save to json.

        Returns:
            tuple: (credentials object, service status code)
        """
        creds = None
        dir = os.path.dirname(os.path.abspath(__file__))
        creds_path = dir + '/authorization/credentials.json'
        token_path = dir + '/authorization/token.json'

        try:
            if os.path.exists(token_path):
                creds = Credentials.from_authorized_user_file(token_path, self.__scopes)
        except Exception as e:
            print(f"Using token.json to authorize failed: {e}")
            return creds, ServiceStatus.ERROR_GMAIL_TOKEN_JSON

        try:
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    flow = InstalledAppFlow.from_client_secrets_file(creds_path, self.__scopes)
                    creds = flow.run_local_server(port=0)
                with open(token_path, "w") as token:
                    token.write(creds.to_json())
        except Exception as e:
            print(f"Using credentials.json to authorize failed: {e}")
            return None, ServiceStatus.ERROR_GMAIL_CREDENTIALS_JSON
        
        return creds, ServiceStatus.SUCCESS

    def __start(self, open_proxy=True):
        """Gmail api authorization process.

        Args:
            open_proxy (bool, optional): enable proxy to request gmail api. Defaults to True.

        Returns:
            Enum object: service status code
        """
        creds, code = self.__authorization()
        if code is not ServiceStatus.SUCCESS:
            return code
        if creds is None:
            return ServiceStatus.ERROR_GMAIL_AUTHORIZATION

        if open_proxy:
            try:
                dir = os.path.dirname(os.path.abspath(__file__))
                with open(os.path.dirname(dir)+"/proxy.json", 'r') as file:
                    proxy = json.load(file)
            except Exception as e:
                print(f"Proxy file error: {e}")
                return ServiceStatus.ERROR_GMAIL_PROXY_JSON

            try:
                http = httplib2.Http(proxy_info=httplib2.ProxyInfo(
                    httplib2.socks.PROXY_TYPE_HTTP, proxy['ip'], proxy['port']
                    ))
                authorized_http = google_auth_httplib2.AuthorizedHttp(creds, http=http)
                self.__service = build("gmail", 'v1', http=authorized_http)
            except Exception as e:
                print(f"Gmail authorization by proxy failed: {e}")
                return ServiceStatus.ERROR_GMAIL_BUILD_SERVICE_AUTHORIZED_HTTP
        else:
            try:
                self.__service = build("gmail", "v1", credentials=creds)
            except Exception as e:
                print(f"Gmail authorization failed: {e}")
                return ServiceStatus.ERROR_GMAIL_BUILD_SERVICE
        
        try:  #test connection
            results = self.__service.users().labels().list(userId="me").execute()
            results.get("labels", [])
            print("Gmail connected.")
            return ServiceStatus.SUCCESS
        except HttpError as e:
            print(f"Connect Gmail failed(HttpError): {e}")
        except Exception as e:
            print(f"Connect Gmail failed: {e}")
        
        return ServiceStatus.ERROR_GMAIL_CONNECTION

    def start(self):
        """An api for external to start a gmail client and connect to gmail service.

        Returns:
            Enum object: service status code 
        """
        for i in range(5):
            code = self.__start()
            if code is ServiceStatus.SUCCESS:
                return ServiceStatus.SUCCESS
            print(f"Gmail connection retry {i}")

        return code

    def __get_message_ids(self, labelIds=['UNREAD']):
        """Get the message ids from gmail under specific labels

        Args:
            labelIds (list, optional): Gmail labels. Defaults to ['UNREAD'].

        Returns:
            tuple: (list of message id, service status code)
        """
        try:
            messages = self.__service.users().messages().list(userId=self.__user_id, labelIds=labelIds).execute()
            return messages.get("messages", []), ServiceStatus.SUCCESS
        except HttpError as e:
            print(f"Get message ids failed(HttpError): {e}")
        except Exception as e:
            print(f"Get message ids failed: {e}")
        
        return [], ServiceStatus.ERROR_GMAIL_GET_MESSAGE_IDS
        
    def get_message_ids(self, labelIds=['UNREAD']):
        """A decorator of self.__get_message_ids.
        If get message ids failed, try again up to five times.

        Args:
            labelIds (list, optional): Gmail labels. Defaults to ['UNREAD'].

        Returns:
            tuple: (email ids, service status code)
        """
        for i in range(5):
            message_ids, code = self.__get_message_ids(labelIds)
            if code is ServiceStatus.SUCCESS:
                break
            print(f"Get email ids retry {i}")

        return message_ids, code

    def __decode_message(self, message_id, format='full', remove_link=True):
        """Get encoded email from gmail and decoded it to text.

        Args:
            message_id (String): email id
            format (str, optional): email format get from gmail. Defaults to 'full'.
            remove_link (bool, optional): remove the link in decoded email if set as True. Defaults to True.

        Returns:
            tuple: (email text, service status code)
        """
        try:
            message = self.__service.users().messages().get(userId=self.__user_id, id=message_id['id'], format=format).execute()
            text = self.__decoder.decode_message(message, remove_link)  
            return text, ServiceStatus.SUCCESS
        except HttpError as e:
            print(f"Decode message failed(HttpError): {e}")
        except Exception as e:
            print(f"Decode message failed: {e}")
        
        return None, ServiceStatus.ERROR_GMAIL_EMAIL_DECODE
    
    def decode_message(self, message_id, format='full', remove_link=True):
        """Get encoded email from gmail and decode it into text. Try up to five times if failed.

        Args:
            message_id (String): email id
            format (str, optional): email format get from gmail. Defaults to 'full'.
            remove_link (bool, optional): remove the link in decoded email if set as True. Defaults to True.

        Returns:
            tuple: (email text, service status code)
        """
        for i in range(5):
            text, code = self.__decode_message(message_id, format, remove_link)
            if code is ServiceStatus.SUCCESS:
                break
            print(f"Decode message retry {i}")
            
        return text, code