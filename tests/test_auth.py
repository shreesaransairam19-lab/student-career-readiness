"""Auth service tests."""

import os
import sqlite3
import tempfile

import pytest

from services.auth import AuthService

SCHEMA = os.path.join(os.path.dirname(__file__), '..', 'database', 'schema.sql')


@pytest.fixture
def db_path():
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    conn = sqlite3.connect(path)
    with open(SCHEMA) as f:
        conn.executescript(f.read())
    conn.execute("INSERT INTO roles (name, description) VALUES ('Python Developer', 'Backend')")
    conn.execute("INSERT INTO skills (name, category) VALUES ('Python', 'Programming')")
    conn.commit()
    conn.close()
    yield path
    os.unlink(path)


@pytest.fixture
def auth(db_path):
    return AuthService(db_path)


def test_register_returns_id_and_hashes_password(auth, db_path):
    user_id = auth.register('a@example.com', 'secret123', 'Alice')
    assert user_id > 0
    conn = sqlite3.connect(db_path)
    row = conn.execute("SELECT password_hash FROM students WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    assert row[0] != 'secret123'
    assert row[0].startswith('scrypt:') or row[0].startswith('pbkdf2:')


def test_register_duplicate_email_rejected(auth):
    auth.register('a@example.com', 'secret123', 'Alice')
    with pytest.raises(ValueError, match='already registered'):
        auth.register('a@example.com', 'other', 'Other')


def test_login_success_and_failure(auth):
    auth.register('a@example.com', 'secret123', 'Alice')
    assert auth.login('a@example.com', 'secret123')['email'] == 'a@example.com'
    assert auth.login('a@example.com', 'wrong') is None
    assert auth.login('missing@example.com', 'secret123') is None


def test_get_user_by_id_and_update_profile(auth):
    uid = auth.register('a@example.com', 'secret123', 'Alice')
    auth.update_profile(uid, 'Alice B', 'CS', 2, 'Python Developer')
    user = auth.get_user_by_id(uid)
    assert user['name'] == 'Alice B'
    assert user['department'] == 'CS'
    assert user['study_year'] == 2
    assert user['career_goal'] == 'Python Developer'
    assert auth.get_user_by_id(9999) is None


def test_roles_lookup(auth):
    roles = auth.get_all_roles()
    assert len(roles) == 1
    assert roles[0]['name'] == 'Python Developer'
    assert auth.get_role_by_name('Python Developer')['description'] == 'Backend'
    assert auth.get_role_by_name('Nope') is None
    assert auth.get_role_by_id(roles[0]['id'])['name'] == 'Python Developer'


def test_projects_scoped_to_student(auth):
    u1 = auth.register('a@example.com', 'secret123', 'Alice')
    u2 = auth.register('b@example.com', 'secret123', 'Bob')
    auth.add_project(u1, 'Project A', 'desc', 'Python', '')
    auth.add_project(u2, 'Project B', 'desc', 'SQL', '')

    p1 = auth.get_user_projects(u1)
    p2 = auth.get_user_projects(u2)
    assert [p['title'] for p in p1] == ['Project A']
    assert [p['title'] for p in p2] == ['Project B']