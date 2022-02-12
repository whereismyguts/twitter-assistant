from twitter_api.api import TwitterApi
from database.mongo import db
from settings import debug_chat
from telegram_bot.services import send_to_all_managers


def get_random(table, count=1, filter=None):
    if not filter:
        filter = {"id": {"$exists": False}}
    return [
        row
        for row in table.aggregate(
            [
                {"$match": filter},
                {"$sample": {"size": count}},
            ]
        )
    ]


import datetime

if __name__ == '__main__':
    orders = get_random(db.orders, filter={"status": "new", "action": "like"})

    for order in orders:
        print(order)
        print(order["_id"])
        r = TwitterApi.set_like(order["user"], order["post"]["id"])
        if r.get("data", {}).get("liked"):
            db.orders.update_one(
                dict(_id=order["_id"]),
                {"$set": dict(status="done")},
            )
            msg = "{} is DONE.\nfollower: @{}\npost: {}\ncontent: '{}'".format(
                order["action"],
                order["user"]["username"],
                'https://twitter.com/{}/status/{}'.format(
                    order["post"]['author_id'],
                    order["post"]["id"],
                ),
                order["post"]["text"],
            )
            send_to_all_managers(msg)
            # print(datetime.datetime.utcnow(), txt)

