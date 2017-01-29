"""Unit tests."""

import os
import database
import unittest
import tempfile
import json

import main
from models import User, Team


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
        self.assertEquals(num_users, 1)

    def test_auth_makes_user(self):
        """Test that auth will create a new user."""
        num_users = len(User.query.all())
        self.assertEquals(num_users, 0)
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
        self.assertEquals(num_users, 1)

    def test_user_not_found(self):
        """Test that get user returns a 404 for unknown users."""
        num_users = len(User.query.all())
        self.assertEquals(num_users, 0)
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
        rv = self.app.post(
            '/v1/team',
            data='{"name": "newteam1"}',
            content_type='application/json'
        )
        self.assertEquals(rv.status_code, 201)
        t = Team.query.first()
        self.assertEquals(t.name, 'newteam1')

if __name__ == '__main__':
    unittest.main()
