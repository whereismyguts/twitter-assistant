import telepot
from settings import debug_chat, BOTS_POOL
import traceback,time

def get_bot(bot_key):
    return telepot.Bot(bot_key)

def send_debug(bot, alias, msg):
    emoji = BOTS_POOL[alias]['emoji']
    debug_text = '[DEBUG]{}: {} BOT\n{}'.format(emoji, alias.upper(), msg)
    for i in range(2):
        try:
            bot.sendMessage(debug_chat, debug_text)
            break
        except telepot.exception.TooManyRequestsError as e:
            print(e, traceback.format_exc())
            sec = e.json.get('parameters',{}).get('retry_after', 5)
            
            print('SLEEPING', sec)
            time.sleep(sec)
        except telepot.exception.TelegramError as tex:
            print(tex)
            return 

def send_to_all_managers(alias, msg):
    emoji = BOTS_POOL[alias]['emoji']
    msg = "[INFO]{}: {} BOT\n{}".format(emoji, alias.upper(), msg)
    bot_key = BOTS_POOL['bot_key']
    print(msg)
    for i in range(2):
        try:
            get_bot(bot_key).sendMessage(debug_chat, msg)
            break
        except telepot.exception.TooManyRequestsError as e:
            print(e, traceback.format_exc())
            sec = e.json.get('parameters',{}).get('retry_after', 5)
            
            print('SLEEPING', sec)
            time.sleep(sec)
        except telepot.exception.TelegramError as tex:
            print(tex)
            return 
        
    # return
    
    
    # for m in db.managers.find():
    #     get_bot().sendMessage(m['chat_id'], msg)


if __name__ == "__main__":
    for i in range(1):
        send_to_all_managers('test', 'testing ' + str(i))
