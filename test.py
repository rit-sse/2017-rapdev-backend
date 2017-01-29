"""Unit tests."""

import os
import database
import unittest
import tempfile
import json

import main
from models import User, Team, TeamType


class TestCase(unittest.TestCase):
    """Unit tests for APIs."""

    def setUp(self):
        """Set up for the tests."""
        self.db_fd, self.db_name = tempfile.mkstemp()
        database.set_engine('sqlite:///' + self.db_name)
        database.init_db()
        self.app = main.app.test_client()

    def tearDown(self):
        """Cleanup from the tests."""
        database.get_db().close()
        os.close(self.db_fd)
        os.unlink(self.db_name)

    def test_auth(self):
        """Test the authentication process."""
        num_users_start = len(User.query.all())
        u = User(name="anthony", email="foo@bar.com")
        database.get_db().add(u)
        database.get_db().commit()
        assert u.id is not None
        rv = self.app.post(
            '/v1/auth',
            data='{"username":"anthony"}',
            content_type='application/json'
        )
        self.assertEquals(rv.status_code, 200)
        got = json.loads(rv.data)
        self.assertTrue('token' in got)
        self.assertTrue(len(got['token']) > 0)
        num_users = len(User.query.all())
        self.assertEquals(num_users - num_users_start, 1)

    def test_auth_makes_user(self):
        """Test that auth will create a new user."""
        num_users_start = len(User.query.all())
        rv = self.app.post(
            '/v1/auth',
            data='{"username":"bob"}',
            content_type='application/json'
        )
        self.assertEquals(rv.status_code, 200)
        got = json.loads(rv.data)
        self.assertTrue('token' in got)
        self.assertTrue(len(got['token']) > 0)
        num_users = len(User.query.all())
        self.assertEquals(num_users - num_users_start, 1)

    def test_user_not_found(self):
        """Test that get user returns a 404 for unknown users."""
        self.assertIsNone(User.query.get(100))
        rv = self.app.get(
            '/v1/user/100',
            content_type='application/json'
        )
        self.assertEquals(rv.status_code, 404)

    def test_user_found(self):
        """Test that the user is returned."""
        u = User(name='Catherine', email='cat@example.com')
        database.get_db().add(u)
        database.get_db().commit()
        rv = self.app.get(
            '/v1/user/' + str(u.id),
            content_type='application/json'
        )
        self.assertEquals(rv.status_code, 200)
        got = json.loads(rv.data)
        self.assertEquals(got["id"], u.id)
        self.assertEquals(got["name"], u.name)
        self.assertEquals(got["email"], u.email)
        self.assertEquals(len(got["teams"]), 0)
        self.assertEquals(len(got["permissions"]), 0)
        # TODO add test for presence of teams and permissions

    def test_add_team(self):
        """Test that teams can be added."""
        team_count_original = len(Team.query.all())
        u = User.query.filter_by(name='student').first()
        rv = self.app.post(
            '/v1/team',
            data='{"name": "newteam1", "type": "other_team"}',
            content_type='application/json',
            headers = {"Authorization": "Bearer " + u.generate_auth_token()}
        )
        self.assertEquals(rv.status_code, 201)
        t = Team.query.first()
        self.assertEquals(t.name, 'newteam1')
        team_count = len(Team.query.all())
        self.assertEquals(team_count - team_count_original, 1)

    def test_add_team_no_permission(self):
        team_count_original = len(Team.query.all())
        u = User.query.filter_by(name='student').first()
        rv = self.app.post(
            '/v1/team',
            data='{"name": "newteam1", "type": "class"}',
            content_type='application/json',
            headers = {"Authorization": "Bearer " + u.generate_auth_token()}
        )
        self.assertEquals(rv.status_code, 403)
        team_count = len(Team.query.all())
        self.assertEquals(team_count, team_count_original)

    def test_get_team_user_is_on(self):
        """Test that a user can query their own team."""
        u = User.query.filter_by(name='student').first()
        team_type = TeamType.query.filter_by(name='single').first()
        team = Team(name="testteam1")
        team.members.append(u)
        team.team_type = team_type
        database.get_db().add(team)
        database.get_db().commit()
        rv = self.app.get(
            '/v1/team/' + str(team.id),
            content_type='application/json',
            headers = {"Authorization": "Bearer " + u.generate_auth_token()}
        )
        self.assertEquals(rv.status_code, 200)
        got = json.loads(rv.data)
        self.assertEquals(got["id"], team.id)
        self.assertEquals(got["name"], team.name)
        self.assertEquals(got["type"], team.team_type.name)
        self.assertEquals(len(got["members"]), 1)
        self.assertEquals(got["members"][0]["id"], u.id)
        self.assertEquals(got["members"][0]["name"], u.name)

    def test_get_team_user_is_not_on(self):
        """Test that a non-elevated user can not query extended details of
        other teams."""
        student = User.query.filter_by(name='student').first()
        professor = User.query.filter_by(name='professor').first()
        team_type = TeamType.query.filter_by(name='single').first()
        team = Team(name="testteam1")
        team.team_type = team_type
        team.members.append(professor)
        database.get_db().add(team)
        database.get_db().commit()
        rv = self.app.get(
            '/v1/team/' + str(team.id),
            content_type='application/json',
            headers = {
                "Authorization": "Bearer " + student.generate_auth_token()
            }
        )
        self.assertEquals(rv.status_code, 200)
        got = json.loads(rv.data)
        self.assertEquals(got["id"], team.id)
        self.assertEquals(got["type"], team.team_type.name)
        self.assertTrue("name" not in got)
        self.assertTrue("members" not in got)

    def test_student_has_permission(self):
        u = User.query.filter_by(name='student').first()
        self.assertTrue(u.has_permission('room.read'))
        self.assertFalse(u.has_permission('team.create.elevated'))

    def test_failure_of_token_verify(self):
        u = User.verify_auth_token("asdfasdfsadfsadfsadfa")
        self.assertIsNone(u)

    def test_token_verify_deleted_user(self):
        self.assertIsNone(User.query.get(100))
        u = User(name="foo")
        u.id = 100
        token = u.generate_auth_token()
        got = User.verify_auth_token(token)
        self.assertIsNone(got)

if __name__ == '__main__':
    unittest.main()
