"""Teamroom Tracking System.

Main logic and API routes.
"""

from flask import Flask, request, abort, Response
from database import get_db, init_db
from models import *
from functools import wraps
import json
from sqlalchemy.exc import IntegrityError
from sqlalchemy import or_
import datetime
import iso8601
from werkzeug.exceptions import HTTPException

app = Flask(__name__)


def returns_json(f):
    """Decorator to add the content type to responses."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            r = f(*args, **kwargs)
        except HTTPException as e:
            # monkey-patch the headers / body to be json
            headers = e.get_headers()
            for header in headers:
                if 'Content-Type' in header:
                    headers.remove(header)
            headers.append(('Content-Type', 'application/json'))
            e.get_headers = lambda x: headers
            e.get_body = lambda x: "{}"
            raise e
        if isinstance(r, tuple):
            return Response(r[0], status=r[1], content_type='application/json')
        else:
            return Response(r, content_type='application/json')
    return decorated_function


def includes_user(f):
    """Add a request user parameter to the decorated function."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'Authorization' not in request.headers or \
                not request.headers['Authorization'].startswith('Bearer '):
            abort(401)
        else:
            token = request.headers['Authorization'][len('Bearer '):]
            u = User.verify_auth_token(token)
            if u is None:
                abort(401)
            else:
                return f(u, *args, **kwargs)
    return decorated_function


def json_param_exists(param_name, json_root=-1):
    """Check if the given parameter exists and is valid.

    If a json_root is included, check within that. Otherwise, use request.json.
    Checks:
    - Is the json_root "Truthy" (not None, not blank, etc.)?
    - Is the parameter name in the json_root?
    - Is the value not None?
    """
    if json_root == -1:
        json_root = request.json
    return json_root and \
        param_name in json_root and \
        json_root[param_name] is not None


@app.teardown_appcontext
def shutdown_session(exception=None):
    """End the database session."""
    get_db().remove()


@app.route('/v1/auth', methods=['POST'])
@returns_json
def auth():
    """Authenticate users."""
    if not json_param_exists('username'):
        abort(400)
    username = request.json['username']

    user = User.query.filter_by(name=username).first()

    if user is None:
        user = User(username, username + '@')
        get_db().add(user)
        get_db().commit()

    encoded = user.generate_auth_token()

    return json.dumps({'token': encoded})


@app.route('/v1/user/<int:user_id>')
@returns_json
def user_read(user_id):
    """Get a user by user ID."""
    user = User.query.get(user_id)

    if user is None:
        abort(404)

    return json.dumps(user.as_dict(include_teams_and_permissions=True))


# team CRUD

@app.route('/v1/team', methods=['POST'])
@returns_json
@includes_user
def team_add(token_user):
    """Add a team given a team name."""
    if not json_param_exists('name') or \
            not json_param_exists('type'):
        abort(400)
    name = request.json['name']
    team_type = TeamType.query.filter_by(name=request.json['type']).first()
    if not team_type:
        abort(400)

    if team_type.name == 'other_team':
        if not token_user.has_permission('team.create') and \
                not token_user.has_permission('team.create.elevated'):
            abort(403)
    else:  # creating any team other than 'other_team' requires elevated
        if not token_user.has_permission('team.create.elevated'):
            abort(403)

    team = Team(name=name)
    team.team_type = team_type

    get_db().add(team)
    # TODO if unique check on name fails this will throw an exception
    get_db().commit()

    return '', 201


@app.route('/v1/team/<int:team_id>', methods=['GET'])
@returns_json
@includes_user
def team_read(token_user, team_id):
    """Get a team's info."""
    team = Team.query.get(team_id)
    if team is None:
        abort(404)

    if (token_user.has_permission('team.read.elevated') or
            any(map(lambda u: u.id == token_user.id, team.members))):
        return json.dumps(team.as_dict(with_details=True))

    return json.dumps(team.as_dict(with_details=False))


@app.route('/v1/team/<int:team_id>', methods=['PUT'])
@returns_json
# TODO make this accept a user
def team_update(team_id):
    """Update a team's name given name."""
    team = Team.query.get(team_id)

    if team is None:
        abort(404)

    # TODO ensure the user is permitted to modify this team

    name = request.json['name']  # TODO change this to json_param_exists
    if name is None or len(name.strip()) == 0:
        abort(400)

    team.name = name
    get_db().commit()

    return '', 200


@app.route('/v1/team/<int:team_id>', methods=['DELETE'])
@returns_json
# TODO make this accept a user
def team_delete(team_id):
    """Delete a team given its ID."""
    team = Team.query.get(team_id)
    if team is None:
        abort(404)

    # TODO ensure the user is permitted to delete this team
    # TODO deschedule any reservations this team

    get_db().delete(team)
    get_db().commit()

    return '', 200


# add/remove user to team

