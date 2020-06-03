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

        metrics = await self.metric_client.evaluate(user.last_dialog)

        if user.state == db.UserState.DIALOG:
            user.add_score(metrics)
            await self.db.finish_dialog(user)

        return aioweb.json_response({"metrics": metrics.as_dict()})

    @util.route("GET", "/user")
    async def user(self, request):
        params = request.url.query
        user = await self.db.user(token=params["token"])

        return aioweb.json_response({"user": {
            "name": user.name,
            "id": str(user.id),
            "state": user.state.value,
            "last_dialog": user.last_dialog,
            "rating": user.avg_score,
            "place": await self.db.user_place(user),
        }})

    @util.route("GET", "/rating")
    async def users_by_rating(self, request):
        start, end = (int(request.url.query[key]) for key in ("n", "m"))
        leaderboard = await self.db.leaderboard(start, end)
        return aioweb.json_response({"rating": [
            user.as_public_dict()
            for user in leaderboard
        ]})

    @util.route("POST", "/rollback")
    async def rollback(self, request):
        params = await request.json()
        user = await self.db.user(token=params["token"])

        if len(user.last_dialog) > 1:
            del user.last_dialog[-2:]
            await self.db.update_dialog(user)

        return aioweb.json_response({})
