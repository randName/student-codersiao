from flask import request, json
from app import rd, db, app, models
from datetime import datetime

from .models import Flight, Booking, Person

def json_error(message):
    return json.jsonify({'status': 'error', 'message': message})

def json_resp(data):
    data['status'] = 'ok'
    return json.jsonify(data)

def generate_reply(text):
    return "I'm sorry, I couldn't understand that"

@app.route('/')
def index():
    return "Please access the service through the REST API"

@app.route('/booking/<pnr>')
def booking(pnr):
    b = Booking.query.get(pnr)
    if not b: return json_error('No such booking')

    return json_resp({'booking': { 'pnr': b.pnr,
        'flight': tuple(str(f) for f in b.flight),
        'person': tuple(str(p) for p in b.person)
    }})

@app.route('/token')
def token():
    b = Person.query.filter(Person.booking.any(Booking.pnr==request.args.get('pnr')))
    b = b.filter_by(name=request.args.get('name')).first()
    if not b: return json_error('No such person')

    return json_resp({'token': b.generate_token()})

@app.route('/message')
def reply_text():
    p = Person.verify_token(request.args.get('token'))
    if not p: return json_error('Invalid token')

    return json_resp({'reply': generate_reply(request.args.get('text'))})
