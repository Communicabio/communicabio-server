import asyncio
import contextlib

import nltk
import pymorphy2

from util import ApiClient

MORPH = pymorphy2.MorphAnalyzer()


class MetricSet:
    def __init__(self, coherence, positivity, politeness, coherence_mistakes=[], \
                    positivity_mistakes=[], politeness_mistakes=[]):
        self.coherence = coherence
        self.positivity = positivity
        self.politeness = politeness
        self.coherence_mistakes = coherence_mistakes
        self.positivity_mistakes = positivity_mistakes
        self.politeness_mistakes = politeness_mistakes

    @property
    def score(self):
        return (self.positivity + self.politeness) / 2

    def as_dict(self):
        return {
            "coherence": {
                "score": self.coherence,
                "mistakes": self.coherence_mistakes,
            },
            "positivity": {
                "score": self.positivity,
                "mistakes": self.positivity_mistakes,
            },
            "politeness": {
                "score": self.politeness,
                "mistakes": self.politeness_mistakes,
            }
        }


class MockClient:
    async def evaluate(self, messages):
        return MetricSet(1.0, 1.0, 1.0)


class Client(ApiClient):
    mock = MockClient

    def __init__(self, pool, session, api, obscene_words, polite_words):
        super().__init__(session, api)
        self.pool = pool
        self.obscene_words = obscene_words
        self.polite_words = polite_words

    @classmethod
    def connect(cls, pool, session, api, obscene_words, polite_words):
        if api is None:
            return cls.mock()
        else:
            return Client(pool, session, api, obscene_words, polite_words)

    async def evaluate(self, messages):

        results = await asyncio.gather(*map(self.__evaluate_dialog,
                                [(messages, metric) for metric in ["positivity", "politeness"]]))

        positivity_mistakes = results[0]['mistakes']
        politeness_mistakes = results[1]['mistakes']
        positivity_score = results[0]['score']
        politeness_score = results[1]['score']

        return MetricSet(
            1,
            positivity_score,
            politeness_score,
            positivity_mistakes=positivity_mistakes,
            politeness_mistakes=politeness_mistakes,
        )

    async def __evaluate_dialog(self, args):
        messages, metric = args
        results = (await self._post(text=messages, metric=metric))
        return results
