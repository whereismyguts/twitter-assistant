from pymongo import MongoClient

DB_HOST = '127.0.0.1'
client = MongoClient("mongodb://{}:27017/".format(DB_HOST))
db = client.andrew_db

__all__ = ('db', 'get_random')


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
