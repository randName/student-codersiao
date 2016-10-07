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

def get_id(service, sid=None, uid=None):
    if sid:
        return rd.hget(service, sid)
    if uid:
        return rd.hget('%s:r' % service, uid)

def bot_init(service, sid, uid):
    rd.hset(service, sid, uid)
    rd.hset('%s:r' % service, uid, sid)
    return uid

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
        if state == 'meal'
            response['text'] = "You have selected %s as your inflight meal" % message
            set_state('idle')
        elif state == 'options':
            if message == 'Notifications':
                response['text'] = "Notifications have been turned off."
            set_state('idle')
        elif state == 'flight':
            if message == 'Timings':
                response['text'] = "Your flight is departing at 10pm today."
            elif message == "Seat number":
                response['text'] = "Your seat number is 23A. Have a pleasant flight."
            elif message == "Check-in Row":
                response['text'] = "You will be checking in at row 8."
            set_state('idle')
        else:
            response['text'] = "I'm sorry, I didn't understand that."

    return response

def bot_updates():
    responses = []
    flights = { f:rd.get('flight:%s'%f)for f in rd.smembers('flights') }

    for u in rd.smembers('users'):
        resp = {}
        f = rd.hget(u,'flight')
        status = flights.get(f, None)
        notified = rd.hget(u,'notified')

        if status != notified:
            if status == "gate open":
                resp['text'] = "Your boarding gate is open."
            elif status == "row open":
                resp['text'] = "Your check-in row is open.\nYou can /queue for a number"
            rd.hset(u, 'notified', status)

        if resp:
            resp['uid'] = u
            responses.append(resp)

    return responses

REDIS_URL=os.getenv("REDIS_URL")
rd = StrictRedis.from_url(REDIS_URL, decode_responses=True)
