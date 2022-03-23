
from database.mongo import get_database

def get_last_request(user_id, db=None):
    db = db or get_database('main')
    user = db.last_requests.find_one({'user_id': user_id})
    if user:
        return user['last_request']
    
def set_last_request(user_id, last_req, db=None):
    db = db or get_database('main')
    db.last_requests.update_one(
        {"user_id": user_id},
        {"$set": {'last_request': last_req}},
        upsert=True,
    )
    
    