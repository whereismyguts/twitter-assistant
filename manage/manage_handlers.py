import traceback
import datetime
from twitter_api.api import TwitterApi


def set_authorize_state(db, manager, chat_id, tmp_state, response_message, extra_data=None):
    try:
        auth_url, owner_token, owner_secret = TwitterApi.get_authorization_url()
        manager["owner_token"] = owner_token
        manager["owner_secret"] = owner_secret
        manager["state"] = tmp_state
        if extra_data:
            manager.update(extra_data)
            print(manager)
    except Exception as e:
        print(e, traceback.format_exc())
        return "error, " + str(e)
    response = db.managers.update_one(
        {"chat_id": chat_id},
        {"$set": manager},
        upsert=False,
    )
    return response_message + auth_url
    


def handle_enter_pin(db, manager, message, chat_id):
    owner_token = manager["owner_token"]
    owner_secret = manager["owner_secret"]
    if not (owner_token and owner_secret):
        manager["state"] = "main"
        response = db.managers.update_one(
            {"chat_id": chat_id},
            {"$set": manager},
            upsert=False,
        )
        return "error, cant find your auth session data, try again"
    try:
        access_token, access_token_secret = TwitterApi.verify_pin(
            message, owner_token, owner_secret
        )
    except Exception as e:
        return "error, " + str(e)
    finally:
        try:
            manager['state'] = 'main'
            response = db.managers.update_one(
                {"chat_id": chat_id},
                {"$set": manager},
                upsert=False,
            )
        except:
            pass

    try:
        # check authorization:
        user_data = TwitterApi.get_user_data_me(access_token, access_token_secret)
    except Exception as e:
        print(e, traceback.format_exc())
        return "Error, " + str(e)
    user_data["access_token"] = access_token
    user_data["access_token_secret"] = access_token_secret
    user_data['deleted'] = False
    return user_data
    

def handle_add_source(db, username):
    try:
        user_data = TwitterApi(db=db).get_user_data_by_username(username)
    except Exception as e:
        print(e)
        return 'Could not find user with username "{}"'.format(username)
    user_data['deleted'] = False
    source = db.sources.find_one({"id": user_data["id"]})
    user_data['created'] = datetime.datetime.utcnow()
    if source:
        if not source['deleted']:
            return "@{} is already in source list".format(username)
        
        db.sources.update_one({"id": user_data["id"]}, {'$set': user_data})
        return "@{} revoked in source list ✅".format(username)
    else:    
        db.sources.insert_one(user_data)
        return "@{} added to source list ✅".format(username)
