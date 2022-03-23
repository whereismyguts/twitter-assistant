from settings import consumer_key, consumer_secret
from requests_oauthlib import OAuth1Session
from database.mongo import get_database
import json
import datetime

class TwitterApi():

    _user = None

    def __init__(self, alias=None, db=None):
        if db is None:
            self.db = get_database(alias)
            
        else:
            self.db = db
            
        
    def get_user(self):
        if self._user is None:
            self._user = self.db.users.find_one({'status': 'ok'})
        if not self._user:
            raise Exception("need at least one user authorized")
        return self._user

    def create_oauth_session(self, user=None):
        user = user or self.get_user()
        return OAuth1Session(
            consumer_key,
            client_secret=consumer_secret,
            resource_owner_key=user["access_token"],
            resource_owner_secret=user["access_token_secret"],
        )


    def check_all_users(self):
        users=list(self.db.users.find(dict(deleted=False)))
        params = {"usernames": 'jack', "user.fields": "id,name,username"}
        
        for u in users:
            oauth = self.create_oauth_session(user=u)
            response = oauth.get("https://api.twitter.com/2/users/by", params=params)
            if 'status' in response.json() and response.json()['status'] == 403:
                print(u['username'])
                u['status'] = 'blocked'
            else:
                # print(u['username'])
                # print(response.text)
                u['status'] = 'ok'
            self.db.users.update_one(
                {"id": u['id']},
                {"$set": u},
            )
            
    def get_user_data_by_username(self, username):
        params = {"usernames": username, "user.fields": "id,name,username"}
        oauth = self.create_oauth_session()
        response = oauth.get("https://api.twitter.com/2/users/by", params=params)
        print(json.dumps(response.json(), indent=4, sort_keys=True))
        return response.json()["data"][0]

    def get_tweets_by_query(self, query, count=100, start_dt=None, user=None):
        oauth = self.create_oauth_session(user=user)
        params = {
            "query": query + ' -is:retweet', 
            "max_results": count,
            "tweet.fields": "id,author_id,text,created_at",
        }
        if start_dt:
            # 'YYYY-MM-DDTHH:mm:ssZ'
            # params["end_time"] = end_dt.strftime("%Y-%M-%dT%H:%M:%SZ")
            start_dt = max(start_dt, datetime.datetime.utcnow() - datetime.timedelta(days=7))
            params['start_time'] = start_dt.isoformat('T')[:-3] + 'Z'
            
        response = oauth.get('https://api.twitter.com/2/tweets/search/recent', params=params)
        if response.status_code != 200:
            raise Exception(
                "Request returned an error: {} {}".format(
                    response.status_code, response.text
                )
            )
        
        print(json.dumps(response.json(), indent=4, sort_keys=True))
        if response.json()['meta']['result_count'] == 0:
            return []
        json_response = response.json()["data"]
        return json_response
    
    def get_user_data_me(access_token, access_token_secret):
        oauth = OAuth1Session(consumer_key, client_secret=consumer_secret)

        oauth = OAuth1Session(
            consumer_key,
            client_secret=consumer_secret,
            resource_owner_key=access_token,
            resource_owner_secret=access_token_secret,
        )
        params = {"user.fields": "id,name"}
        response = oauth.get("https://api.twitter.com/2/users/me", params=params)

        if response.status_code != 200:
            raise Exception(
                "Request returned an error: {} {}".format(
                    response.status_code, response.text
                )
            )

        # print("Response code: {}".format(response.status_code))
        json_response = response.json()["data"]
        # print(json.dumps(json_response, indent=4, sort_keys=True))
        return json_response

    @classmethod
    def verify_pin(cls, verifier, resource_owner_key, resource_owner_secret):
        # Get the access token
        access_token_url = "https://api.twitter.com/oauth/access_token"
        oauth = OAuth1Session(
            consumer_key,
            client_secret=consumer_secret,
            resource_owner_key=resource_owner_key,
            resource_owner_secret=resource_owner_secret,
            verifier=verifier,
        )
        oauth_tokens = oauth.fetch_access_token(access_token_url)
        access_token = oauth_tokens["oauth_token"]
        access_token_secret = oauth_tokens["oauth_token_secret"]
        return access_token, access_token_secret

    def get_authorization_url():
        request_token_url = "https://api.twitter.com/oauth/request_token?oauth_callback=oob&x_auth_access_type=write"
        oauth = OAuth1Session(consumer_key, client_secret=consumer_secret)
        try:
            fetch_response = oauth.fetch_request_token(request_token_url)
        except ValueError as e:
            print(
                "There may have been an issue with the consumer_key or consumer_secret you entered.",
                e,
            )

        resource_owner_key = fetch_response.get("oauth_token")
        resource_owner_secret = fetch_response.get("oauth_token_secret")
        # print("Got OAuth token: %s" % resource_owner_key)

        # Get authorization
        base_authorization_url = "https://api.twitter.com/oauth/authorize"
        authorization_url = oauth.authorization_url(base_authorization_url)
        # print("Please go here and authorize: %s" % authorization_url)
        return authorization_url, resource_owner_key, resource_owner_secret

    @classmethod
    def set_like(cls, user, post_id):
        payload = {"tweet_id": post_id}
        oauth = OAuth1Session(
            consumer_key,
            client_secret=consumer_secret,
            resource_owner_key=user["access_token"],
            resource_owner_secret=user["access_token_secret"],
        )
        # print("https://api.twitter.com/2/users/{}/likes".format(post_id), payload)
        # Making the request
        response = oauth.post(
            "https://api.twitter.com/2/users/{}/likes".format(user["id"]), json=payload
        )

        if response.status_code != 200:
            raise Exception(
                "Request returned an error: {} {}".format(
                    response.status_code, response.text
                )
            )

        # print("Response code: {}".format(response.status_code))

        # Saving the response as JSON
        json_response = response.json()
        print(json.dumps(json_response, indent=4, sort_keys=True))
        return json_response

    @classmethod
    def retweet(cls, user, post_id):
        payload = {"tweet_id": post_id}
        oauth = OAuth1Session(
            consumer_key,
            client_secret=consumer_secret,
            resource_owner_key=user["access_token"],
            resource_owner_secret=user["access_token_secret"],
        )

        # Making the request
        response = oauth.post(
            "https://api.twitter.com/2/users/{}/retweets".format(user['id']), json=payload,
        )

        if response.status_code != 200:
            raise Exception(
                "Request returned an error: {} {}".format(response.status_code, response.text)
            )

        print("Response code: {}".format(response.status_code))

        # Saving the response as JSON
        json_response = response.json()
        print(json.dumps(json_response, indent=4, sort_keys=True))
        return json_response
    
    @classmethod
    def undo_rt(cls, user, source_tweet_id):
        oauth = OAuth1Session(
            consumer_key,
            client_secret=consumer_secret,
            resource_owner_key=user["access_token"],
            resource_owner_secret=user["access_token_secret"],
        )

        # Making the request
        response = oauth.delete(
            "https://api.twitter.com/2/users/{}/retweets/{}".format(user['id'], source_tweet_id)
        )

        if response.status_code != 200:
            raise Exception(
                "Request returned an error: {} {}".format(response.status_code, response.text)
            )

        print("Response code: {}".format(response.status_code))

        # Saving the response as JSON
        json_response = response.json()
        print(json.dumps(json_response, indent=4, sort_keys=True))
        
        
    def get_tweets_by_id(self, user_id, last_id=None, start_dt=None):
        url = "https://api.twitter.com/2/users/{}/tweets".format(user_id)
        # Tweet fields are adjustable.
        # Options include:
        # attachments, author_id, context_annotations,
        # conversation_id, created_at, entities, geo, id,
        # in_reply_to_user_id, lang, non_public_metrics, organic_metrics,
        # possibly_sensitive, promoted_metrics, public_metrics, referenced_tweets,
        # source, text, and withheld
        params = {
            "tweet.fields": "id,author_id,text,created_at,in_reply_to_user_id",
            "exclude": "retweets,replies",
        }
        if last_id:
            params["since_id"] = last_id

        if start_dt:
            # 'YYYY-MM-DDTHH:mm:ssZ'
            # params["end_time"] = end_dt.strftime("%Y-%M-%dT%H:%M:%SZ")
            params['start_time'] = start_dt.isoformat('T')[:-3] + 'Z'
        print(params)
        oauth = self.create_oauth_session()
        response = oauth.get(url, params=params)
        print(response.status_code)
        if response.status_code != 200:
            raise Exception(
                "Request returned an error: {} {}".format(
                    response.status_code, response.text
                )
            )
        # print(json.dumps(response.json(), indent=2, ensure_ascii=False))
        if response.json().get("meta", {}).get("result_count") == 0:
            return []
        return response.json()["data"]


if __name__ == "__main__":
    db = get_database('main')
    TwitterApi(db=db).check_all_users()
