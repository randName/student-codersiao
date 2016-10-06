from app import db, app
from itsdangerous import URLSafeSerializer, BadSignature

booking_person = db.Table('booking_person',
    db.Column('pnr', db.String(6), db.ForeignKey('booking.pnr')),
    db.Column('person', db.Integer, db.ForeignKey('person.pid')),
)

booking_flight = db.Table('booking_flight',
    db.Column('pnr', db.String(6), db.ForeignKey('booking.pnr')),
    db.Column('flight', db.Integer, db.ForeignKey('flight.fid')),
)


class Person(db.Model):
    pid = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    seat = db.Column(db.String(4))

    def __init__(s, name, seat=None):
        s.name = name
        s.seat = seat

    def generate_token(s):
        ser = URLSafeSerializer(app.config['TOKEN_KEY'])
        return ser.dumps({ 'pid': s.pid, 's': s.seat })

    @staticmethod
    def verify_token(token):
        s = URLSafeSerializer(app.config['TOKEN_KEY'])
        try:
            data = s.loads(token)
        except BadSignature:
            return None
        return Person.query.get(data['pid'])

    def __str__(s):
        return "%s" % s.name

    def __repr__(s):
        return "<Person %s>" % s.pid


class Booking(db.Model):
    pnr = db.Column(db.String(6), primary_key=True)
    person = db.relationship('Person', secondary=booking_person, backref='booking')
    flight = db.relationship('Flight', secondary=booking_flight)

    def __init__(s, pnr):
        s.pnr = pnr

    def __str__(s):
        return "%s" % s.pnr

    def __repr__(s):
        return "<Booking %s>" % s.pnr


class Flight(db.Model):
    fid = db.Column(db.Integer, primary_key=True)
    flight_no = db.Column(db.Integer)
    departure = db.Column(db.DateTime)
    arrival = db.Column(db.DateTime)
    start = db.Column(db.String(3))
    dest = db.Column(db.String(3))

    def __init__(s, fn, st, dep, dt, arv):
        s.flight_no = fn
        s.start = st
        s.departure = dep
        s.dest = dt
        s.arrival = arv

    @property
    def duration(s):
        return s.arrival - s.departure

    @property
    def date(s):
        return s.departure.date()

    @property
    def time(s):
        return s.departure.time()

    def __str__(s):
        return "SQ{0} {2}✈{3} ({1:%x %X})".format(s.flight_no, s.departure, s.start, s.dest)

    def __repr__(s):
        return "<Flight SQ%s>" % s.flight_no
