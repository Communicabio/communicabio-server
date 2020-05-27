import random
import util

import aiohttp.web as aioweb

import db
import util
import vk


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

    @util.route("POST", "/user")
    async def dialog(self, request):
        params = await request.json()
        user = await self.db.user(token=params["token"])

        return aioweb.json_response({"user": {
            "name": user.name,
            "state": user.state,
            "last_dialog": user.last_dialog,
        }})
