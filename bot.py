import os
from redis import StrictRedis

START_TEXT = """Hi! Nice to meet you.
Thank you for choosing Singapore Airlines.
To find out what I can help you with, send /help
"""

HELP_TEXT = """I'm Kris, your Journey Concierge.
I can inform you of your flight details.

Here are some things I can help you with:

/meal - Choose your in-flight meal
/flight - Check information about your flight
/options - Change notification settings and more
/cancel - Cancel the current command
"""

def get_options(uid, option):
    if option == 'Notifications':
        return "Notifications have been turned off"
    return "Sorry, that is not available yet"

def get_meal(uid, meal):
    return "Your choice has been recorded"

def get_attendant(uid, request):
    return "Your request has been received. An attendant will be with you shortly"

def get_flight_info(uid, info):
    if info == 'Timings':
        return "Your flight is departing at 10pm today"
    elif info == "Seat number":
        return "Your seat number is 23A"
    elif info == "Check-in Row":
        return "You will be checking in at T3, Row 8"
    return "Sorry, that is not available yet"

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
        rd.hset(uid, 'pstate', rd.hget(uid, 'state'))
        rd.hset(uid, 'state', state)

    response = {}
    state = rd.hget(uid, 'state')
    prev_state = rd.hget(uid, 'pstate')

    if message.startswith('/'):
        cmd = message[1:]
        if cmd.startswith('start'):
            response['text'] = START_TEXT
        elif cmd == 'help':
            response['text'] = HELP_TEXT
        elif cmd == 'cancel':
            set_state('idle')
            cancel_resp = { 'meal': 'Meal selection cancelled' }
            if state in cancel_resp:
                response['text'] = cancel_resp[state]
        elif cmd == 'options':
            set_state('options')
            response['text'] = "What do you want to change?"
            response['options'] = ("Language", "Notifications")
        elif cmd == 'flight':
            set_state('flight')
            response['text'] = "What can I help you with?"
            response['options'] = ("Timings", "Seat number", "Check-in Row")
        elif cmd == 'queue':
            if state == 'row open':
                rd.rpush('queue', uid)
                response['text'] = "Ok, you are #%d" % rd.llen('queue')
            else:
                response['text'] = "Sorry, your row is not open yet"
        elif cmd == 'meal':
            set_state('meal')
            tier = rd.hget(uid, 'meal')
            if tier is None: tier = 'econ'
            response['text'] = "Choose your meal"
            response['options'] = tuple(rd.smembers('meal:%s' % tier))
    else:
        if state == 'meal':
            response['text'] = get_meal(uid, message)
            set_state(prev_state)
        elif state == 'options':
            response['text'] = get_options(uid, message)
        elif state == 'flight':
            response['text'] = get_flight_info(uid, message)
        elif state in ('inflight', 'boarded'):
            response['text'] = get_attendant(uid, message)
        elif message == '✈':
            response['text'] = "Thank you for choosing Singapore Airlines"
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
        state = rd.hget(u, 'state')
        notified = rd.hget(u,'notified')

        if rd.lindex('queue',0) == u:
            if notified != 'row queue':
                resp['text'] = "You are up next in the queue\nPlease be there in 5 minutes"
                rd.hset(u, 'notified', 'row queue')

        elif state == "checked in":
            if notified != 'checked in'
                resp['text'] = "The boarding gate is about 20 minutes away"
                rd.hset(u, 'notified', 'checked in')

        elif status and status != notified:
            if status == "gate open":
                resp['text'] = "Your boarding gate is open."
            elif status == "row open":
                resp['text'] = "Your check-in row is open.\nYou can /queue for a number"
            elif status == "boarded":
                resp['text'] = "Welcome Aboard. Feel free to key in any request."
            rd.hset(u, 'notified', status)
            rd.hset(u, 'pstate', state)
            rd.hset(u, 'state', status)

        if resp:
            resp['uid'] = u
            responses.append(resp)

    return responses

REDIS_URL=os.getenv("REDIS_URL")
rd = StrictRedis.from_url(REDIS_URL, decode_responses=True)
