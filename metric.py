import asyncio
import contextlib

import nltk
import pymorphy2

from util import ApiClient

nltk.download("punkt")
MORPH = pymorphy2.MorphAnalyzer()


class MetricSet:
    def __init__(self, coherence, positivity, politeness):
        self.coherence = coherence
        self.positivity = positivity
        self.politeness = politeness

    def as_dict(self):
        return {
            "coherence": self.coherence,
            "positivity": self.positivity,
            "politeness": self.politeness,
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
        messages = [
            message for i, message in enumerate(messages)
            if i % 2 == 1
        ]

        points = await asyncio.gather(*map(self.__evaluate_message, messages))
        positivity_points = []
        toxicity_points = []

        for positivity, toxicity in points:
            positivity_points.append(positivity)
            toxicity_points.append(toxicity)

        return MetricSet(
            1,
            self.__positivity(positivity_points),
            self.__politeness(messages, toxicity_points),
        )

    def __positivity(self, points):
        if len(points) == 0:
            return 0

        penalty = 0

        for point in points:
            neutral, negative, positive = point

            if negative >= 0.5:
                penalty += 0.1
            elif positive >= 0.5:
                penalty -= 1

        return min(1.0, max(0.5 - penalty, 0))

    def __politeness(self, messages, toxicity_points):
        if len(toxicity_points) == 0:
            return 0

        penalty = 0

        for message, toxicity_point in zip(messages, toxicity_points):
            if toxicity_point <= .1:
                penalty += .1

            words = nltk.word_tokenize(message)

            for word in words:
                infinitive = MORPH.parse(word)[:3]

                for el in infinitive:
                    if el.normal_form in self.obscene_words:
                        penalty += .3
                    elif el.normal_form in self.polite_words:
                        penalty -= .05

        return min(1.0, max(0.75 - penalty, 0))

    async def __evaluate_message(self, message):
        vec = (await self._post(text=message))["vector"]

        return await asyncio.gather(*(
            self.__offload(worker_run, model, vec)
            for model in ("positivity", "toxicity")
        ))

    async def __offload(self, func, *args):
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(self.pool, func, *args)


def make_worker_initializer(model_paths):
    def init():
        global torch
        global worker_models

        import torch

        worker_models = {
            key: torch.load(path, map_location=torch.device("cpu"))
            for key, path in model_paths.items()
        }

    return init


def worker_run(model, data):
    tensor = torch.tensor(data)
    return worker_models[model](tensor.view(1, -1)).squeeze().tolist()
