import traceback, json
from bson.json_util import dumps
from manage.manage_handlers import (
    handle_add_follower,
    handle_add_source,
    handle_enter_pin,
)
import re

COMMANDS_HELP = """
help
This will show the various commands that can be used with this bot. 

add_follower
This will add a new Twitter account to the “pool” of accounts that will like and retweet tweets from main accounts. 

add_source HANDLE
This will add another main Twitter account. The “pool” Twitter accounts will like and retweet tweets from these main accounts. Example: “add_source jack” will like and retweet the 10 last tweets and every new tweet for the @jack Twitter account. 

del_source HANDLE
This will delete the source and stop listening all new post from it

del_follower HANDLE
This will delete the twitter acount frim the "pool" and account will do not liking and retweeting anymore

stats
This will show the list of Twitter accounts in the “pool” and all the main Twitter accounts connected to the bot. 

set_delay A B
This will establish the timeframe in which main account tweets will be liked/retweeted. Example: “set_delay 2 15” will spread out the likes and retweets between 2 minutes to 15 minutes. 

set_percent ACTION PERCENT
This will set the percentage of “pool” accounts that will like/retweet tweets from the main accounts. Example: “set_percent like 50” will have 50% of the “pool” accounts like all tweets from the main accounts. 

#tag ACTION COUNT
This will like/retweet random tweets that include a specific hashtag. Example: “#BSC like 15” will have the main accounts randomly like 15 tweets that use the #BSC hashtag.
"""

# Logger settings - CloudWatch
# logger = logging.getLogger()
# logger.setLevel(logging.INFO)

# Set client
# DB_HOST = os.environ["DB_HOST"]

from database.mongo import db

from settings import MANAGER_TOKEN

# MANAGER_TOKEN = os.environ('MANAGER_TOKEN')


def get_auth(chat_id, token):
    print("get_auth", chat_id, token)
    if token == MANAGER_TOKEN:
        manager = db.managers.insert_one(
            dict(
                chat_id=chat_id,
                state="main",
            )
        )
        return manager


def start_with(value, text):
    return value[: len(text)] == text


def handle_message(chat_id, message):
    # TODO auth

    manager = db.managers.find_one({"chat_id": chat_id})
    if not manager:
        manager = get_auth(chat_id, message)
        if not manager:
            return "You need to authentificate, please provide MANAGER_TOKEN"
        return "Welcome, test_manager! Now you can send me these commands:\n{}".format(COMMANDS_HELP)

    if manager["state"] == "main":
        if message == 'help':
            return '-- Commands --\n{}'.format(COMMANDS_HELP)
        if message == "add_follower":
            return handle_add_follower(db, manager, chat_id)

        if start_with(message, "add_source"):
            message = message.replace("@", "")
            username = message.split(" ")[1]
            return handle_add_source(db, username)

        # if start_with(message, "like"):
        #     post_id = message.split(" ")[1]
        #     return set_like(db, post_id)
        
        if start_with(message, "del_follower"):
            username = message.split(" ")[1].lower()
            user = db.users.find_one({'username': re.compile(username, re.IGNORECASE)})
            if not user or user['deleted']:
                return 'There no source: {}'.format(username)
            db.users.update_one({'username': username}, {'deleted': True})
            return 'Source {} now is removed'.format(username)
        
        if start_with(message, "del_source"):
            username = message.split(" ")[1].lower()
            user = db.sources.find_one({'username': re.compile(username, re.IGNORECASE)})
            if not user or user['deleted']:
                return 'There no source: {}'.format(username)
            db.sources.update_one({'username': username}, {'deleted': True})
            return 'Source {} now is removed'.format(username)
        
        if message == 'stats':
            users=[u['username'] for u in db.users.find(dict(deleted=False))]
            sources=[u['username'] for u in db.sources.find(dict(deleted=False))]
            rt_orders=db.orders.find(dict(status='new', action='rt'))
            like_orders=db.orders.find(dict(status='new', action='rt'))
            text = 'Users pool({}):\n{}\n\nSources({}):\n{}\n\nOrders in queue:\nLike: {}\nRetweet: {}'.format(
                len(users), '\n'.join(users),
                len(sources), '\n'.join(sources),
                like_orders and len(list(like_orders)) or 0, 
                rt_orders and len(list(rt_orders)) or 0, 
            )
            return text
        
    if manager["state"] == "enter_pin":
        return handle_enter_pin(db, manager, message, chat_id)
    return ""


if __name__ == "__main__":
    print(1488937141400969217)
    while 1:
        try:
            print("BOT:" + handle_message("2", input("ME:")))
        except Exception as e:
            print(e, traceback.format_exc())
            print(e)
            break
