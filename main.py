from flask import Flask, request, abort, Response
app = Flask(__name__)
from database import db_session
from functools import wraps
import models
import json
import jwt


secret = 'secret'


def returns_json(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        r = f(*args, **kwargs)
        return Response(r, content_type='application/json')
    return decorated_function

@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()


@app.route('/api/v1/auth', methods=['POST'])
@returns_json
def auth():
    username = request.form['username']

    user = models.User.query.filter_by(name=username).first()

    if user is None:
        user = models.User(username, username + '@')
        db_session.add(user)
        db_session.commit()

    encoded = jwt.encode({'id': user.id}, secret, algorithm='HS256')

    return json.dumps({'token': encoded})



@app.route('/api/v1/user/<int:user_id>')
@returns_json
def user_by_id(user_id):
    """Get a user by user ID."""
    user = models.User.query.get(user_id)

    if user is None:
        abort(404)

    return json.dumps(user.as_dict())





if __name__ == '__main__':
    app.run()
