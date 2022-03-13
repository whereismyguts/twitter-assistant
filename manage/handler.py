from time import perf_counter
import traceback, json
from custom_settings import set_custom_settings
from twitter_api.api import TwitterApi
from bson.json_util import dumps
from manage.manage_handlers import (
    set_authorize_state,
    handle_add_source,
    handle_enter_pin,
)
import datetime
import re
from manage.hashtag_handlers import create_hastag_orders
from manage.info_handlers import get_stats

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

from database.mongo import get_database
from settings import MANAGER_TOKEN

# MANAGER_TOKEN = os.environ('MANAGER_TOKEN')


def get_auth(chat_id, token, db):
    # print("get_auth", chat_id, token)
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


def handle_message(chat_id, message, alias):
    # TODO auth
    db = get_database(alias)
    
    manager = db.managers.find_one({"chat_id": chat_id})
    if not manager:
        manager = get_auth(chat_id, message, db)
        if not manager:
            return "You need to authentificate, please provide MANAGER_TOKEN"
        return "Welcome, test_manager! Now you can send me these commands:\n{}".format(COMMANDS_HELP)

    if manager["state"] == "main":
        if message == 'help':
            return '-- Commands --\n{}'.format(COMMANDS_HELP)

        if message == "add_follower":
            return set_authorize_state(
                db, manager, chat_id, 'enter_pin', 
                "Follow the link, authorize your Twitter account and send me a PIN:\n",
            )

        if start_with(message, "new_hashtag_task"):
            tags = message.split(' ')[1:]
            tags = [t.strip() for t in tags]
            print(tags)
            try:
                for t in tags:
                    assert t[0] == '#' and len(t)>1
            except Exception as e:
                print(e, traceback.format_exc())
                return '\n'.join([
                    'Bad hastag format!',
                    'example:',
                    '"new_hashtag_task #tag1 #tag2"',
                ])
            return set_authorize_state(
                db, manager, chat_id, 'enter_pin_hastag_task',
                "Follow the link, authorize your Twitter account for new hashtag task and send me a PIN:\n",
                extra_data={'tags': tags}
            )
        
        if start_with(message, "add_source"):
            message = message.replace("@", "")
            username = message.split(" ")[1]
            return handle_add_source(db, username)

        # if start_with(message, "like"):
        #     post_id = message.split(" ")[1]
        #     return set_like(db, post_id)
        
        if start_with(message, "#"):
            return create_hastag_orders(db, message, alias, chat_id)
            
        if start_with(message, "set_percent"):
            try:
                _, action, percent = message.split(' ')
                action = action.upper()
                if action not in ['RT', 'LIKE']:
                    return 'The ACTION value must be one of ["like", "rt"]'
                percent = float(percent)
                if percent > 1 or percent < 0:
                    return 'The PERCENT value must be between 0 and 1'
            except Exception as e:
                print("PERCENT parse error:")
                print(e, traceback.format_exc())
                return "Can't parse the set_percent command!"
            
            key = action + '_USER_PERCENT'
            set_custom_settings(db, {key: percent})
            return '{} percent changed to {}'.format(action, percent)
        
        if start_with(message, "del_follower"):
            username = message.split(" ")[1].lower()
            user = db.users.find_one({'username': re.compile(username, re.IGNORECASE)})
            if not user or user['deleted']:
                return 'There no follower: {}'.format(username)
            
            r = db.orders.delete_many({
                "user.username": username, 
                'status': 'new',
            })
            removed = r and r.raw_result["n"] or 0
            db.users.update_one(
                {'username': username}, 
                {'$set': {
                    'deleted': True,
                }})
            result =  'Follower {} now is removed'.format(username)
            if removed:
                result += '\n{} pending actions in cancelled'.format(removed)
            return result
        
        if start_with(message, "del_source"):
            username = message.split(" ")[1].lower()
            user = db.sources.find_one({'username': re.compile(username, re.IGNORECASE)})
            if not user or user['deleted']:
                return 'There no source: {}'.format(username)
            
            r = db.orders.delete_many({
                "post.author_id": user['id'], 
                'status': 'new',
            })
            removed = r and r.raw_result["n"] or 0
            db.sources.update_one({'username': username}, {'$set': {'deleted': True}})
            
            result = 'Source {} now is removed.'.format(username) 
            if removed:
                result += '\n{} pending actions in cancelled'.format(removed)
            return result
        
        if message == 'stats':
            return get_stats(db)
        
        if start_with(message, "set_delay"):
            try:
                start = int(message.split(" ")[1])
                end = int(message.split(" ")[2])
            except Exception as e:
                print(e, traceback.format_exc())
                return "Can't recognize format 'set_delay A B'"
            if end < 0 or start < 0:
                return "A and B must be greater than 0"
            if end <= start: 
                return '"A" must be greater than "B"'
            set_custom_settings(db, {
                'DELAY_MINUTES_MAX': end,
                'DELAY_MINUTES_MIN': start,
            })
            return 'Delay is set to {}-{} minutes'.format(start, end)
        
    if manager["state"] == "enter_pin":
        user_data = handle_enter_pin(db, manager, message, chat_id)
        if not isinstance(user_data, dict):
            return user_data
        
        user = db.users.find_one(dict(id=user_data["id"])) # ignore deleted
        if not user: # error?
            user = db.users.insert_one({"id": user_data["id"]})
        user = db.users.update_one(
            {"id": user_data["id"]},
            {"$set": user_data},
            upsert=False,
        )
        return 'New follower "{}" authorized 👌'.format(user_data["username"])
    
    if manager['state'] == 'enter_pin_hastag_task':
        user_data = handle_enter_pin(db, manager, message, chat_id)
        print(manager)
        if not isinstance(user_data, dict): # error?
            return user_data
        db.hashtag_tasks.insert_one({
            'status': 'active',
            'created': datetime.datetime.utcnow(),
            'last_update': datetime.datetime.utcnow(),
            'tags': manager['tags'],
            'user': user_data,
        })

        return 'New hashtag task created!'
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
