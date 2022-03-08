from pymongo import MongoClient
from settings import BOTS_POOL

DB_HOST = '127.0.0.1'
client = MongoClient("mongodb://{}:27017/".format(DB_HOST))

__all__ = ('get_database', 'get_random')


def get_database(alias):
    return getattr(client, BOTS_POOL[alias]['db'])

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
