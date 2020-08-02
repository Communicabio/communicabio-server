import json
import random
from schemes import Phrase
from typing import List

class Manager:
    def __init__(self, lang: str):
        self.lang = lang
        with open(f"assets/dialog-{lang}.json") as file:
            self.dialogs = json.load(file)

    def start(self) -> Phrase:
        return Phrase(text=random.choice(self.dialogs))

    def reply(self, history: List[Phrase]) -> Phrase:
        # ...
        return history[-1]
