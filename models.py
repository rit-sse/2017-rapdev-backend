from sqlalchemy import Column, Integer, String, Table, ForeignKey
from sqlalchemy.orm import relationship
from database import Base


join_table_user_roles = Table('user_roles', Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('role_id', Integer, ForeignKey('roles.id'))
)

join_table_user_teams = Table('user_teams', Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('team_id', Integer, ForeignKey('teams.id'))
)


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True)
    email = Column(String(120), unique=True)
    roles = relationship('Role',
                         secondary=join_table_user_roles,
                         back_populates="users")
    teams = relationship('Team',
                         secondary=join_table_user_teams,
                         back_populates="users")

    def __init__(self, name=None, email=None):
        self.name = name
        self.email = email

    def as_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email
        }

join_table_role_permissions = Table('role_permissions', Base.metadata,
    Column('role_id', Integer, ForeignKey('roles.id')),
    Column('permission_id', Integer, ForeignKey('permissions.id'))
)


class Role(Base):
    __tablename__ = 'roles'
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True)
    users = relationship('User',
                         secondary=join_table_user_roles,
                         back_populates='roles')
    permissions = relationship('Permission',
                         secondary=join_table_role_permissions,
                         back_populates='roles')

    def __init__(self, name=None):
        self.name = name


class Permission(Base):
    __tablename__ = 'permissions'
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True)
    roles = relationship('Role',
                         secondary=join_table_role_permissions,
                         back_populates='permissions')

    def __init__(self, name=None):
        self.name = name


class TeamType(Base):
    __tablename__ = 'teamtypes'
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True)
    teams = relationship("Team", back_populates="teamtype")
    priority = Column(Integer)
    advance_time = Column(Integer) # max days ahead that they can reserve a room

    def __init__(self, name=None):
        self.name = name


class Team(Base):
    __tablename__ = 'teams'
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True)
    teamtype_id = Column(Integer, ForeignKey('teamtypes.id'))
    teamtype = relationship("TeamType", back_populates="teams")
    users = relationship('User',
                         secondary=join_table_user_teams,
                         back_populates='teams')

    def __init__(self, name=None):
        self.name = name


join_table_room_roomfeatures = Table('room_roomfeatures', Base.metadata,
    Column('room_id', Integer, ForeignKey('rooms.id')),
    Column('roomfeature_id', Integer, ForeignKey('roomfeatures.id'))
)


class Room(Base):
    __tablename__ = 'rooms'
    id = Column(Integer, primary_key=True)
    number = Column(String(50), unique=True)
    features = relationship('RoomFeature',
                            secondary=join_table_room_roomfeatures,
                            back_populates='rooms')

    def __init__(self, number=None):
        self.number = number


class RoomFeature(Base):
    __tablename__ = 'roomfeatures'
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True)
    rooms = relationship('Room',
                         secondary=join_table_room_roomfeatures,
                         back_populates='features')

    def __init__(self, name=None):
        self.name = name
