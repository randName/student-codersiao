from flask import request, json
from app import rd, db, app, models

@app.route('/')
def index():
    return "Hello World!"
