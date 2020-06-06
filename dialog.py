from util import ApiClient


class MockClient:
    async def reply(self, messages):
        return messages[-1]


class Client(ApiClient):
    mock = MockClient

    async def reply(self, messages, en=False):
        return (await self._post(history=messages, en=en))["text"]
