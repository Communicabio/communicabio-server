import asyncio
import random
import re

import aiogram

import db


COMMANDS = {
    "start",
    "help",
    "new",
    "finish",
}

HELP_TEXT = (
    "Список доступных команд:\n"
    " – /help – показать список команд\n"
    " – /new – начать новый диалог\n"
    " – /finish – закончить диалог\n"
)


class Bot:
    def __init__(self, db, dialog_client, metric_client, token, phrases):
        self.db = db
        self.dialog_client = dialog_client
        self.metric_client = metric_client
        self.token = token
        self.phrases = phrases

        self.__bot = aiogram.Bot(token=token)
        self.__dispatcher = aiogram.Dispatcher(self.__bot)
        self.__dispatchable_handle_message = \
            self.__dispatcher.message_handler()(self.__handle_message)

    def setup_app(self, app):
        app["BOT_DISPATCHER"] = self.__dispatcher

        app.router.add_route(
            "*", f"/webhooks/telegram/{self.token}",
            aiogram.dispatcher.webhook.WebhookRequestHandler,
            name="telegram_webhook_handler",
        )

    async def poll(self):
        await self.__dispatcher.start_polling()

    async def __handle_message(self, message):
        user = await self.db.user(
            name=message.from_user.username,
            telegram_id=message.from_user.id,
        )

        if message.is_command():
            cmd, args = message.get_full_command()
            cmd = cmd[1:]

            if cmd in COMMANDS:
                await getattr(self, "_" + cmd)(user, message)
            else:
                await self.__unknown_command(message)
        else:
            if user.state == db.UserState.MAIN_MENU:
                await self.__unknown_command(message)
            else:
                await self.__handle_reply(user, message)

    async def _start(self, user, message):
        await message.answer("Добро пожаловать в Communicabio!\n\n" + HELP_TEXT)

    async def __unknown_command(self, message):
        await message.answer("Неизвестная команда!\n\n" + HELP_TEXT)

    async def _help(self, user, message):
        await message.answer(HELP_TEXT)

    async def _new(self, user, message):
        if user.state != db.UserState.MAIN_MENU:
            await self.__print_report(user, message)

        initial_message = random.choice(self.phrases)

        await self.db.new_dialog(user, initial_message)

        await message.answer(initial_message)

    async def _finish(self, user, message):
        if user.state != db.UserState.DIALOG:
            await message.answer(
                "Нет текущего диалога, нажмите /new, чтобы начать новый.\n",
            )

            return

        await self.db.finish_dialog(user)

        await self.__print_report(user, message)

    async def __print_report(self, user, message):
        metrics = await self.metric_client.evaluate(user.last_dialog)

        await message.answer((
            f"Ваш результат:\n"
            # f" – связность: {metrics.coherence}\n"
            f" – позитивность: {metrics.positivity}\n"
            f" – вежливость: {metrics.politeness}\n"
        ))

    async def __handle_reply(self, user, message):
        if message.text is None:
            return

        user.last_dialog.append(message.text)

        our_reply = await self.dialog_client.reply(user.last_dialog)
        user.last_dialog.append(our_reply)

        await self.db.update_dialog(user)

        await message.answer(our_reply)
