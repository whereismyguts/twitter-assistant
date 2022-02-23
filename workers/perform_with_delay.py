import sys,os
sys.path
sys.path.append(os.getcwd())

from custom_settings import get_custom_settings
from twitter_api.api import TwitterApi
from database.mongo import db, get_random
from settings import debug_chat
from telegram_bot.services import send_to_all_managers
import argparse
import time
import random
import datetime
import traceback

def perform_action(order):
    try:
        if order['action'] == 'like':
            r = TwitterApi.set_like(order["user"], order["post"]["id"])
            return r.get("data", {}).get("liked")
        elif order['action'] == 'rt':
            r = TwitterApi.retweet(order["user"], order["post"]["id"])
            return r.get("data", {}).get("retweeted") 
    except Exception as e:
        r = {'errors': str(e)}
    if 'errors' in r:
        db.orders.update_one(
            {'_id': order['_id']},
            {'$set': {'status': 'error', 'error': r['errors']}}
        )

# CRON: */1 * * * *
if __name__ == "__main__":
    
    parser = argparse.ArgumentParser()
    parser.add_argument("-a", "--action")
    args = parser.parse_args()
    ACTION_TYPE = args.action
    if ACTION_TYPE not in ['rt', 'like']:
        raise Exception('bad action!')
    
    if os.path.isfile(ACTION_TYPE + '.lock'):
        # print(ACTION_TYPE, 'is locked! cant')
        sys.exit()
        
    with open(ACTION_TYPE+'.lock', 'w') as f:
        
            f.write(str(datetime.datetime.utcnow()))
            print(ACTION_TYPE, 'locked')
            
            
    try:
        stored_settings = get_custom_settings() 
        print(stored_settings)
        
        # orders = get_random(
        #     db.orders,
        #     filter={
        #         "status": "new",
        #         "action": ACTION_TYPE,
        #     },
        # )
        orders = db.orders.find({
            "status": "new",
            "action": ACTION_TYPE,
        }).sort("_id").limit(1)
        # NOTE:
        # Default orders count is 1 (recomended, because this command is executed in crontab once in a minute). 
        # Random delay before every action:
        for order in orders:
            delay = random.randint(
                stored_settings['DELAY_MINUTES_MIN'],
                stored_settings['DELAY_MINUTES_MAX'], 
            )
            print(delay, 'minutes sleep...')
            time.sleep(delay*60 + random.randint(0,10))
            print(delay, 'sleep is over.')
            
            if perform_action(order):
                db.orders.update_one(
                    dict(_id=order["_id"]),
                    {"$set": dict(
                        status="done",
                        time=datetime.datetime.utcnow(),
                    )},
                )
                msg = "{} is DONE after {}min delay.\nfollower: @{}\npost: {}\ncontent: '{}'".format(
                    order["action"],
                    delay,
                    order["user"]["username"],
                    "https://twitter.com/{}/status/{}".format(
                        order["post"].get("author_id", 'none'),
                        order["post"]["id"],
                    ),
                    order["post"]["text"],
                )
                send_to_all_managers(msg)
                
        
    except Exception as e:
        print(e, traceback.format_exc())
    
    
    os.remove(ACTION_TYPE+'.lock')
    print(ACTION_TYPE, 'unlocked')
            
