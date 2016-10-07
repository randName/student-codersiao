import os
import logging
from telegram import KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardHide
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, Filters, Job
from telegram.ext import MessageHandler, CallbackQueryHandler
from bot import get_id, bot_init, bot_message, bot_updates

def keyboard_buttons(inline=False, **kwargs):
    if 'options' not in kwargs:
        return ReplyKeyboardHide()

    buttons = kwargs.get('options', ('✈',)),

    def makerow(r):
        if not inline:
            return tuple(KeyboardButton(n) for n in r)
        return tuple(
            InlineKeyboardButton(n, callback_data=i) for i, n in r.items()
        )

    makemarkup = InlineKeyboardMarkup if inline else ReplyKeyboardMarkup

    if 'resize_keyboard' not in kwargs:
        kwargs['resize_keyboard'] = True
    if 'one_time_keyboard' not in kwargs:
        kwargs['one_time_keyboard'] = True

    return makemarkup(tuple(makerow(row) for row in buttons), **kwargs)

def button(bot, update):
    query = update.callback_query
    uid = get_id('telegram', update.message.from_user['id'])
    response = bot_message(uid, query.data)
    response['reply_markup'] = keyboard_buttons(**response)

    if response.get('edit', False):
        response['chat_id'] = query.message.chat_id
        response['message_id'] = query.message.message_id
        bot.editMessageText(**response)
    elif 'text' in response:
        update.message.reply_text(**response)

def handle_message(bot, update):
    m = update.message

    uid = get_id('telegram', m.from_user['id'])
    if uid is None:
        if m.text.startswith('/start'):
            uid = bot_init('telegram', m.from_user['id'], m.text[7:])
        else:
            print( m.from_user['id'] )
            m.reply_text("I'm sorry, service not initalized")
            return

    response = bot_message(uid, m.text)
    response['reply_markup'] = keyboard_buttons(**response)

    if 'text' in response:
        m.reply_text(**response)

def check_status(bot, job):
    responses = bot_updates()

    for r in responses:
        r['reply_markup'] = keyboard_buttons(**r)
        r['chat_id'] = get_id('telegram', uid=r['uid'])
        bot.sendMessage(**r)

TG_TOKEN=os.getenv("TELEGRAM_TOKEN")
REFRESH_INTERVAL = 10.0

logging.basicConfig(level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

logger = logging.getLogger(__name__)

def error(bot, update, error):
    logger.warn('Update "%s" caused error "%s"' % (update, error))

updater = Updater(token=TG_TOKEN)
d = updater.dispatcher
d.add_handler(CallbackQueryHandler(button))
d.add_handler(MessageHandler(None, handle_message))
d.add_error_handler(error)
updater.job_queue.put(Job(check_status, REFRESH_INTERVAL), next_t=0.0)
updater.start_polling()
updater.idle()
