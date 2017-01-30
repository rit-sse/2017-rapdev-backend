"""Models."""

from sqlalchemy import Column, Integer, String, Table, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from database import Base
import jwt


secret = 'secret'


join_table_user_roles = Table(
    'user_roles', Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('role_id', Integer, ForeignKey('roles.id'))
)


join_table_user_teams = Table(
    'user_teams', Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('team_id', Integer, ForeignKey('teams.id'))
)


class User(Base):
    """Single user of the system."""

    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True)
    email = Column(String(120), unique=True)
    roles = relationship('Role',
                         secondary=join_table_user_roles,
                         back_populates="users")
    teams = relationship('Team',
                         secondary=join_table_user_teams,
                         back_populates="members")

    @staticmethod
    def verify_auth_token(token):
        """Get the user from a JWT token."""
        try:
            decoded = jwt.decode(token, secret, algorithms=['HS256'])
        except jwt.DecodeError:
            return None
        user = User.query.get(decoded['id'])
        return user

    def __init__(self, name=None, email=None):
        """Create a user."""
        self.name = name
        self.email = email

    def generate_auth_token(self):
        """Create a JWT token with the user ID."""
        return jwt.encode({'id': self.id}, secret, algorithm='HS256')

    def has_permission(self, permission_name):
        """Check that a user has the given permission."""
        for role in self.roles:
            for permission in role.permissions:
                if permission.name == permission_name:
                    return True
        return False

    def as_dict(self, include_teams_and_permissions=False, for_user=None):
        """
        Get the user as a dictionary.

        Optionally includes the user's teams and permissions.
        """
        if include_teams_and_permissions:
            all_permissions = []
            for role in self.roles:
                for permission in role.permissions:
                    if permission not in all_permissions:
                        all_permissions.append(permission.name)
            return {
                'id': self.id,
                'name': self.name,
                'email': self.email,
                'teams': map(lambda t: t.as_dict(for_user=for_user), self.teams),
                'permissions': all_permissions
            }
        else:
            return {
                'id': self.id,
                'name': self.name,
                'email': self.email
            }

join_table_role_permissions = Table(
    'role_permissions', Base.metadata,
    Column('role_id', Integer, ForeignKey('roles.id')),
    Column('permission_id', Integer, ForeignKey('permissions.id'))
)


class Role(Base):
    """
    Role for a user.

    Examples: Student
    """

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
        """Create a role."""
        self.name = name


class Permission(Base):
    """Permission for a role."""

    __tablename__ = 'permissions'
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True)
    roles = relationship('Role',
                         secondary=join_table_role_permissions,
                         back_populates='permissions')

    def __init__(self, name=None):
        """Create a permission."""
        self.name = name


class TeamType(Base):
    """Type of team."""

    __tablename__ = 'teamtypes'
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True)
    teams = relationship('Team', back_populates='team_type')
    priority = Column(Integer)
    # max days ahead that they can reserve a room
    advance_time = Column(Integer)

    def __init__(self, name=None, priority=None, advance_time=None):
        """Create a type of team."""
        self.name = name
        self.priority = priority
        self.advance_time = advance_time


class Team(Base):
    """Team of users."""

    __tablename__ = 'teams'
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True)
    team_type_id = Column(Integer, ForeignKey('teamtypes.id'))
    team_type = relationship("TeamType", back_populates="teams")
    members = relationship('User',
                           secondary=join_table_user_teams,
                           back_populates='teams')
    reservations = relationship('Reservation', back_populates='team')

    def __init__(self, name=None):
        """Create a team."""
        self.name = name

    def as_dict(self, for_user=None):
        """Convert to a dict, optionally including name and member details
        if the given user has the requisite permissions."""
        base = {
            "id": self.id,
            "type": self.team_type.name
        }
        if for_user and \
            (for_user.has_permission('team.read.elevated') or
                (for_user.has_permission('team.read')
                    and self.has_member(for_user))):
            base["name"] = self.name
            base["advance_time"] = self.team_type.advance_time
            members = []
            for member in self.members:
                members.append({
                    "id": member.id,
                    "name": member.name
                })
            base["members"] = members
        return base

    def has_member(self, user):
        """Check if the given user is a member of the team."""
        return any(map(lambda u: u.id == user.id, self.members))


join_table_room_roomfeatures = Table(
    'room_roomfeatures', Base.metadata,
    Column('room_id', Integer, ForeignKey('rooms.id')),
    Column('roomfeature_id', Integer, ForeignKey('roomfeatures.id'))
)


class Room(Base):
    """Room."""

    __tablename__ = 'rooms'
    id = Column(Integer, primary_key=True)
    number = Column(String(50), unique=True)
    features = relationship('RoomFeature',
                            secondary=join_table_room_roomfeatures,
                            back_populates='rooms')
    reservations = relationship('Reservation', back_populates='room')

    def __init__(self, number=None):
        """Create a room."""
        self.number = number

    def as_dict(self, include_features=False):
        """
        Get the room as a dictionary.

        Optionally include the features of the room.
        """
        if include_features:
            feature_list = []
            for feature in self.features:
                feature_list.append(feature.as_dict())

            return {
                'id': self.id,
                'number': self.number,
                'features': feature_list,
            }
        else:
            return {
                'id': self.id,
                'number': self.number
            }


class RoomFeature(Base):
    """Features of a room."""

    __tablename__ = 'roomfeatures'
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True)
    rooms = relationship('Room',
                         secondary=join_table_room_roomfeatures,
                         back_populates='features')

    def __init__(self, name=None):
        """Create a feature for a room."""
        self.name = name

    def as_dict(self):
        return {
            'id': self.id,
            'name': self.name
        }


class Reservation(Base):
    """Reservation for a room and team."""

    __tablename__ = 'reservations'
    id = Column(Integer, primary_key=True)
    team_id = Column(Integer, ForeignKey('teams.id'))
    team = relationship('Team', back_populates='reservations')
    room_id = Column(Integer, ForeignKey('rooms.id'))
    room = relationship('Room', back_populates='reservations')
    created_by_id = Column(Integer, ForeignKey('users.id'))
    created_by = relationship('User')
    start = Column(DateTime)
    end = Column(DateTime)

    # Return values for validate_conflicts()
    NO_CONFLICT = 0
    CONFLICT_OVERRIDABLE = 1
    CONFLICT_FAILURE = 2

    def __init__(self, start=None, end=None, team=None,
                 room=None, created_by=None):
        """Create a reservation."""
        self.start = start
        self.end = end
        self.team = team
        self.room = room
        self.created_by = created_by

    def as_dict(self, for_user=None):
        """Get the reservation as a dictionary."""
        return {
            'id': self.id,
            'team': self.team.as_dict(for_user=for_user),
            'room': self.room.as_dict(include_features=False),
            'start': self.start.isoformat(),
            'end': self.end.isoformat()
        }

    def validate_conflicts(self):
        conflicting_reservations = Reservation.query.filter(
            Reservation.end >= self.start,
            Reservation.start <= self.end,
            Reservation.room_id == self.room.id,
            Reservation.id != self.id
        ).all()

        if len(conflicting_reservations) > 0:
            can_override = True
            for conflict in conflicting_reservations:
                if conflict.team.team_type.priority <= self.team.team_type.priority:
                    can_override = False
                    break
            if can_override:
                return Reservation.CONFLICT_OVERRIDABLE, conflicting_reservations
            else:
                return Reservation.CONFLICT_FAILURE, conflicting_reservations
        else:
            return Reservation.NO_CONFLICT, conflicting_reservations
