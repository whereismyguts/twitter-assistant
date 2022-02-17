import sys,os
sys.path
sys.path.append(os.getcwd())

import random

from database.mongo import db
from twitter_api.api import TwitterApi
from settings import debug_chat
from telegram_bot.services import send_to_all_managers


LIKE_USER_PERCENT = 0.8
RT_USER_PERCENT = 0.5


# posts = db.posts
# posts = [random.randint(1000, 1000000) for i in range(10)]


def get_sources():
    return [s for s in db.sources.find(dict(deleted=False))]
    # return [dict(id=get_id()) for i in range(5)]


def get_users():
    return [u for u in db.users.find(dict(deleted=False))]
    # return [dict(id=get_id()) for i in range(10)]


def get_posts_from_source(source):
    # posts = [dict(id=get_id(), last_id=get_id()) for i in range(1)]
    posts = TwitterApi.get_tweets_by_id(source["id"], last_id=source.get("last_id"))
    if posts:
        source["last_id"] = max([p["id"] for p in posts])
        db.sources.update_one(
            dict(id=source["id"]),
            {"$set": source},
        )
        return posts
    return []


def get_some_users(percent=1):
    users = get_users()
    if len(users) < 5:
        return users
    count = int(len(users) * percent)
    random.shuffle(users)
    return users[:count]


def create_order(post, user, action):
    db.orders.insert_one(
        dict(
            action=action,
            user=user,
            post=post,
            status="new",
        )
    )

    msg = "{} is ENQUEUED.\nfollower: @{}\npost: {}\ncontent: '{}'".format(
        action,
        user["username"],
        'https://twitter.com/{}/status/{}'.format(
            post['author_id'],
            post["id"],
        ),
        post["text"],
    )
    return msg


if __name__ == "__main__":
    sources = get_sources()
    for source in sources:
        posts = get_posts_from_source(source)
        # print(source)
        text = ''
        for post in posts:
            for user in get_some_users(percent=LIKE_USER_PERCENT):
                text = create_order(post, user, "like")
                if text:
                    send_to_all_managers(text)
            for user in get_some_users(percent=RT_USER_PERCENT):
                text = create_order(post, user, "rt")
                if text:
                    send_to_all_managers(text)

            
