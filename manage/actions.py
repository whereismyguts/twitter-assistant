from twitter_api.api import TwitterApi


def set_like(db, post_id):
    
    for user in  db.users.aggregate([{'$sample': {'size': 1}}]):
        response = TwitterApi.set_like(user, post_id)
        print("TODO remove:")
        print(response)
        return "👍🏻 by {}".format(user['username'])
