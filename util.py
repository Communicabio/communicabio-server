import asyncio
import json
import traceback

import aiohttp.web as aioweb


CORS_HEADERS = {
    "Access-Control-Allow-Credentials": "true",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "*",
    "Access-Control-Allow-Headers": "*",
}


class ApiClient:
    def __init__(self, session, api):
        self.session = session
        self.api = api

    @classmethod
    def connect(cls, session, api):
        if api is None:
            return cls.mock()
        else:
            return cls(session, api)

    async def _post(self, path=None, **kwargs):
        if path is None:
            url = self.api
        else:
            url = f"{self.api}/{path}"

        async with self.session.post(url, json=kwargs) as response:
            response.raise_for_status()
            return json.loads(await response.read())


def route(*args, **kwargs):
    def wrapper(func):
        if not hasattr(func, "antispam_routes"):
            func.antispam_routes = []

        func.antispam_routes.append((args, kwargs))

        return func

    return wrapper


def add_routes(add_route, api):
    for func_name in dir(api):
        func = getattr(api, func_name)

        if not hasattr(func, "antispam_routes"):
            continue

        for args, kwargs in func.antispam_routes:
            add_route(func, *args, **kwargs)


def make_route_adder(app):
    def add_route(func, methods, path):
        if not isinstance(methods, (tuple, list)):
            methods = (methods,)

        for method in methods:
            app.add_routes([getattr(aioweb, method.lower())(path, func)])

    return add_route


@aioweb.middleware
async def middleware(request, handler):
    try:
        return await handler(request)
    except asyncio.CancelledError:
        raise
    except Exception as exc:
        traceback.print_exc()
        return aioweb.json_response({"error": repr(exc)})


def is_truthy(s):
    if s is None:
        return False

    return s.lower() in ("y", "yes", "1", "true")
