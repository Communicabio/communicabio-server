from typing import Optional, Dict, Any, List, Union
from fastapi import FastAPI, HTTPException, Body
import hmac
import logging
import db
import dialogs
import os
import requests

app = FastAPI()

LANGUAGES = {'en'} #, 'ru'}

args = {
    'mongo_url': os.getenv('MONGO_URL'),
}

token2lang = dict()
lang2token = dict()

for lang in LANGUAGES:
    token = os.getenv(f'{lang.upper()}_TELEGRAM_TOKEN')
    args[f'{lang}_telegram_token'] = token
    token2lang[token] = lang
    lang2token[lang] = token

databases = {lang: db.MongoDB(args['mongo_url'], lang) for lang in LANGUAGES}
dialog_managers = {lang: dialogs.Manager(lang) for lang in LANGUAGES}

def send_text(chat_id: int, text: str, lang: str):
    requests.post(f'https://api.telegram.org/bot{lang2token[lang]}/sendMessage',
                    json={'chat_id': chat_id, 'text': text}).raise_for_status()

def parse_command(text: str) -> List[str]:
    if text[0] != '/':
        return []
    return list(text.split())

def show_help(lang: str, **kwargs):
    if lang == 'ru':
        return "*полезное сообщение, объясняющее все о боте*"
    else:
        return "*helpful message explaining everything about the bot*"

def end_dialog(user_id: int, name: str, lang: str, **kwargs) -> List[str]:
    """Ends dialog. Shows feedback."""
    user = database.fetch_user(user_id, name)
    user, dialog = database.finish_dialog(user)
    messages = []
    if lang == 'ru':
        text = f'Поздравляю - вы завершили диалог!\n' \
               f'Баллы за вежливость {dialog.politeness} (от 0 до 1).\n' \
               f'Баллы за позитивность {dialog.positivity} (от 0 до 1)'
        messages.append(text)
    else:
        text = f"Congratulations! You've finished the dialog." \
               f"Politeness score: {dialog.politeness} out of 1." \
               f"Positivity score: {dialog.positivity} out of 1."
        messages.append(text)
    return messages

def new_dialog(user_id: int, name: str, lang: str, **kwargs) -> str:
    """Starts new dialog if the previous is finished"""
    user = database.fetch_user(user_id, name)
    if user.state != 0:
        if lang == 'ru':
            return "Пожалуйста, закончите предыдущий диалог (/end), чтобы начать новый."
        else:
            return "Please, /end the previous dialog to start a new one."
    phrase = dialog_manager.start()
    user = database.add_phrase(user, phrase)
    return phrase

commands = {
    '/start': show_help,
    '/help': show_help,
    '/end': end_dialog,
    '/new': new_dialog,
}

def process(user_id: int, message: str, name: str, lang: str) -> Union[str, List[str]]:
    command = parse_command(message)
    if len(command) == 0:
        user = databases[lang].fetch_user(user_id)
        if user.state == 0:
            if lang == 'ru':
                return "Чтобы начать новый диалог используй /new"
            else:
                return "To start new dialog use /new"
        else:
            user = databases[lang].add_phrase(database.add_phrase(user, message))
            phrase = dialog_managers[lang].reply(user.dialog)
            database.add_phrase(databases[lang].add_phrase(user, phrase))
    else:
        return commands[command[0]](user_id=user_id, name=name, lang=lang)

@app.post("/tg/{token}")
def receive_update(token: str, update: Dict[Any, Any] = Body(...)):
    lang = None
    for TOKEN in token2lang:
        if hmac.compare_digest(TOKEN, token):
            lang = token2lang[TOKEN]
            break
    if lang is None:
        raise HTTPException(status_code=403, detail="Invalid token")
    if 'message' not in update:
        return {'error': 'Message is missing in the update'}
    logging.warning(update)
    chat_id = update['message']['chat']
    if 'text' not in update['message']:
        logging.info('Text is missing in the message')
        return {'error': 'Text is missing in the message'}

    if len(update['message']['from'].get('username', '')) > 0:
        name = update['message']['from']['username']
    else:
        name = update['message']['from']['first_name'] + ' ' + update['message']['from'].get('last_name')

    text = process(chat_id, update['message']['text'], name)
    if isinstance(text, str):
        send_text(chat_id, text)
    else:
        for message in text:
            send_text(chat_id, message)
    return {"ok": True}
