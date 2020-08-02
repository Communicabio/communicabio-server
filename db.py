import pymongo
from pydantic import BaseModel
from typing import Optional, Tuple, List
from json import JSONEncoder
import json
import logging
from schemes import *

class MongoDB:
    def __init__(self, url: str, lang: str ='en'):
        self.client = pymongo.MongoClient(url)
        self.app = self.client[f'communicabio-{lang}']
        self.users = self.app['users']
        self.dialogs = self.app['dialogs']

    def fetch_user(self, user_id: int, name: Optional[str]) -> User:
        result = self.users.find_one({'user_id': user_id});
        if result is None:
            user = User(user_id=user_id, name=name)
            user._id = self.users.insert_one(user.dict()).inserted_id
            return user
        return User(**result)

    def add_phrase(self, user: User, phrase: Phrase) -> User:
        self.users.update_one({'_id': user._id}, {'$push': {'dialog': phrase.dict()},
                                                  '$set': {'state': 1}})
        user.dialog.append(phrase)
        return user

    def finish_dialog(self, user: User) -> Tuple[User, Dialog]:
        attrs = ['politeness', 'positivity'];
        dialog = Dialog(phrases=user.dialog)
        for attr in attrs:
            cnt = 0
            total = 0
            for phrase in user.dialog:
                if getattr(phrase, attr) is None:
                    continue
                cnt += 1
                total += getattr(phrase, attr)
            if cnt != 0:
                setattr(dialog, attr, total / cnt)
        self.dialogs.insert_one(dialog.dict());
        logging.debug(self.users.find_one({'_id': user._id}))
        self.users.update_one({'_id': user._id}, {'$set': {'dialog': [], 'state': 0}})
        logging.debug(type(user._id))
        user.dialog = []
        user.state = 0
        return (user, dialog)
