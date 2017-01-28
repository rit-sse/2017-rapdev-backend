from flask import Flask, request, abort, redirect, url_for, Response
from database import db_session
from models import *
from functools import wraps
import json
import jwt
from sqlalchemy.exc import IntegrityError


app = Flask(__name__)

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


@app.route('/v1/auth', methods=['POST'])
@returns_json
def auth():
    if not request.json or not 'username' in request.json:
        abort(400)
    username = request.json['username']

    user = User.query.filter_by(name=username).first()

    if user is None:
        user = User(username, username + '@')
        db_session.add(user)
        db_session.commit()

    encoded = jwt.encode({'id': user.id}, secret, algorithm='HS256')

    return json.dumps({'token': encoded})


@app.route('/v1/user/<int:user_id>')
@returns_json
def user_by_id(user_id):
    """Get a user by user ID."""
    user = User.query.get(user_id)

    if user is None:
        abort(404)

    return json.dumps(user.as_dict(include_teams_and_permissions=True))



# team CRUD

@app.route('/v1/team/<int:team_id>', methods=['POST'])
@returns_json
def team_add(team_id):
    name = request.form['name']

    if name is None:
        abort(400)

    team = Team(name=name)

    db_session.add(team)
    db_session.commit()

    return '', 201


@app.route('/v1/team/<int:team_id>', methods=['GET'])
@returns_json
def team_read(team_id):
    team = Team.query.get(id=team_id)

    if team is None:
        abort(400)

    return json.dumps({
        'name': team.name,
        'members': team.users
    })


@app.route('/v1/team/<int:team_id>', methods=['PUT'])
@returns_json
def team_update(team_id):
    team = Team.query.get(id=team_id)

    if team is None:
        abort(400)

    team.name = request.form['name']
    db_session.commit()

    return '', 200


@app.route('/v1/team/<int:team_id>', methods=['DELETE'])
@returns_json
def team_delete(team_id):
    team = Team.query.get(id=team_id)

    if team is None:
        abort(400)

    db_session.remove(team)
    db_session.commit()

    return '', 200

if __name__ == '__main__':
    app.run()


@app.route('/v1/room', methods=['POST'])
@returns_json
def room_add():
    '''
    add a room, given the room number
    '''
    if not request.json or 'number' not in request.json:
        abort(400)
    num = request.json['number']

    if num is None or len(num.strip()) == 0:
        abort(400)

    room = Room(number=num)

    try:
        db_session.add(room)
        db_session.commit()
    except IntegrityError:
        abort(500)

    return room.as_dict(include_features=False)


# @app.route('/reservation')
# @returns_json
# def get_reservations():
#     reservations =



if __name__ == '__main__':
    app.run()
