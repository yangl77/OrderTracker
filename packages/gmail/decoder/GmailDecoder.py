import base64 
import re


class GmailDecoder():
    def __init__(self):
        pass

    def decode_message(self, message, remove_link=True):
        """Decode a string

        Args:
            message (str): encoded string
            remove_link (bool, optional): remove the http/https links in decoded string if True. Defaults to True.

        Returns:
            str: decoded string
        """
        part = message.get('payload').get('parts')[0]
        data = part.get('body').get('data')
        data = data.replace("-","+").replace("_","/") 
        decoded_data = base64.b64decode(data)
        decoded_string = decoded_data.decode('utf-8')

        if remove_link:
            decoded_string = self.__remove_http_links(decoded_string)

        return decoded_string

    def __remove_http_links(self, text):
        """Remove http/https link in a text

        Args:
            text (str): The text waiting for removing links.

        Returns:
            str: text without links
        """
        pattern = r'<https?://[^>]+>|https?://\S+'
        cleaned_text = re.sub(pattern, '', text)
        return cleaned_text.strip()