#!/usr/bin/env python3

import argparse
import asyncio
import concurrent.futures
import contextlib
import json
import os
from pathlib import Path

import aiohttp
import aiohttp.web as aioweb

import api
import db
import dialog
import metric
import tgbot
import util


async def main():
    args = parse_args()
    assets = Path(args.assets)

    with open(assets / "start_phrases.json") as phrase_file:
        phrases = json.load(phrase_file)["data"]

    with open(assets / "obscene_words.json") as obscene_word_file:
        obscene_words = json.load(obscene_word_file)

    with open(assets / "polite_words.json") as polite_word_file:
        polite_words = json.load(polite_word_file)

    database = db.Db(args.mongodb)

    async with contextlib.AsyncExitStack() as stack:
        http_session = await stack.enter_async_context(aiohttp.ClientSession())

        pool = stack.enter_context(concurrent.futures.ProcessPoolExecutor(
            max_workers=args.num_workers,
            initializer=metric.make_worker_initializer({
                model: assets / f"{model}.bin"
                for model in ("positivity", "toxicity")
            }),
        ))

        dialog_client = dialog.Client.connect(http_session, args.dialog_api)

        metric_client = metric.Client.connect(
            pool,
            http_session,
            args.metric_api,
            obscene_words,
            polite_words,
        )

        telegram_bot = tgbot.Bot(
            database,
            dialog_client,
            metric_client,
            args.telegram_token,
            phrases,
        )

        http_api = api.Api(
            database,
            dialog_client,
            metric_client,
            args.vk_secret,
            phrases,
        )

        web_app = aioweb.Application(middlewares=[util.cors])
        http_api.setup_app(web_app)

        await asyncio.gather(
            telegram_bot.run(),
            aioweb._run_app(web_app, host=args.host, port=args.port),
        )


def parse_args():
    parser = argparse.ArgumentParser(
        description="Communicabio Telegram bot server",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "--assets",
        default="./assets",
        help="path to assets",
    )

    parser.add_argument(
        "--telegram-token",
        default=getenv("TELEGRAM_TOKEN"),
        help="Telegram bot token",
    )

    parser.add_argument(
        "--vk-secret",
        default=getenv("VK_SECRET"),
        help="VKontakte secret",
    )

    parser.add_argument(
        "--mongodb",
        default=getenv("MONGODB", "mongodb://localhost:27017"),
        help="MongoDB URL",
    )

    parser.add_argument(
        "--dialog-api",
        default=getenv("DIALOG_API"),
        help="dialog API address",
    )

    parser.add_argument(
        "--metric-api",
        default=getenv("METRIC_API"),
        help="metric API address",
    )

    parser.add_argument(
        "--num-workers",
        default=getenv("NUM_WORKERS"),
        help="number of metric workers",
    )

    parser.add_argument(
        "--host",
        default=getenv("HOST"),
        help="HTTP API host",
    )

    parser.add_argument(
        "--port",
        default=getenv("PORT"),
        help="HTTP API port",
    )

    return parser.parse_args()


def getenv(key, default=None):
    return os.getenv("COMMUNICABIO_" + key, default)


if __name__ == "__main__":
    asyncio.run(main())
