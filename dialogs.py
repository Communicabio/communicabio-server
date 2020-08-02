import json
import random
from types import Phrase

class Manager:
    def __init__(lang):
        self.lang = lang
        with open(f"assests/dialog-{lang}.json") as file:
            self.dialogs = json.load(file)

    def start() -> Phrase:
        return Phrase(text=random.choice(self.dialogs))

    def reply(history: List[Phrase], last: Phrase) -> Phrase:
        # ...
        return last;
