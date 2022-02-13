from database.mongo import db

DEFAULT_SETTINGS = {
    'DELAY_MINUTES_MAX': 15,
    'DELAY_MINUTES_MIN': 1,
}

# db.settings.insert_one(DEFAULT_SETTINGS)

def get_custom_settings():
    settings = db.settings.find_one() or dict()
    for key, val in DEFAULT_SETTINGS.items():
        settings[key] = settings.get(key) or val
    return settings


def set_custom_settings(data):
    settings = db.settings.find_one() or dict()
    settings.update(data)
    if '_id' in settings:
        db.settings.update_one(
            {'_id': settings['_id']}, 
            {'$set': data},
        )
    else:
        db.settings.insert_one(data)
        

