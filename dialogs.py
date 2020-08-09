import json
import random
from schemes import Phrase
from typing import List
import pymongo
import requests
import logging

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
        #self.dialogs = self.db['dialogs-vectorized']

    def start(self) -> Phrase:
        return Phrase(text=random.choice(self.dialogs))

    def reply(self, history: List[Phrase]) -> Phrase:
        # ...
        resp = requests.post(self.gpt2links[self.lang],
                    {'history': [el.text for el in history]})
        if resp.status_code != 200:
            logging.warning(resp.text)
            resp.raise_for_status()
        return Phrase(text=resp.json()['text'])
