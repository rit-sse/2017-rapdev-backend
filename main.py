from flask import Flask
app = Flask(__name__)
from database import db_session
import models
import json

@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()

@app.route('/')
def hello_world():
    temp = []
    for u in models.User.query.all():
        temp.append(u.as_dict())
    return json.dumps(temp)

@app.route('/create')
def create():
    u = models.User('test','test@')
    db_session.add(u)
    db_session.commit()
    return str(models.User.query.all())


