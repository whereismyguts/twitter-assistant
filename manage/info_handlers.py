from custom_settings import get_custom_settings
import json 

def get_stats(db):
    users_ = list(db.users.find(dict(deleted=False)))
    blocked_users = []
    ok_users = []
    for u in users_:
        if u['status'] == 'blocked':
            blocked_users.append(u['username'])
        else:
            ok_users.append(u['username'])
    sources = [u['username'] for u in db.sources.find(dict(deleted=False))]
    rt_orders = db.orders.find(dict(status='new', action='rt'))
    like_orders = db.orders.find(dict(status='new', action='like'))
    hashtag_tasks = list(db.hashtag_tasks.find({'status': 'active'}))
    errors = db.orders.find(dict(status='error'))
    text = '''Users pool ({}):
{}

Blocked ({}):
{}

Sources ({}):
{}

Active hashtag tasks ({}):
{}

Orders in queue:
Like: {}
Retweet: {}
Errors: {}

Configuration values: {}'''.format(
        len(ok_users), '\n'.join(ok_users),
        len(blocked_users), '\n'.join(blocked_users),
        len(sources), '\n'.join(sources),
        len(hashtag_tasks), '\n'.join([' '.join(h['tags']) + ' by @'+h['user']['username'] for h in hashtag_tasks]),
        like_orders and len(list(like_orders)) or 0, 
        rt_orders and len(list(rt_orders)) or 0, 
        errors and len(list(errors)) or 0,
        json.dumps(get_custom_settings(db), indent=4)
    )
    return text
