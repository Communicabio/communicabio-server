import json
import random
from schemes import Phrase
from typing import List
import pymongo
import requests
import logging

def request_auth(url):
    """
    https://cloud.google.com/run/docs/authenticating/service-to-service#console-ui
    """
    receiving_service_url = url
    metadata_server_token_url = f'http://metadata/computeMetadata/v1/instance/service-accounts/default/identity?audience='
    token_request_url = metadata_server_token_url + receiving_service_url
    token_request_headers = {'Metadata-Flavor': 'Google'}

    # Fetch the token
    token_response = requests.get(token_request_url, headers=token_request_headers)
    jwt = token_response.content.decode("utf-8")
    # Provide the token in the request to the receiving service
    receiving_service_headers = {'Authorization': f'bearer {jwt}'}
    return receiving_service_headers

class Manager:
    gpt2links = {
        'en': 'https://en-gpt2-ervice-pcdqvqhk7q-uc.a.run.app'
    }
    def __init__(self, mongo_url: str, lang: str):
        self.lang = lang
        self.client = pymongo.MongoClient(mongo_url)
        self.db = self.client[f'communicabio-{lang}']
        with open(f'assets/dialog-{lang}.json') as file:
            self.dialogs = json.load(file)
        self.gpt2_headers = request_auth(self.gpt2links[lang])
        logging.info(self.gpt2_headers)
        #self.dialogs = self.db['dialogs-vectorized']

    def start(self) -> Phrase:
        return Phrase(text=random.choice(self.dialogs))

    def reply(self, history: List[Phrase]) -> Phrase:
        # ...
        resp = requests.post(self.gpt2links[self.lang],
                    json={'history': [el.text for el in history]},
                    headers=self.gpt2_headers)
        if resp.status_code != 200:
            logging.warning(resp.text)
            resp.raise_for_status()
        return Phrase(text=resp.json()['text'])
