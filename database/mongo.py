from pymongo import MongoClient

DB_HOST = '127.0.0.1'
client = MongoClient("mongodb://{}:27017/".format(DB_HOST))
db = client.test_database

__all__ = ('db',)
