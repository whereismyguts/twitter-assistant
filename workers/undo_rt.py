from twitter_api.api import TwitterApi
from database.mongo import db

tweets = [
    '1492293136885993474',
    '1492308138434908162',
]
username = 'promo_nakamoto'


user = db.users.find_one(dict(username=username))
for t in tweets:
    TwitterApi.undo_rt(user, t)
