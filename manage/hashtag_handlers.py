from telegram_bot.services import send_to_all_managers
from custom_settings import get_custom_settings
from twitter_api.api import TwitterApi
from telegram_bot.services import get_bot
from workers.crawl_new_tweets import get_some_users, create_order
import traceback

def create_hastag_orders(db, message, alias, chat_id):
    try:
        if len(message.split(' ')) != 3:
            raise Exception("{} is not 3 parts".format(message))
        tag, action, count = message.split(' ')
        count = int(count)
        if count < 10 or count > 100:
            return 'The COUNT must be between 10 and 100'
        if action not in ['like', 'rt']:
            return 'The ACTION value must be one of ["like", "rt"]'
        
        custom_settings = get_custom_settings(db)
        
        posts = list(TwitterApi(db=db).get_tweets_by_query(tag, count))
        user_count =  len(posts) * len(get_some_users(percent=custom_settings['{}_USER_PERCENT'.format(action.upper())]))
        bot = get_bot()
        bot.sendMessage(chat_id, 'Found {} tweets. We creating about {} {} orders, this may take some time, see the log'.format(
            len(list(posts)), 
            user_count,
            action.lower(),
        ))
        user_count = 0
        for post in posts:
            for user in get_some_users(percent=custom_settings['{}_USER_PERCENT'.format(action.upper())]):
                text = create_order(db, post, user, action.lower())
                if text:
                    send_to_all_managers(alias, text)
                user_count += 1
        return 'Found {} tweets with {} hastag. Created {} {} orders.'.format(
            len(list(posts)), 
            tag,
            user_count,
            action.lower(),
        )            
    except Exception as e:
        print("TAG parse error:")
        print(e, traceback.format_exc())
        return "Can't parse the tag command!"
