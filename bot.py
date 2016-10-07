import os
from redis import StrictRedis

START_TEXT = """Hi! Nice to meet you.
Thank you for choosing Singapore Airlines.
To find out what I can help you with, send /help
"""

HELP_TEXT = """I'm your friendly attendant.

You can ask for information by sending these commands:

/meal - Choose your in-flight meal
/flight - Check information about your flight
/options - Change notification settings and more
/cancel - Cancel the current command
"""

def bot_message(uid, message):

    def set_state(state):
        rd.hset(uid, 'state', state)

    response = {}
    state = rd.hget(uid, 'state')

    if message.startswith('/'):
        cmd = message[1:]
        if cmd == 'start':
            response['text'] = START_TEXT
        elif cmd == 'help':
            response['text'] = HELP_TEXT
        elif cmd == 'cancel':
            set_state('idle')
            cancel_resp = { 'meal': 'Meal selection cancelled' }
            response['text'] = cancel_resp[state]
        elif cmd == 'options':
            set_state('options')
            response['text'] = "What do you want to change?"
            response['options'] = ("Language", "Notifications")
        elif cmd == 'flight':
            set_state('flight')
            response['text'] = "What can I help you with?"
            response['options'] = ("Timings", "Seat number", "Check-in Row")
        elif cmd == 'meal':
            set_state('meal')
            tier = rd.hget(uid, 'meal')
            if tier is None: tier = 'econ'
            response['text'] = "Choose your meal"
            response['options'] = tuple(rd.smembers('meal:%s' % tier))
    else:
        response['text'] = "Ok!"

    return response

REDIS_URL=os.getenv("REDIS_URL")
rd = StrictRedis.from_url(REDIS_URL, decode_responses=True)