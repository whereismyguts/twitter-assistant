import sys,os
sys.path
sys.path.append(os.getcwd())

import random

from database.mongo import get_database
from twitter_api.api import TwitterApi
from settings import debug_chat
from telegram_bot.services import send_to_all_managers
from custom_settings import get_custom_settings, emojis
import datetime
import argparse

# posts = db.posts
# posts = [random.randint(1000, 1000000) for i in range(10)]


def get_sources(db):
    return [s for s in db.sources.find(dict(deleted=False))]
    # return [dict(id=get_id()) for i in range(5)]


def get_users(db):
    return [u for u in db.users.find(dict(deleted=False, status='ok'))]
    # return [dict(id=get_id()) for i in range(10)]


def get_posts_from_source(db, source):
    # posts = [dict(id=get_id(), last_id=get_id()) for i in range(1)]
    last_id=source.get("last_id")
    if last_id:
        params = {'last_id': last_id}
    else:
        params = {'start_dt': source['created'] }

    posts = TwitterApi(db=db).get_tweets_by_id(
        source["id"], 
        **params
    )
    if posts:
        source["last_id"] = max([p["id"] for p in posts])
        db.sources.update_one(
            dict(id=source["id"]),
            {"$set": source},
        )
        return posts
    return []


def get_some_users(db, percent=1):
    users = get_users(db)
    if len(users) < 5:
        return users
    count = int(len(users) * percent)
    random.shuffle(users)
    return users[:count]


def create_order(db, post, user, action):
    db.orders.insert_one(
        dict(
            action=action,
            user=user,
            post=post,
            created=datetime.datetime.utcnow(),
            status="new",
        )
    )

    msg = "{}{} is ENQUEUED.\nfollower: @{}\npost: {}".format(
        emojis.get((action, 'ENQUEUED'), ''),
        action,
        user["username"],
        'https://twitter.com/{}/status/{}'.format(
            post['author_id'],
            post["id"],
        ),
    )
    return msg


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-n", "--name")
    args = parser.parse_args()
    
    db = get_database(args.name)
    custom_settings = get_custom_settings(db)
    sources = get_sources(db)
    for source in sources:
        posts = get_posts_from_source(db, source)
        # print(source)
        text = ''
        for post in posts:
            if post.get('in_reply_to_user_id'): # don't act with replies
                print('skiped:' ,post['id'], post['text'])
                continue
            for user in get_some_users(db, percent=custom_settings['LIKE_USER_PERCENT']):
                text = create_order(db, post, user, "like")
                if text:
                    send_to_all_managers(args.name, text)
            for user in get_some_users(db, percent=custom_settings['RT_USER_PERCENT']):
                text = create_order(db, post, user, "rt")
                if text:
                    send_to_all_managers(args.name, text)

            
