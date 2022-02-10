import traceback
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton


class BaseHandler:
    def __init__(self, data, bot):
        self.bot = bot
        self.data = data

    @property
    def event(self):
        if "message" in self.data:
            return "message"
        if "callback_query" in self.data:
            return "press"
        if "channel_post" in self.data:
            return "channel_post"
        raise Exception("unknown event")

    def handle_post(self):
        post = self.data["channel_post"]
        self._handle_message(post.get("text", post.get("caption", "")))

    def handle_message(self):
        msg = self.data["message"]
        self._handle_message(msg.get("text", msg.get("caption", "")))

    def handle_press(self):
        buttons = []
        button_id = None
        for b_row in self.data["callback_query"]["message"]["reply_markup"][
            "inline_keyboard"
        ]:
            buttons += b_row

        for i, b in enumerate(buttons):
            if b["callback_data"] == self.data["callback_query"]["data"]:
                button_id = i
                break

        self._handle_press(buttons, button_id)

    @property
    def chat_title(self):
        if "message" in self.data:
            if "title" not in self.data["message"]["chat"]:
                return "you"
            return "chat ({})".format(self.data["message"]["chat"]["title"])
        if "channel_post" in self.data:
            return "channel ({})".format(self.data["channel_post"]["chat"]["title"])

    def handle(self):
        try:
            if self.event == "message":
                self.handle_message()

            if self.event == "press":
                self.handle_press()
            if self.event == "channel_post":
                self.handle_post()
        except Exception as e:
            print("HANDLE ERROR")
            print(e, traceback.format_exc())
            print("DATA")
            print(self.data)
        return "OK"

    def send(self, text, keys=None):  # keys=[{'text': '', 'data': ''}]
        keyboard = None
        if keys:
            rows = self.lines(len(keys))
            keyboard = []
            i = 0
            print("KEYBOARD")
            for row in rows:
                line = []
                for c in range(row):
                    line.append(
                        InlineKeyboardButton(
                            text=keys[i]["text"],
                            callback_data=keys[i]["data"],
                        )
                    )
                    print(keys[i])
                    i += 1
                keyboard.append(line)

            keyboard = InlineKeyboardMarkup(
                inline_keyboard=keyboard,
            )
        # keyboard = InlineKeyboardMarkup(
        #     inline_keyboard=[
        #         [InlineKeyboardButton(
        #             text='Press me',
        #             callback_data='press1',
        #         )],
        #         [InlineKeyboardButton(
        #             text='Press me too',
        #             callback_data='press2',
        #         )],
        #     ]
        # )
        # print(keyboard)
        self.bot.sendMessage(self.chat_id, text, reply_markup=keyboard)

    def lines(self, n):

        scheme = [
            [],
            [1],
            [2],
            [3],
            [4],
            [3, 2],
            [3, 3],
            [4, 3],
            [4, 4],
            [3, 3, 3],
            [4, 3, 3],
            [4, 4, 3],
            [4, 4, 4],
        ]

        if n < len(scheme):
            return scheme[n]

        return [3, 3, 3]

    @property
    def chat_id(self):
        if "message" in self.data:
            return self.data["message"]["chat"]["id"]
        if "channel_post" in self.data:
            return self.data["channel_post"]["chat"]["id"]
        return self.data["callback_query"]["message"]["chat"]["id"]
