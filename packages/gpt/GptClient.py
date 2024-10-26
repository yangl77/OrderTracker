import requests
import os
import json
from ..serviceStatus.ServiceStatus import ServiceStatus


class GptClient():
    def __init__(self):
        self.__api_key = None
        self.__proxies = None

    def __start(self):
        """Setup api key and proxy used for gpt authorization and connection

        Returns:
            enum oject: service status code
        """
        try:
            dir = os.path.dirname(os.path.abspath(__file__))
            with open(dir+'/authorization/api_key.json', 'r') as file:
                key = json.load(file)
            self.__api_key = key['key']
        except Exception as e:
            print(f"api_key.json file error: {e}")
            return ServiceStatus.ERROR_GPT_API_KEY

        try:
            dir = os.path.dirname(dir)
            with open(dir+'/proxy.json', 'r') as file:
                proxy = json.load(file)
            self.__proxies = {
                'http': f'http://{proxy['ip']}:{proxy['port']}',
                'https': f'https://{proxy['ip']}:{proxy['port']}',
                }
        except Exception as e:
            print(f"proxy.json file error: {e}")
            return ServiceStatus.ERROR_GPT_PROXY_SETUP
        
        return ServiceStatus.SUCCESS

    def start(self):
        """Repeatedlly setup if failed. Up tp five times.

        Returns:
            enum objcet: service status code
        """
        for i in range(5):
            code = self.__start()
            if code is ServiceStatus.SUCCESS:
                print("Gpt connected.")
                break

        return code

    def __query(self, message): 
        """Query Gpt model

        Args:
            message (string): prompt

        Returns:
            tuple: (gpt answer, service status code)
        """
        url = 'https://api.openai.com/v1/chat/completions'
        headers = {
            'Authorization': f'Bearer {self.__api_key}',
            'Content-Type': 'application/json',
        }

        data = {
            'model': 'gpt-4o-mini', 
            'messages': [
                {'role': 'user', 'content': message}
            ]
        }

        session = requests.Session()
        session.proxies.update(self.__proxies)

        try:
            response = session.post(url, headers=headers, json=data)
            response_data = response.json()
            answer = response_data['choices'][0]['message']['content']
            return answer, ServiceStatus.SUCCESS
        except requests.exceptions.HTTPError as http_err:
            print(f"Gpt query failed(HTTP error occurred): {http_err}") 
        except requests.exceptions.ConnectionError as conn_err:
            print(f"Gpt query(Error connecting to the API): {conn_err}")  
        except requests.exceptions.Timeout as timeout_err:
            print(f"Gpt query(Request timed out): {timeout_err}") 
        except json.JSONDecodeError:
            print("Gpt query(Failed to parse JSON from the response.)")
        except Exception as e:
            print(f"Gpt query: {e}")
        
        return None, ServiceStatus.ERROR_GPT_QUERY 
    
    def query(self, message):
        """Repeatedly query gpt if connection failed or get invalid response. Up to five time.

        Args:
            message (string): prompt

        Returns:
            tuple: (gpt answer, service status code)
        """
        for i in range(5):
            answer, code = self.__query(message)
            if code is ServiceStatus.SUCCESS:
                break
            print(f"Gpt query retry {i}")

        return answer, code