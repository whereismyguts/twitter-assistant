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
from custom_settings import emojis
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
        }).sort("_id")
        
        orders = list(orders)
        print('orders: ', len(orders))
        if len(orders) == 0:
          raise Exception("No orders found!")  
        
        for order in orders:
            user = db.users.find_one({'id': order['user']['id']})
            
            if user['status'] != 'ok':
                print(user['username'], 'user is', user['status'])
                continue    
            
            if 'last_request' in user:
                lr = user['last_request']
                time_from_lr = datetime.datetime.utcnow() - lr
                if time_from_lr.total_seconds() < 5*60:
                    print('{} was used recently ({}), need to wait for {} sec'.format(
                        user['username'], lr, 5*60 - time_from_lr.total_seconds()
                    ))
                    continue
            print('got a suitable order:\n', order)    
            break
        else:
            raise Exception("Can't find suitable users now.")
        # 'user.status': { '$ne': 'ok' } 
        
        
        delay = random.randint(
            stored_settings['DELAY_MINUTES_MIN'],
            stored_settings['DELAY_MINUTES_MAX'], 
        )
        print(delay, 'minutes sleep...')
        time.sleep(delay*60 + random.randint(0,10))
        print(delay, 'sleep is over.')
        
        if perform_action(order):
            db.users.update_one(
                {'id': order['user']['id']},
                {'$set': {'last_request': datetime.datetime.utcnow()}},
            )
            db.orders.update_one(
                dict(_id=order["_id"]),
                {"$set": dict(
                    status="done",
                    time=datetime.datetime.utcnow(),
                )},
            )
            msg = "{}{} is DONE after {}min delay.\nfollower: @{}\npost: {}".format(
                emojis.get((order["action"], 'DONE'), ''),
                order["action"],
                delay,
                order["user"]["username"],
                "https://twitter.com/{}/status/{}".format(
                    order["post"].get("author_id", 'none'),
                    order["post"]["id"],
                ),
            )
            send_to_all_managers(msg)
                
        
    except Exception as e:
        print(e, traceback.format_exc())
    
    
    os.remove(ACTION_TYPE+'.lock')
    print(ACTION_TYPE, 'unlocked')
            
