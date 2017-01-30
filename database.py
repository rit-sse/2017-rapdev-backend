"""Database methods."""

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import datetime
import os


def init_engine():
    """Return a initilized engine based on the running environment."""
    if os.getenv('PRODUCTION', False):
        USER = os.getenv('PG_ENV_POSTGRES_USER', 'postgres')
        DB = os.getenv('PG_ENV_POSTGRES_DB', USER)
        PASS = os.getenv('PG_ENV_POSTGRES_PASSWORD')
        return create_engine(
            'postgres://' + USER + ':' + PASS + '@pg:5432/' + DB)
    else:
        return create_engine('sqlite:///test.db', convert_unicode=True)

engine = init_engine()
_db_session = scoped_session(sessionmaker(autocommit=False,
                                          autoflush=False,
                                          bind=engine))
Base = declarative_base()
Base.query = _db_session.query_property()


def get_db():
    """Return the current DB session."""
    return _db_session


def set_engine(new_querystring):
    """Swap the current sqlite database location to the new destination.

    FOR TESTING ONLY!
    """
    global engine, _db_session
    engine = create_engine(new_querystring, convert_unicode=True)
    _db_session = scoped_session(
        sessionmaker(autocommit=False, autoflush=False, bind=engine)
    )
    Base.query = _db_session.query_property()


def init_db():
    """Initialize the database."""
    # import all modules here that might define models so that
    # they will be registered properly on the metadata.  Otherwise
    # you will have to import them first before calling init_db()
    import models
    Base.metadata.create_all(bind=engine)
    seed()


def seed():
    """Seed the database with sample data."""
    import models
    # the rooms

    room_features = ['Projector', 'TV', 'Webcam', 'Phone Line']

    rooms = {
               '1560': ['Projector'],
               '1561': ['TV', 'Webcam'],
               '1562': ['Projector'],
               '1563': ['TV'],
               '1564': ['Projector'],
               '1565': ['TV', 'Webcam'],
               '1665': ['TV', 'Webcam'],
               '1663': ['TV'],
               '1662': ['Projector'],
               '1661': ['Projector'],
               '1660': ['Projector']
            }

    feature_dict = {}
    for feature in room_features:
        f = models.RoomFeature(name=feature)
        get_db().add(f)
        feature_dict[feature] = f

    rooms_dict = {}
    for room_number in rooms:
        r = models.Room(number=room_number)
        for feature in rooms[room_number]:
            f = feature_dict[feature]
            r.features.append(f)
        rooms_dict[room_number] = r
        get_db().add(r)

    # the types of team
    teamtype_dict = {}
    teamtype_dict['single'] = models.TeamType(
        name='single',
        priority=4,
        advance_time=7 * 2  # 2 weeks
    )
    get_db().add(teamtype_dict['single'])
    get_db().add(
        models.TeamType(
            name='other_team',
            priority=4,
            advance_time=7 * 2  # 2 weeks
        )
    )
    get_db().add(
        models.TeamType(
            name='class',
            priority=3,
            advance_time=7 * 2  # 2 weeks
        )
    )
    get_db().add(
        models.TeamType(
            name='colab_class',
            priority=2,
            advance_time=7 * 2  # 2 weeks
        )
    )
    get_db().add(
        models.TeamType(
            name='senior_project',
            priority=1,
            advance_time=7 * 2  # 2 weeks
        )
    )

    # the permissions

    perm_names = [
        'team.create',
        'team.create.elevated',
        'team.delete',
        'team.delete.elevated',
        'team.read',
        'team.read.elevated',
        'team.update',
        'team.update.elevated',
        'reservation.create',
        'reservation.delete',
        'reservation.delete.elevated',
        'reservation.read',
        'reservation.update',
        'reservation.update.elevated',
        'room.update.elevated',
        'room.create.elevated',
        'room.read',
        'room.delete.elevated',
        'feature.create',
        'feature.delete',
        'feature.update',
        'feature.read',
        'role.create',
        'role.delete',
        'role.update'
    ]
    perm_dict = {}
    for perm in perm_names:
        p = models.Permission(name=perm)
        get_db().add(p)
        perm_dict[perm] = p

    roles = {
        'student': [
            'team.create',
            'team.delete',
            'team.read',
            'team.update',
            'reservation.create',
            'reservation.delete',
            'reservation.read',
            'reservation.update',
            'room.read',
            'feature.read'
        ],
        'labbie': [
            'team.create',
            'team.delete',
            'team.read',
            'team.update',
            'reservation.create',
            'reservation.delete',
            'reservation.read',
            'reservation.update',
            'room.read',
            'feature.read',
            'team.read.elevated'
        ],
        'professor': [
            'team.create',
            'team.delete',
            'team.read',
            'team.update',
            'reservation.create',
            'reservation.delete',
            'reservation.read',
            'reservation.update',
            'room.read',
            'feature.read',
            'team.create.elevated',
            'team.read.elevated'
        ],
        'admin': [
            'team.create',
            'team.create.elevated',
            'team.delete',
            'team.delete.elevated',
            'team.read',
            'team.read.elevated',
            'team.update',
            'team.update.elevated',
            'reservation.create',
            'reservation.delete',
            'reservation.delete.elevated',
            'reservation.read',
            'reservation.update',
            'reservation.update.elevated',
            'room.update.elevated',
            'room.create.elevated',
            'room.read',
            'room.delete.elevated',
            'feature.create',
            'feature.delete',
            'feature.update',
            'feature.read',
            'role.create',
            'role.delete',
            'role.update'
        ]
    }
    users_dict = {}
    for role in roles:
        r = models.Role(name=role)
        for permission in roles[role]:
            p = perm_dict[permission]
            r.permissions.append(p)
        get_db().add(r)
        # seed a user TODO don't do this in production?
        u = models.User(name=role, email=role + "@example.com")
        u.roles.append(r)
        team = models.Team(u.name)
        team_type = teamtype_dict['single']
        team.team_type = team_type
        team.members.append(u)
        u.teams.append(team)
        users_dict[role] = u
        get_db().add(team)
        get_db().add(u)

    reservation = models.Reservation(
        start=datetime.datetime.now() + datetime.timedelta(days=7),
        end=datetime.datetime.now() + datetime.timedelta(days=7, hours=1),
        team=users_dict['admin'].teams[0],
        room=rooms_dict['1660'],
        created_by=users_dict['admin']
    )
    get_db().add(reservation)

    get_db().commit()
