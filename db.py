import enum
import secrets

import motor
import pymongo


TOKEN_LENGTH = 32


@enum.unique
class UserState(enum.Enum):
    MAIN_MENU = 1
    DIALOG = 2

START_PHRASE = "Привет! Я Communicabio. Обычно я буду писать тебе с какой-то просьбой или требованием. Тебе нужно будет договориться со мной, в том числе отказать, если условия не нравятся. Просто пиши мне в чат и мы все обсудим. Если захочешь изменить свою реплику, нажми на “Отмена”. Когда закончишь с диалогом, нажми на “Закончить”. Потребуется некоторое время, чтобы оценить диалог, а затем появится результат. Если я найду какие-то ошибки, то покажу их. Заверши диалог, чтобы закончить обучение."

class User:
    def __init__(self, row):
        self.name = row["name"]
        self.id = row.get("_id")
        self.telegram_id = row.get("telegram_id")
        self.vk_id = row.get("vk_id")
        self.token = row["token"]
        self.state = UserState(row.get("state", UserState.Dialog.value))
        self.last_dialog = row.get("last_dialog", [START_PHRASE])
        self.num_dialogs = row.get("num_dialogs", 0)
        self.sum_score = row.get("sum_score", 0)
        self.avg_score = row.get("avg_score", 0)

    def add_score(self, metrics):
        self.num_dialogs += 1
        self.sum_score += metrics.score
        self.avg_score = self.sum_score / self.num_dialogs

    def as_dict(self):
        return {
            "state": self.state.value,
            **{key: getattr(self, key, None) for key in (
                "name",
                "id",
                "telegram_id",
                "vk_id",
                "token",
                "last_dialog",
                "num_dialogs",
                "sum_score",
                "avg_score",
            )},
        }

    def as_public_dict(self):
        return {
            "id": str(self.id),
            **{key: getattr(self, key, None) for key in (
                "name",
                "num_dialogs",
                "sum_score",
                "avg_score",
            )},
        }


class Db:
    def __init__(self, url):
        self.__client = motor.MotorClient(url)
        self.__db = self.__client["communicabio"]
        self.__users = self.__db["users"]
        self.__dialogs = self.__db["dialogs"]

    async def setup(self):
        await self.__users.create_index([
            ("avg_score", pymongo.DESCENDING),
            ("_id", pymongo.ASCENDING),
        ])

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

            user = User({
                "name": name,
                id_key: id_value,
                "token": secrets.token_hex(TOKEN_LENGTH),
            })

            user.id = (await self.__users.insert_one(user.as_dict())).inserted_id
        else:
            user = User(user)

        return user

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
                "num_dialogs": user.num_dialogs,
                "sum_score": user.sum_score,
                "avg_score": user.avg_score,
            }},
        )

    async def finish_dialog(self, user):
        await self.__users.update_one(
            {"_id": user.id},
            {"$set": {
                "state": UserState.MAIN_MENU.value,
                "num_dialogs": user.num_dialogs,
                "sum_score": user.sum_score,
                "avg_score": user.avg_score,
            }},
        )

    async def update_dialog(self, user):
        await self.__users.update_one(
            {"_id": user.id},
            {"$set": {"last_dialog": user.last_dialog}},
        )

    async def leaderboard(self, start, end):
        return [
            User(user)
            for user in await self.__users.find(
                {}, sort=[
                    ("avg_score", pymongo.DESCENDING),
                    ("_id", pymongo.ASCENDING),
                ],
                skip=start,
                limit=end - start,
            ).to_list(length=None)
        ]

    async def user_place(self, user):
        return await self.__users.count_documents({"$or": [
            {"avg_score": {"$gt": user.avg_score}},
            {
                "avg_score": {"$eq": user.avg_score},
                "_id": {"$lt": user.id},
            },
        ]})
