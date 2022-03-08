

DEFAULT_SETTINGS = {
    'DELAY_MINUTES_MAX': 15,
    'DELAY_MINUTES_MIN': 1,
    'LIKE_USER_PERCENT': 0.8,
    'RT_USER_PERCENT': 0.5,
    'USER_COOLDOWN_SECONDS': 10*60,
}

# db.settings.insert_one(DEFAULT_SETTINGS)

emojis = {
    ('like', 'ENQUEUED'): '💛 ',
    ('rt', 'ENQUEUED'): '🟨 ',
    ('like', 'DONE'):'💚 ',
    ('rt', 'DONE'):'🟩 ',
}

def get_custom_settings(db):
    settings = db.settings.find_one() or dict()
    for key, val in DEFAULT_SETTINGS.items():
        settings[key] = settings.get(key) if settings.get(key) is not None else val
    settings = dict(settings)
    if '_id' in settings:
        del settings['_id']
    return settings



def set_custom_settings(db, data):
    settings = db.settings.find_one() or dict()
    settings.update(data)
    if '_id' in settings:
        db.settings.update_one(
            {'_id': settings['_id']}, 
            {'$set': data},
        )
    else:
        db.settings.insert_one(data)
        

