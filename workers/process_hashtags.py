import sys,os
sys.path
sys.path.append(os.getcwd())

from database.mongo import get_database
from settings import BOTS_POOL
import argparse
import datetime
import traceback
from twitter_api.api import TwitterApi
from workers.crawl_new_tweets import create_order
from telegram_bot.services import send_to_all_managers

# CRON: */1 * * * *
if __name__ == "__main__":
    # parser = argparse.ArgumentParser()
    # # parser.add_argument("-a", "--action")
    # parser.add_argument("-n", "--name")
    # args = parser.parse_args()
    # bot_alias = args.name
    bot_alias = 'main'
    
    if bot_alias not in BOTS_POOL:
        raise ValueError(bot_alias, 'not in the bots pool!')
    db = get_database(bot_alias)
    hashtag_tasks = list(db.hashtag_tasks.find({'status': 'active'}))
    
    try:
        for hashtag_task in hashtag_tasks:
            # print(hashtag_task)
            query = ' '.join( hashtag_task['tags'])            
            posts = list(TwitterApi(db=db).get_tweets_by_query(
                query, 
                start_dt=hashtag_task['last_update'],
                user=hashtag_task['user']
            ))
            for post in posts:
              try:
                for action in ['rt', 'like']:
                    text = create_order(db, post, hashtag_task['user'], action.lower())
                    if text:
                        send_to_all_managers(bot_alias, text)
                
              finally:
                db.hashtag_tasks.update_one(
                    {'_id': hashtag_task['_id']},
                    {'$set': {'last_update': datetime.datetime.utcnow()}}
                )
    except Exception as e:
        print("hasgtag task error:")
        print(e, traceback.format_exc())
        
    

# def upd():
#     for hashtag_task in db.hashtag_tasks.find({
#          'status': 'new',
#     })
#     db.hashtag_tasks.update_one(
#                     {'_id': hashtag_task['_id']},
#                     {'$set': {'last_update': datetime.datetime.utcnow()}}
#                 )
    
