from manage.handler import handle_message
from telegram_bot.bot_base import BaseHandler
from settings import debug_chat

# from sheets_api import append_transaction, get_data_from_current_list
import datetime
import traceback


class ContainTestDataSource:
    # STAY IN DATABASE-LIKE PARADIGM
    _data = {
        "items": [],
    }

    # types:
    # Item = Type('Item', {'key', 'date'})

    @property
    def items(self):
        return self._data["items"]

    def insert_item(self, key, date):
        self.items.append({"key": key, date: datetime.datetime.utcnow()})

    def get_items(self, key):
        result = []
        for i in self.items:
            if i["key"] == key:
                result.append(i)
        return result


class ManageHandler(BaseHandler, ContainTestDataSource):

    # override:

    def _handle_message(self, text):
        # print(self.data)
        # print('text')
        # print(self.chat_id)
        self.handle_key(text)
        # self.send('unknow')

        # self.send('texted: {}'.format(text))
        # self.send('What to do?', keys=[
        #     {'text': 'new event', 'data': 'new'},
        #     {'text': 'nah', 'data': 'nah'}
        # ])

    def _handle_press(self, buttons, button_id):
        # print(buttons[button_id]['text'])

        # self.send('pressed: {}'.format(buttons[button_id]))
        print("buttons[button_id]")
        print(buttons[button_id])
        self.handle_key(buttons[button_id]["callback_data"])

    @property
    def comands(self):
        # TODO states
        comands = [
            "add_follower",
            "add_source",
            "list_followers",
            "list_sources",
            "report",
        ]
        return [dict(text=k, data=k) for k in comands]

    def handle_key(self, text):
        answer = handle_message(self.chat_id, text)

        try:
            if self.chat_id != debug_chat:
                debug_text = "req:\n{}\nresp:\n{}".format(text, answer)
                self.bot.sendMessage(debug_chat, debug_text)
        except Exception as e:
            print("debug")
            print(e)

        if answer:
            self.send(answer)
        # if not text.startswith("/"):
        #     self.append_item(text)
        #     self.send('{} added. Total: {}'.format(
        #         text,
        #         len(self.get_items(key=text)),
        #     ))

        # self.send_main_menu()
