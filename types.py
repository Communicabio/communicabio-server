import pymongo
from pydantic import BaseModel
from typing import Optional, Tuple, List
from json import JSONEncoder
import json

def _default(self, obj):
    return getattr(obj.__class__, "toJSON", _default.default)(obj)

_default.default = JSONEncoder().default
JSONEncoder.default = _default

class Id(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not isinstance(v, ObjectId) and not isinstance(v, str):
            raise TypeError('ObjectId required')
        try:
            res = Id(v)
            return res
        except bson.errors.InvalidId:
            logging.warning(f'{v} is not ObjectId')
            raise TypeError(f'{v} is not ObjectId')


    @classmethod
    def __modify_schema__(cls, schema):
        schema.update({
            'Title': 'MongoDB ObjectID',
            'type': 'string'
        })

    def toJSON(self):
        return str(self)

ObjectId.toJSON = Id.toJSON

class Phrase(BaseModel):
    _id: Optional[Id]
    text: str
    author: Optional[Id]
    politeness: Optional[float]
    positivity: Optional[float]

    class Config:
        extra = pydantic.Extra.allow

class User(BaseModel):
    _id: Optional[Id]
    state: int = 0
    name: str
    user_id: int
    dialog: List[Phrase] = []

    class Config:
        extra = pydantic.Extra.allow

class Dialog(BaseModel):
    _id: Optional[Id]
    phrases: List[Phrase]
    politeness: Optional[float]
    positivity: Optional[float]

    class Config:
        extra = pydantic.Extra.allow
