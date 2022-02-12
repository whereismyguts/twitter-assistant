import telepot
from settings import BOT_KEY
from database.mongo import db
from settings import debug_chat


def get_bot():
    return telepot.Bot(BOT_KEY)


def send_to_all_managers(msg):
    msg = "[INFO]: " + msg
    print(msg)
    # get_bot().sendMessage(debug_chat, msg)
    # return
    
    
    for m in db.managers.find():
        get_bot().sendMessage(m['chat_id'], msg)