@app.route('/v1/team_user/<int:team_id>', methods=['POST'])
@returns_json
def team_user_add(team_id):
    """Add a user to a team given the team and user IDs."""
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
    get_db().commit()

    return '', 200


@app.route('/v1/team_user/<int:team_id>', methods=['DELETE'])
@returns_json
def team_user_delete(team_id):
    """Remove a user from a team given the team and user IDs."""
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
    get_db().commit()

    return '', 200


# reservation CRUD

@app.route('/v1/reservation', methods=['POST'])
@returns_json
def reservation_add():
    """Add a reservation.

    Uses the team ID, room ID, created by ID, start and end datetimes.
    """
    if not json_param_exists('team_id') or \
       not json_param_exists('room_id') or \
       not json_param_exists('created_by_id') or \
       not json_param_exists('start') or \
       not json_param_exists('end'):
        abort(400)

    team_id = request.json['team_id']
    team = Team.query.get(team_id)
    if team is None:
        abort(400)

    room_id = request.json['room_id']
    room = Room.query.get(room_id)
    if room is None:
        abort(400)

    # TODO make this come from the submitted token
    created_by_id = request.json['created_by_id']
    created_by = User.query.get(created_by_id)
    if created_by is None:
        abort(400)

    start = request.json['start']
    end = request.json['end']

    res = Reservation(team=team, room=room, created_by=created_by,
                      start=start, end=end)

    # TODO prevent double-booking

    get_db().add(res)
    get_db().commit()

    return '', 201


@app.route('/v1/reservation/<int:res_id>', methods=['GET'])
@returns_json
def reservation_read(res_id):
    """Get a reservation's info given ID."""
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
@includes_user
def reservation_update(token_user, res_id):
    """Update a reservation.

    Uses a room ID, start and end datetimes.
    """
    if not json_param_exists('room_id') or \
       not json_param_exists('start') or \
       not json_param_exists('end'):
        abort(400)

    room_id = request.json['room_id']
    room = Room.query.get(room_id)
    if room is None:
        abort(400)

    start = request.json['start']
    end = request.json['end']

    res = Reservation.query.get(res_id)
    if res is None:
        abort(400)

    if not token_user.has_permission('reservation.update.elevated'):
        is_my_reservation = any(map(lambda m: m.id == token_user.id,
                                    res.team.members))
        if not (is_my_reservation and
                token_user.has_permission('reservation.update')):
            abort(403)

    res.room = room
    res.start = start
    res.end = end

    # TODO prevent double-booking

    get_db().commit()

    return '', 200


@app.route('/v1/reservation/<int:res_id>', methods=['DELETE'])
@returns_json
def reservation_delete(res_id):
    """Remove a reservation given its ID."""
    res = Reservation.query.get(res_id)
    if res is None:
        abort(400)

    get_db().delete(res)
    get_db().commit()

    return '', 200


# room CRUD

@app.route('/v1/room', methods=['GET'])
@returns_json
def room_list():
    """List all rooms."""
    rooms = []
    for room in Room.query.all():
        rooms.append(room.as_dict())

    return json.dumps(rooms)


@app.route('/v1/room', methods=['POST'])
@returns_json
def room_add():
    """Add a room, given the room number."""
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
        abort(400)
    return json.dumps(room.as_dict(include_features=False)), 201


@app.route('/v1/room/<int:room_id>', methods=['GET'])
@returns_json
def room_read(room_id):
    """Get a room's info given its ID."""
    room = Room.query.get(room_id)
    if room is None:
        abort(400)

    return json.dumps({
        'number': room.number,
        'features': room.features,
        'reservations': room.reservations,
    })


@app.route('/v1/room/<int:room_id>', methods=['PUT'])
@returns_json
def room_update(room_id):
    """Update a room given its room number and feature list."""
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

    get_db().commit()

    return '', 200


@app.route('/v1/room/<int:room_id>', methods=['DELETE'])
@returns_json
def room_delete(room_id):
    """Remove a room given its ID."""
    room = Room.query.get(room_id)
    if room is None:
        abort(400)

    get_db().delete(room)
    get_db().commit()

    return '', 200


@app.route('/v1/reservation', methods=['GET'])
@returns_json
def get_reservations():
    """Get a filtered reservation list.

    Optional query params: start, end
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

        reservations = Reservation.query.filter(
            Reservation.end >= start, Reservation.start <= end)
    else:
        reservations = Reservation.query.filter(
            or_(Reservation.start >= datetime.datetime.now(),
                Reservation.end >= datetime.datetime.now()))

    reservations = map(lambda x: x.as_dict(), reservations)

    return json.dumps(reservations)


if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == 'init':
        print 'init db...'
        init_db()

    import os
    if os.getenv('PRODUCTION') == 'TRUE':
        app.run(host='0.0.0.0')
    else:
        app.run()
