from flask import Flask, request, abort
app = Flask(__name__)
from database import db_session
import models
import json
import jwt



secret = 'secret'

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

@app.route('/api/v1/auth', methods=['POST'])
def auth():
    username=request.form['username']

    user = models.User.query.filter_by(name=username).first()
    
    if user is None:
        user = models.User(username, username + '@')
        db_session.add(user)
        db_session.commit()
        
    encoded = jwt.encode({'id': user.id}, secret, algorithm='HS256') 

    return json.dumps({'token': encoded})


@app.route('/api/v1/user/<int:user_id>')
def user_by_id(user_id):
    """Get a user by user ID."""
    user = models.User.query.get(user_id)

    if user is None:
        abort(404)

    return json.dumps(user.as_dict())


if __name__ == '__main__':
    app.run()
