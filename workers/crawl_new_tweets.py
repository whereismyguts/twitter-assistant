from twitter_api.api import TwitterApi

from database.mongo import db
for t in db.tweets.aggregate([{'$sample': {'size': 1}}]):
    print(t)
# for source in db.sources.find():
#     tweets = TwitterApi.get_tweets_by_id(source["id"])
#     for tweet in tweets:
#         print(tweet["id"])
#         print(tweet["text"])
#         db.tweets.update_one(
#             dict(id=tweet["id"]),
#             {"$set": tweet},
#             upsert=True,
#         )
