# from flask import Flask, request as fl_request
# import telepot
from telegram_bot.manage_bot import ManageHandler

import urllib3
import traceback

# from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton
import json

import time
import pickle
import os

from telegram_bot.services import get_bot


# proxy_url = "http://proxy.server:{}".format(PORT)
# telepot.api._pools = {
#     'default': urllib3.ProxyManager(proxy_url=proxy_url, num_pools=3, maxsize=10, retries=False, timeout=30),
# }
# telepot.api._onetime_pool_spec = (urllib3.ProxyManager, dict(proxy_url=proxy_url, num_pools=1, maxsize=1, retries=False, timeout=30))


bot = get_bot()


def handle(msg):
    handler = ManageHandler(msg, bot)
    handler.handle()


def run():

    if os.path.exists("state.pickle"):
        with open("state.pickle", "rb") as state_pickle:
            state = pickle.load(state_pickle)
            print("load:", state)
    else:
        state = dict(last_id=0)
    print("serving...")
    while 1:

        try:

            response = bot.getUpdates()
            for r in response:
                if state["last_id"] >= r["update_id"]:
                    continue

                handler = ManageHandler(r, bot)
                handler.handle()

                state["last_id"] = r["update_id"]
                with open("state.pickle", "wb") as state_pickle:
                    print("dump:", state)
                    pickle.dump(state, state_pickle)

        except KeyboardInterrupt:
            print("CLOSE")
            exit()
        except Exception as e:
            print(e, traceback.format_exc())
            print('try again...')
            time.sleep(10)
            
        time.sleep(3)


if __name__ == "__main__":
    run()
