import re
import spacy

nlp = spacy.load("en_core_web_sm")

class Analyzer:
    def __init__(self, logger=None):
        self.logger = logger

    def extract_keywords(self, text):
        doc = nlp(text)
        keywords = set()
        for token in doc:
            # self.logger.info(f'checking token: {token}')
            base = token.text.lower().strip()
            bare = re.sub(r'\W+', '', base)
            
            is_email = re.match(r"[^@]+@[^@]+\.[^@]+", base) is not None
            # is_url = re.match(r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))", base) is not None
            is_url = re.match(r"(https?://[^\s]+)", base) is not None
            is_number = re.match(r"^\d+([,.]\d+)*$", bare) is not None                        
            is_symbol = bool(token.pos_ == 'SYM')
            is_phone = re.match(r"(\+?\d{1,4}?[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?)?\d{3}[-.\s]?\d{4}", base) is not None
            is_symbol = token.pos_ == 'SYM' or bare in ['+', '-', '*', '/', '=']  # Add specific symbols as needed
            is_hexadecimal = re.match(r"^(0[xX])?[0-9a-fA-F]+$", base) is not None
            is_punct = token.is_punct or bare in [",", ".", "/", "(", ")", "[", "]", "{", "}", "<", ">", "'", '"']
            is_time = re.match(r"^\d{1,2}:\d{2}([ap]m)?$", bare) is not None
            
            skip = bool(token.is_stop)
            skip = skip or token.text.isdigit()
            skip = skip or token.text.strip() == ""
            skip = skip or is_punct
            skip = skip or is_number
            skip = skip or is_symbol
            skip = skip or is_email
            skip = skip or is_url
            skip = skip or is_phone
            skip = skip or is_hexadecimal
            skip = skip or is_time

            # if token.text.strip() == "+":
            #     print(f'{token} : is_stop: {token.is_stop}')
            #     print(f'{token} : is_punct: {is_punct}')
            #     print(f'{token} : symbol: {is_symbol}')
            #     print(f'{token} : isdigit: {token.text.isdigit()}')
            #     print(f'{token} : is empty: {token.text.strip() == ""}')
            #     print(f'{token} : is number: {is_number}')
            #     print(f'{token} : is email: {is_email}')
            #     print(f'{token} : is url: {is_url}')            
            #     print(f'{token} : is phone: {is_phone}')            
            #     print(f'{token} : is hexadecimal: {is_hexadecimal}')            
            #     print(f'{token} : skip: {skip}')

            if not skip:
                keywords.add(base)

            # self.logger.info(' - token handled')
        return keywords