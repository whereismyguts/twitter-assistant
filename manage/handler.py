import traceback, json
from bson.json_util import dumps
from manage.actions import set_like
from manage.manage_handlers import (
    handle_add_follower,
    handle_add_source,
    handle_enter_pin,
)

COMMANDS_HELP = """
help\n- Show this text.

add_follower\n- Authorize your Twitter account by link and PIN, to use them for interact with sources.

add_source USERNAME\n- Add Twitter account and periodically scan it for new tweets to like/rt them. Example "add_source jack" - search and retweet/like 10 last and every new original tweets of @jack twitter account.

stats\n- Show list of all followers and sources.

set_delay A B (*In progress*)\n- Set time random limits (in minutes) between background actions (like or rt). Example: "set_delay 2 15" will make every type of action executing with delay from 2 to 15 minutes each.

set_percent ACTION PERCENT (*In progress*)\n- Set how many percents (1-100) of your authorized users will be engaged in one action (like and rt). Using if there is more than 5 users authorized. Example: "set_precent like 50".

#TAG ACTION COUNT (*In progress*)\n- Find and add to queue like (or rt) some amount of posts with hashtag. Example: "#python rt 10", "#news like 5".
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
            return handle_add_source(db, message.split(" ")[1])

        if start_with(message, "like"):
            post_id = message.split(" ")[1]
            return set_like(db, post_id)
        if message == 'stats':
            data = dict(
                users=['https://twitter.com/{}'.format(u['username']) for u in db.users.find()],
                # managers=safe_dumps(db.managers.find()),
                sources=['https://twitter.com/{}'.format(u['username']) for u in db.sources.find()]
            )
            return json.dumps(data, indent=4, ensure_ascii=False)
        
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
