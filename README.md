# Twitter Assistant

A Python-based automation tool for Twitter that crawls new tweets, processes hashtags, and performs delayed actions such as liking and retweeting. The system includes background workers scheduled via cron and a Telegram bot for management and handling updates.

## Purpose
This project automates Twitter interactions, such as monitoring feeds, engaging with content (likes, retweets), and processing hashtag-based tweets. The Telegram bot component allows for real-time management, handling incoming messages or commands to control or monitor the Twitter operations.

## Features
- Scheduled crawling of new tweets every 10 minutes.
- Delayed performance of likes and retweets every 15 minutes for main feeds and hashtags.
- Telegram bot integration for handling updates, with persistent state management using pickle.
- Support for multiple bot aliases configured in `settings.py` (BOTS_POOL).
- Logging for all worker processes.

## Installation
1. Clone the repository:  
   `git clone https://github.com/whereismyguts/twitter-assistant.git`
2. Create a virtual environment:  
   `python -m venv venv`  
   Activate it: `source venv/bin/activate` (Unix/Mac) or `venv\Scripts\activate` (Windows).
3. Install dependencies (based on code; add to `requirements.txt` if not present):  
   `pip install telepot argparse`  
   (Note: Custom modules like `telegram_bot` may require additional setup or are assumed to be part of the repo.)
4. Configure `settings.py` with BOTS_POOL, e.g.:  
   ```python
   BOTS_POOL = {
       'main': {'bot_key': 'YOUR_TELEGRAM_BOT_TOKEN', 'state_file': 'state_main.pickle'},
       'hashtags': {'bot_key': 'ANOTHER_TOKEN', 'state_file': 'state_hashtags.pickle'}
   }
   ```
5. Set up Twitter API credentials if required in workers (not shown in provided code).
6. (Optional) Configure proxy if needed (commented code suggests support for urllib3.ProxyManager).

## Usage
### Running the Telegram Bot
Run the bot for a specific alias:  
```bash
python main.py -n main
```
This starts polling for Telegram updates, processes them with `ManageHandler`, and saves state to the configured pickle file.

### Scheduling Workers with Cron
Add the following to your crontab (adjust paths to match your installation, e.g., `/home/twitter_bot/twitter-assistant`):  
```
*/10 * * * * cd /path/to/twitter-assistant && /path/to/python workers/crawl_new_tweets.py -n main >> log/crawl_main.log
*/15 * * * * cd /path/to/twitter-assistant && /path/to/python workers/perform_with_delay.py -n main -a like >> log/like_main.log
*/15 * * * * cd /path/to/twitter-assistant && /path/to/python workers/perform_with_delay.py -n main -a rt >> log/rt_main.log

*/10 * * * * cd /path/to/twitter-assistant && /path/to/python workers/process_hashtags.py -n hashtags >> log/crawl_hash.log
*/15 * * * * cd /path/to/twitter-assistant && /path/to/python workers/perform_with_delay.py -n hashtags -a like >> log/like_hash.log
*/15 * * * * cd /path/to/twitter-assistant && /path/to/python workers/perform_with_delay.py -n hashtags -a rt >> log/like_hash.log
```
- Use `crontab -e` to edit and save.

## Configuration
- **Bot Aliases**: Defined in `BOTS_POOL` with Telegram bot tokens and state files.
- **State Management**: Uses pickle to track the last processed update ID, preventing duplicate handling.
- **Error Handling**: Catches exceptions, prints tracebacks, and retries after 10 seconds.
- **Proxy Support**: Uncomment and configure proxy settings if operating behind a proxy.

## License
MIT
