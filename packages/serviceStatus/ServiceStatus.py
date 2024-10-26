from enum import Enum, auto


class ServiceStatus(Enum):
    SUCCESS = auto()

    ERROR_GMAIL_TOKEN_JSON = auto()  # gmail authorization by token.json error
    ERROR_GMAIL_CREDENTIALS_JSON = auto()  # gmail authorization by credentials.json error
    ERROR_GMAIL_AUTHORIZATION = auto()  # gmail authorization failed although token.json and credentials.json is good
    ERROR_GMAIL_PROXY_JSON = auto()  # gmail proxy.json error
    ERROR_GMAIL_BUILD_SERVICE_AUTHORIZED_HTTP = auto()  # gmail build service with proxy failed
    ERROR_GMAIL_BUILD_SERVICE = auto()  # gmail build service withour proxy failed
    ERROR_GMAIL_CONNECTION = auto()  # gmail connection error
    ERROR_GMAIL_GET_MESSAGE_IDS = auto()  # get email message ids failed
    ERROR_GMAIL_EMAIL_DECODE = auto()  # email decode failed

    ERROR_GPT_API_KEY = auto()  # get gpt api key failed
    ERROR_GPT_PROXY_SETUP = auto()  # setup gpt proxy failed
    ERROR_GPT_QUERY = auto()  # gpt query failed

    ERROR_MONGODB_PASSWORD = auto()  # get mongodb password failed
    ERROR_MONGODB_CONNECTION = auto()  # connect mongodb failed
    ERROR_MONGODB_CLOSE = auto()  # close mongodb failed
    ERROR_MONGODB_INSERT = auto()  # insert mongodb failed
    ERROR_MONGODB_UPDATE = auto()  # update mongodb failed
    ERROR_MONGODB_FIND = auto()  # Get data in mongodb failed
    ERROR_MONGODB_CANNOT_DECIDE_NEW_ORDER = auto()  # get previous order failed, so cannot decide wether it is a new order
    ERROR_MONGODB_ADD_ORDER = auto()  # add order error
    ERROR_MONGODB_UPDATE_ORDER = auto()  # update order error

