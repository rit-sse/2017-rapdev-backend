from flask import Flask, request, abort, Response
from database import db_session
from models import *
from functools import wraps
import json
import jwt
from sqlalchemy.exc import IntegrityError
from sqlalchemy import or_
import datetime
import iso8601


app = Flask(__name__)

secret = 'secret'


def returns_json(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        r = f(*args, **kwargs)
        if isinstance(r, tuple):
            return Response(r[0], status=r[1], content_type='application/json')
        else:
            return Response(r, content_type='application/json')
    return decorated_function


@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()


@app.route('/v1/auth', methods=['POST'])
@returns_json
def auth():
    if not request.json or 'username' not in request.json:
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
    """
    Get a user by user ID.
    """
    user = User.query.get(user_id)

    if user is None:
        abort(404)

    return json.dumps(user.as_dict(include_teams_and_permissions=True))


# team CRUD

@app.route('/v1/team', methods=['POST'])
@returns_json
def team_add():
    """
    Add a team given a team name
    """
    name = request.json['name']

    if name is None or len(name.strip()) == 0:
        abort(400)

    team = Team(name=name)

    db_session.add(team)
    db_session.commit()

    return '', 201


@app.route('/v1/team/<int:team_id>', methods=['GET'])
@returns_json
def team_read(team_id):
    """
    Get a team's info
    """
    team = Team.query.get(team_id)
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
    team = Team.query.get(team_id)

    if team is None:
        abort(400)

    name = request.json['name']
    if name is None or len(name.strip()) == 0:
        abort(400)

    team.name = name
    db_session.commit()

    return '', 200


@app.route('/v1/team/<int:team_id>', methods=['DELETE'])
@returns_json
def team_delete(team_id):
    """
    Delete a team given its id
    """
    team = Team.query.get(team_id)
    if team is None:
        abort(400)

    db_session.delete(team)
    db_session.commit()

    return '', 200


# add/remove user to team

@app.route('/v1/team_user/<int:team_id>', methods=['POST'])
@returns_json
def team_user_add(team_id):
    """
    Add a user to a team given the team and user ids
    """
    team = Team.query.get(team_id)
    if team is None:
        abort(400)

    user_id = request.json['user_id']
    if user_id is None or len(user_id.strip()) == 0:
        abort(400)

    user = User.query.get(user_id)
    if user is None:
        abort(400)

    user.teams.append(team)
    db_session.commit()

    return '', 200


@app.route('/v1/team_user/<int:team_id>', methods=['DELETE'])
@returns_json
def team_user_delete(team_id):
    """
    Remove a user from a team given the team and user ids
    """
    team = Team.query.get(team_id)
    if team is None:
        abort(400)

    user_id = request.json['user_id']
    if user_id is None or len(user_id.strip()) == 0:
        abort(400)

    user = User.query.get(user_id)
    if user is None:
        abort(400)

    user.teams.delete(team)
    db_session.commit()

    return '', 200


# reservation CRUD

@app.route('/v1/reservation', methods=['POST'])
@returns_json
def reservation_add():
    """
    Add a reservation given the team id, room id, creator id, start and end datetimes
    """
    team_id = request.json['team_id']
    if team_id is None or len(team_id.strip()) == 0:
        abort(400)

    team = Team.query.get(team_id)
    if team is None:
        abort(400)

    room_id = request.json['room_id']
    if room_id is None or len(room_id.strip()) == 0:
        abort(400)

    room = Room.query.get(room_id)
    if room is None:
        abort(400)

    creator_id = request.json['creator_id']
    if creator_id is None or len(creator_id.strip()) == 0:
        abort(400)

    creator = User.query.get(creator_id)
    if creator is None:
        abort(400)

    start = request.json['start']
    if start is None or len(start.strip()) == 0:
        abort(400)

    end = request.json['end']
    if end is None or len(end.strip()) == 0:
        abort(400)

    res = Reservation(team=team, room=room, created_by=creator, start=start, end=end)

    db_session.add(res)
    db_session.commit()

    return '', 201


@app.route('/v1/reservation/<int:res_id>', methods=['GET'])
@returns_json
def reservation_read(res_id):
    """
    Get a reservation's info given id
    """
    res = Reservation.query.get(res_id)
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
    team_id = request.json['team_id']
    if team_id is None or len(team_id.strip()) == 0:
        abort(400)

    team = Team.query.get(team_id)
    if team is None:
        abort(400)

    room_id = request.json['room_id']
    if room_id is None or len(room_id.strip()) == 0:
        abort(400)

    room = Room.query.get(room_id)
    if room is None:
        abort(400)

    creator_id = request.json['creator_id']
    if creator_id is None or len(creator_id.strip()) == 0:
        abort(400)

    creator = User.query.get(creator_id)
    if creator is None:
        abort(400)

    start = request.json['start']
    if start is None or len(start.strip()) == 0:
        abort(400)

    end = request.json['end']
    if end is None or len(end.strip()) == 0:
        abort(400)

    res = Reservation.query.get(res_id)
    if res is None:
        abort(400)

    res.team = team
    res.room = room
    res.created_by = creator
    res.start = start
    res.end = end

    db_session.commit()

    return '', 200


@app.route('/v1/reservation/<int:res_id>', methods=['DELETE'])
@returns_json
def reservation_delete(res_id):
    """
    Remove a reservation given its id
    """
    res = Reservation.query.get(res_id)
    if res is None:
        abort(400)

    db_session.delete(res)
    db_session.commit()

    return '', 200


# room CRUD

@app.route('/v1/room', methods=['POST'])
@returns_json
def room_add():
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
        db_session.add(room)
        db_session.commit()
    except IntegrityError:
        abort(400)
    return json.dumps(room.as_dict(include_features=False)), 201


@app.route('/v1/room/<int:room_id>', methods=['GET'])
@returns_json
def room_read(room_id):
    """
    Get a room's info given its id
    """
    room = Room.query.get(room_id)
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
    room = Room.query.get(room_id)

    if room is None:
        abort(400)

    number = request.json['number']
    if number is None or len(number.strip()) == 0:
        abort(400)

    room.number = number

    features = request.json['features']
    if features is None:
        abort(400)

    # remove relationships not in features
    for r in room.features:
        if r not in features:
            room.features.delete(r)

    # add relationships in features
    for f in features:
        if f not in room.features:
            room.features.add(f)

    db_session.commit()

    return '', 200


@app.route('/v1/room/<int:room_id>', methods=['DELETE'])
@returns_json
def room_delete(room_id):
    """
    Remove a room given its id
    """
    room = Room.query.get(room_id)
    if room is None:
        abort(400)

    db_session.delete(room)
    db_session.commit()

    return '', 200


@app.route('/v1/reservation', methods=['GET'])
@returns_json
def get_reservations():
    """
    get filtered reservation list
    optional params start, end
    :return: list of reservations
    """

    start_date = request.args.get('start')
    end_date = request.args.get('end')

    if start_date is not None and end_date is not None:
        start = None
        end = None

        try:
            start = iso8601.parse_date(start_date)
            end = iso8601.parse_date(end_date)
        except iso8601.ParseError:
            abort(400)

        reservations = Reservation.query.filter(Reservation.end >= start, Reservation.start <= end)
    else:
        reservations = Reservation.query.filter(or_(Reservation.start >= datetime.datetime.now(),
                                                Reservation.end >= datetime.datetime.now()))

    reservations = map(lambda x: x.as_dict(), reservations)

    return json.dumps(reservations)


if __name__ == '__main__':
    app.run()
