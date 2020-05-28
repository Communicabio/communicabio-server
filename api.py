import random
import util

import aiohttp.web as aioweb

import db
import util
import vk


MOCK_RATING_N = 40

MOCK_RATING = [
    {
        "rating": random.randint(1, 50) * 5,
        "name": f"user-{i + 1}"
    }
    for i in range(MOCK_RATING_N)
]

MOCK_RATING.sort(key=lambda el: -el["rating"])

for i, entry in enumerate(MOCK_RATING):
    entry["place"] = i + 1


class Api:
    def __init__(self, db, dialog_client, metric_client, vk_secret, phrases):
        self.db = db
        self.dialog_client = dialog_client
        self.metric_client = metric_client
        self.vk_secret = vk_secret
        self.phrases = phrases

    def setup_app(self, app):
        util.add_routes(util.make_route_adder(app), self)

    @util.route("POST", "/token")
    async def token(self, request):
        params = await request.json()
        vk_params = vk.extract_data(self.vk_secret, params["data"])

        if vk_params is None:
            return aioweb.json_response({"error": "invalid signature"})

        user = await self.db.user(
            name=params["name"],
            vk_id=vk_params["vk_user_id"],
        )

        return aioweb.json_response({"token": user.token})

    @util.route("POST", "/start_dialog")
    async def start_dialog(self, request):
        params = await request.json()
        user = await self.db.user(token=params["token"])

        initial_message = random.choice(self.phrases)

        await self.db.new_dialog(user, initial_message)

        return aioweb.json_response({"first_message": initial_message})

    @util.route("POST", "/reply")
    async def reply(self, request):
        params = await request.json()
        user = await self.db.user(token=params["token"])

        user.last_dialog.append(params["message"])

        reply_message = await self.dialog_client.reply(user.last_dialog)
        user.last_dialog.append(reply_message)

        await self.db.update_dialog(user)

        return aioweb.json_response({"reply_message": reply_message})

    @util.route("POST", "/finish_dialog")
    async def finish_dialog(self, request):
        params = await request.json()
        user = await self.db.user(token=params["token"])

        await self.db.finish_dialog(user)

        metrics = await self.metric_client.evaluate(user.last_dialog)
        return aioweb.json_response({"metrics": metrics.as_dict()})

    @util.route("GET", "/user")
    async def user(self, request):
        params = request.url.query
        user = await self.db.user(token=params["token"])

        rating_data = MOCK_RATING[MOCK_RATING_N // 2]

        return aioweb.json_response({"user": {
            "name": user.name,
            "state": user.state.value,
            "last_dialog": user.last_dialog,
            "rating": rating_data["rating"],
            "place": rating_data["place"],
        }})

    @util.route("GET", "/rating")
    async def users_by_rating(self, request):
        params = request.url.query
        return aioweb.json_response({
            "rating": MOCK_RATING[int(params["n"]):int(params["m"])],
        })

    @util.route("POST", "/rollback")
    async def rollback(self, request):
        params = await request.json()
        user = await self.db.user(token=params["token"])

        if len(user.last_dialog) > 1:
            del user.last_dialog[-2:]
            await self.db.update_dialog(user)

        return aioweb.json_response({})
