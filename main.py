from flask import Flask, request, abort, redirect, url_for, Response
from database import get_db
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
    get_db().remove()


@app.route('/v1/auth', methods=['POST'])
@returns_json
def auth():
    if not request.json or not 'username' in request.json:
        abort(400)
    username = request.json['username']

    user = User.query.filter_by(name=username).first()

    if user is None:
        user = User(username, username + '@')
        get_db().add(user)
        get_db().commit()

    encoded = jwt.encode({'id': user.id}, secret, algorithm='HS256')

    return json.dumps({'token': encoded})


@app.route('/v1/user/<int:user_id>')
@returns_json
def user_by_id(user_id):
    """
    Get a user by user ID.
    """
    user = User.query.get(user_id)

    if user is None:
        abort(404)

    return json.dumps(user.as_dict(include_teams_and_permissions=True))


# team CRUD

@app.route('/v1/team/<int:team_id>', methods=['POST'])
@returns_json
def team_add(team_id):
    """
    Add a team given a team name
    """
    name = request.json['name']

    if name is None:
        abort(400)

    team = Team(name=name)

    get_db().add(team)
    get_db().commit()

    return '', 201


@app.route('/v1/team/<int:team_id>', methods=['GET'])
@returns_json
def team_read(team_id):
    """
    Get a team's info
    """
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
    """
    Update a team's name given name
    """
    team = Team.query.get(id=team_id)

    if team is None:
        abort(400)

    name = request.json['name']
    if name is None or name is '':
        abort(400)

    team.name = name
    get_db().commit()

    return '', 200


@app.route('/v1/team/<int:team_id>', methods=['DELETE'])
@returns_json
def team_delete(team_id):
    """
    Delete a team given its id
    """
    team = Team.query.get(id=team_id)

    if team is None:
        abort(400)

    get_db().delete(team)
    get_db().commit()

    return '', 200


# add/remove user to team

@app.route('/v1/team_user/<int:team_id>', methods=['POST'])
@returns_json
def team_user_add(team_id):
    """
    Add a user to a team given the team and user ids
    """
    team = Team.query.get(id=team_id)
    if team is None:
        abort(400)

    user_id = request.json['user_id']
    if user_id is None:
        abort(400)

    user = User.query.get(id=user_id)
    if user is None:
        abort(400)

    user.teams.append(team)
    get_db().commit()

    return '', 200


@app.route('/v1/team_user/<int:team_id>', methods=['DELETE'])
@returns_json
def team_user_delete(team_id):
    """
    Remove a user from a team given the team and user ids
    """
    team = Team.query.get(id=team_id)
    if team is None:
        abort(400)

    user_id = request.json['user_id']
    if user_id is None:
        abort(400)

    user = User.query.get(id=user_id)
    if user is None:
        abort(400)

    user.teams.delete(team)
    get_db().commit()

    return '', 200


if __name__ == '__main__':
    app.run()


# reservation CRUD

@app.route('/v1/reservation/<int:res_id>', methods=['POST'])
@returns_json
def reservation_add(res_id):
    """
    Add a reservation given the team id, room id, creator id, start and end datetimes
    """
    team = Team.query.get(id=request.json['team_id'])
    if team is None:
        abort(400)

    room = Room.query.get(id=request.json['room_id'])
    if room is None:
        abort(400)

    creator = User.query.get(id=request.json['creator_id'])
    if creator is None:
        abort(400)

    start = request.json['start']
    if start is None:
        abort(400)

    end = request.json['end']
    if end is None:
        abort(400)

    res = Reservation(team=team, room=room, created_by=creator, start=start, end=end)

    get_db().add(res)
    get_db().commit()

    return '', 201


@app.route('/v1/reservation/<int:res_id>', methods=['GET'])
@returns_json
def reservation_read(res_id):
    """
    Get a reservation's info given id
    """
    res = Reservation.query.get(id=res_id)

    if res is None:
        abort(400)

    return json.dumps({
        'team': res.team,
        'room': res.room,
        'created_by': res.created_by,
        'start': res.start,
        'end': res.end
    })


@app.route('/v1/reservation/<int:res_id>', methods=['PUT'])
@returns_json
def reservation_update(res_id):
    """
    Update a reservation given team id, room id, creator id, start and end datetimes
    """
    team = Team.query.get(id=request.json['team_id'])
    if team is None:
        abort(400)

    room = Room.query.get(id=request.json['room_id'])
    if room is None:
        abort(400)

    creator = User.query.get(id=request.json['creator_id'])
    if creator is None:
        abort(400)

    start = request.json['start']
    if start is None:
        abort(400)

    end = request.json['end']
    if end is None:
        abort(400)

    res = Reservation.query.get(id=res_id)
    if res is None:
        abort(400)

    res.team = team
    res.room = room
    res.created_by = creator
    res.start = start
    res.end = end

    get_db().commit()

    return '', 200


@app.route('/v1/reservation/<int:res_id>', methods=['DELETE'])
@returns_json
def reservation_delete(res_id):
    """
    Remove a reservation given its id
    """
    res = Reservation.query.get(id=res_id)

    if res is None:
        abort(400)

    get_db().delete(res)
    get_db().commit()

    return '', 200


# room CRUD

@app.route('/v1/room/<int:room_id>', methods=['POST'])
@returns_json
def room_add(room_id):
    """
    add a room, given the room number
    """
    if not request.json or 'number' not in request.json:
        abort(400)
    num = request.json['number']

    if num is None or len(num.strip()) == 0:
        abort(400)

    room = Room(number=num)

    try:
        get_db().add(room)
        get_db().commit()
    except IntegrityError:
        abort(500)

    return '', 201


@app.route('/v1/room/<int:room_id>', methods=['GET'])
@returns_json
def room_read(room_id):
    """
    Get a room's info given its id
    """
    room = Room.query.get(id=room_id)

    if room is None:
        abort(400)

    return json.dumps({
        'number': room.number,
        'features': room.users,
        'reservations': room.reservations,
    })


@app.route('/v1/room/<int:room_id>', methods=['PUT'])
@returns_json
def room_update(room_id):
    """
    Update a room given its room number and feature array
    """
    room = Room.query.get(id=room_id)

    if room is None:
        abort(400)

    room.number = request.json['number']
    features = request.json['features']

    # remove relationships not in features
    for r in room.features:
        if r not in features:
            room.features.delete(r)

    # add relationships in features
    for f in features:
        if f not in room.features:
            room.features.add(f)

    get_db().commit()

    return '', 200


@app.route('/v1/room/<int:room_id>', methods=['DELETE'])
@returns_json
def room_delete(room_id):
    """
    Remove a room given its id
    """
    room = Room.query.get(id=room_id)

    if room is None:
        abort(400)

    get_db().delete(room)
    get_db().commit()

    return '', 200


# @app.route('/reservation')
# @returns_json
# def get_reservations():
#     reservations =


if __name__ == '__main__':
    app.run()
