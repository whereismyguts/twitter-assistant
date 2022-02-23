import telepot
from settings import BOT_KEY
from database.mongo import db
from settings import debug_chat
import traceback,time

def get_bot():
    return telepot.Bot(BOT_KEY)


def send_to_all_managers(msg):
    msg = "[INFO]: " + msg
    print(msg)
    for i in range(2):
        try:
            get_bot().sendMessage(debug_chat, msg)
            break
        except telepot.exception.TooManyRequestsError as e:
            print(e, traceback.format_exc())
            sec = e.json.get('parameters',{}).get('retry_after', 5)
            
            print('SLEEPING', sec)
            time.sleep(sec)
    # return
    
    
    # for m in db.managers.find():
    #     get_bot().sendMessage(m['chat_id'], msg)


if __name__ == "__main__":
    for i in range(30):
        send_to_all_managers('testing ' + str(i))
