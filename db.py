import enum
import secrets

from motor import MotorClient


TOKEN_LENGTH = 32


@enum.unique
class UserState(enum.Enum):
    MAIN_MENU = 1
    DIALOG = 2


class User:
    def __init__(self, row):
        self.name = row["name"]
        self.id = row["_id"]
        self.telegram_id = row.get("telegram_id")
        self.vk_id = row.get("vk_id")
        self.token = row["token"]
        self.state = UserState(row["state"])
        self.last_dialog = row["last_dialog"]


class Db:
    def __init__(self, url):
        self.__client = MotorClient(url)
        self.__db = self.__client["communicabio"]
        self.__users = self.__db["users"]
        self.__dialogs = self.__db["dialogs"]

    async def user(self, name=None, telegram_id=None, vk_id=None, token=None):
        if telegram_id is not None:
            id_key = "telegram_id"
            id_value = telegram_id
        elif vk_id is not None:
            id_key = "vk_id"
            id_value = vk_id
        elif token is not None:
            id_key = "token"
            id_value = token
        else:
            raise Exception(
                "either telegram_id, vk_id or token must be not None"
            )

        user = await self.__users.find_one({id_key: id_value})

        if user is None:
            if id_key == "token":
                return None

            user = {
                "name": name,
                id_key: id_value,
                "token": secrets.token_hex(TOKEN_LENGTH),
                "state": UserState.MAIN_MENU.value,
                "last_dialog": None,
            }

            await self.__users.insert_one(user)

        return User(user)

    async def new_dialog(self, user, initial_message):
        if user.state == UserState.DIALOG:
            await self.__dialogs.insert_one({
                "uid": user.id,
                "messages": user.last_dialog,
            })

        await self.__users.update_one(
            {"_id": user.id},
            {"$set": {
                "state": UserState.DIALOG.value,
                "last_dialog": [initial_message],
            }},
        )

    async def finish_dialog(self, user):
        await self.__users.update_one(
            {"_id": user.id},
            {"$set": {
                "state": UserState.MAIN_MENU.value,
            }},
        )

    async def update_dialog(self, user):
        await self.__users.update_one(
            {"_id": user.id},
            {"$set": {"last_dialog": user.last_dialog}},
        )
