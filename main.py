# from flask import Flask, request as fl_request
# import telepot
from telegram_bot.manage_bot import ManageHandler

# import urllib3
import traceback

# from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton
import argparse
import time
import pickle
import os

from telegram_bot.services import get_bot


# proxy_url = "http://proxy.server:{}".format(PORT)
# telepot.api._pools = {
#     'default': urllib3.ProxyManager(proxy_url=proxy_url, num_pools=3, maxsize=10, retries=False, timeout=30),
# }
# telepot.api._onetime_pool_spec = (urllib3.ProxyManager, dict(proxy_url=proxy_url, num_pools=1, maxsize=1, retries=False, timeout=30))





# def handle(msg):
#     handler = ManageHandler(msg, bot)
#     handler.handle()

# state_file = 'state_test.pickle'
from settings import BOTS_POOL

def run_bot(bot_alias):
    if bot_alias not in BOTS_POOL:
        raise ValueError(bot_alias, 'not in the bots pool!')
    bot_data = BOTS_POOL[bot_alias]
    bot = get_bot(bot_data['bot_key'])
    state_file = bot_data['state_file']
    
    if os.path.exists(state_file):
        with open(state_file, "rb") as state_pickle:
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

                handler = ManageHandler(r, bot, bot_alias)
                handler.handle()

                state["last_id"] = r["update_id"]
                with open(state_file, "wb") as state_pickle:
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
    parser = argparse.ArgumentParser()
    parser.add_argument("-n", "--name")
    args = parser.parse_args()
    run_bot(args.name)
