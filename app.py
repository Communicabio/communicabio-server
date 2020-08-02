from typing import Optional, Dict, Any, List
from fastapi import FastAPI, HTTPException, Body
import hmac
import argparse
import logging
import db
import dialogs

app = FastAPI()

parser = argparse.ArgumentParser(description='Process some integers.')
parser.add_argument('tg_token', help='Telegram Bot Token')
parser.add_argument('mongo_url', help='Auth URL to MongoDB')
parser.add_argument('lang', help='Language code', default='en')
args = parser.parse_args()

TOKEN = args.tg_token
database = db.MongoDB(args.mongo_url, args.lang)
dialog_manager = dialogs.Manager(args.lang)

def send_text(chat_id: int, text: str):
    pass

def parse_command(text: str) -> List[str]:
    if text[0] != '/':
        return []
    return list(text.split())

def show_help(**kwargs):
    if args.lang == 'ru':
        return "*полезное сообщение, объясняющее все о боте*"
    else:
        return "*helpful message explaining everything about the bot*"

def end_dialog(user_id: int, name: str, **kwargs) -> List[str]:
    """Ends dialog. Shows feedback."""
    user = database.fetch_user(user_id, name)
    user, dialog = database.finish_dialog(user)
    messages = []
    if args.lang == 'ru':
        text = f'Поздравляю - вы завершили диалог!\n'
               f'Баллы за вежливость {dialog.politeness} (от 0 до 1).\n'
               f'Баллы за позитивность {dialog.positivity} (от 0 до 1)'
        messages.append(text)
    else:
        text = f"Congratulations! You've finished the dialog." \
               f"Politeness score: {dialog.politeness} out of 1." \
               f"Positivity score: {dialog.positivity} out of 1."
        messages.append(text)
    return messages

def new_dialog(user_id: int, name: str, **kwargs) -> str:
    """Starts new dialog if the previous is finished"""
    user = database.fetch_user(user_id, name)
    if user.state != 0:
        if args.lang == 'ru':
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

def process(user_id: int, message: str, name: str) -> Union[str, List[str]]:
    command = parse_command(message)
    if len(command) == 0:
        user = database.fetch_user(user_id)
        if user.state == 0:
            if args.lang == 'ru':
                return "Чтобы начать новый диалог используй /new"
            else:
                return "To start new dialog use /new"
        else:
            user database.add_phrase(database.add_phrase(user, message))
            phrase = dialog_manager.continue(user.dialog)
            database.add_phrase(database.add_phrase(user, phrase))
    else:
        return commands[command[0]](user_id, name)

@app.get("/tg/{token}")
def receive_update(token: str, update: Dict[Any] = Body(..., embed=True)):
    if not hmac.compare_digest(TOKEN, token):
        raise HTTPException(status_code=403, detail="Invalid token")
    if 'message' not in update:
        return {'error': 'Message is missing in the update'}
    chat_id = update['message']['chat']
    if 'text' not in update:
        return {'error': 'Text is missing in the message'}
    text = process(user_id, update['message']['text'])
    if isinstance(text, str):
        send_text(user_id, text)
    else:
        for message in text:
            send_text(user_id, message)
    return {"ok": True}
