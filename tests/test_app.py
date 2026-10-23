"""Integration tests for Flask routes, validation, and access control."""

import importlib
import os
import sqlite3

import pytest

SCHEMA = os.path.join(os.path.dirname(__file__), '..', 'database', 'schema.sql')


def _make_db(path):
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA foreign_keys = ON")
    with open(SCHEMA) as f:
        conn.executescript(f.read())

    conn.execute("INSERT INTO roles (name, description) VALUES ('Python Developer', 'Backend')")
    conn.execute("INSERT INTO roles (name, description) VALUES ('Web Developer', 'Frontend')")
    skills = [
        ('Python', 'Programming', 'Core Python'),
        ('SQL', 'Programming', 'Queries'),
        ('Git', 'Programming', 'Version control'),
        ('Communication', 'Soft Skills', 'Talking'),
    ]
    for name, cat, desc in skills:
        conn.execute("INSERT INTO skills (name, category, description) VALUES (?, ?, ?)", (name, cat, desc))

    targets = [(1, 1, 5), (1, 2, 4), (1, 3, 4), (1, 4, 4)]
    for role_id, skill_id, target in targets:
        conn.execute(
            "INSERT INTO role_skill_targets (role_id, skill_id, target_rating) VALUES (?, ?, ?)",
            (role_id, skill_id, target),
        )

    conn.commit()
    conn.close()


@pytest.fixture
def client(tmp_path, monkeypatch):
    db_path = str(tmp_path / 'test.db')
    _make_db(db_path)
    monkeypatch.setenv('DATABASE_PATH', db_path)

    import app as app_module
    importlib.reload(app_module)
    app_module.app.config.update(TESTING=True, SECRET_KEY='test')

    with app_module.app.test_client() as c:
        c.db_path = db_path
        yield c


def _skill_id(client, name='Python'):
    conn = sqlite3.connect(client.db_path)
    row = conn.execute("SELECT id FROM skills WHERE name = ?", (name,)).fetchone()
    conn.close()
    return row[0]


def _register_and_profile(client, email='a@example.com', name='Alice', role='Python Developer'):
    r = client.post('/register', data={'name': name, 'email': email, 'password': 'secret123'})
    assert r.status_code == 302
    r = client.post('/profile', data={
        'name': name, 'department': 'CS', 'study_year': '2', 'career_goal': role
    })
    assert r.status_code == 302


def _submit(client, ratings):
    data = {}
    for name, value in ratings.items():
        data[f'skill_{_skill_id(client, name)}'] = str(value)
    return client.post('/assessment/submit', data=data)


def test_unauthenticated_redirects_to_login(client):
    r = client.get('/dashboard')
    assert r.status_code == 302
    assert '/login' in r.headers['Location']


def test_register_login_flow(client):
    r = client.post('/register', data={'name': 'Alice', 'email': 'a@example.com', 'password': 'secret123'})
    assert r.status_code == 302 and '/profile' in r.headers['Location']

    client.get('/logout')
    r = client.post('/login', data={'email': 'a@example.com', 'password': 'secret123'})
    assert r.status_code == 302 and '/profile' in r.headers['Location']

    r = client.post('/login', data={'email': 'a@example.com', 'password': 'nope'})
    assert b'Invalid email or password' in r.data


def test_profile_requires_role_for_assessment(client):
    _register_and_profile(client)
    r = client.get('/assessment')
    assert r.status_code == 200
    assert b'Python' in r.data
    assert b'Not assessed' in r.data or b'N/A' in r.data


def test_valid_assessment_saves_and_dashboard_renders(client):
    _register_and_profile(client)
    r = _submit(client, {'Python': 3, 'SQL': 2})
    assert r.status_code == 302 and '/dashboard' in r.headers['Location']

    r = client.get('/dashboard')
    assert r.status_code == 200
    assert b'Skill gaps' in r.data
    assert b'Below target' in r.data
    assert b'Recommended next actions' in r.data
    assert b'Python' in r.data


def test_rating_six_rejected(client):
    _register_and_profile(client)
    r = _submit(client, {'Python': 6})
    assert r.status_code == 302
    r = client.get('/assessment')
    assert b'must be between 1 and 5' in r.data


def test_rating_zero_rejected(client):
    _register_and_profile(client)
    r = _submit(client, {'Python': 0})
    assert r.status_code == 302
    r = client.get('/assessment')
    assert b'must be between 1 and 5' in r.data


def test_non_numeric_rating_rejected(client):
    _register_and_profile(client)
    r = client.post('/assessment/submit', data={f'skill_{_skill_id(client)}': 'abc'})
    assert r.status_code == 302
    r = client.get('/assessment')
    assert b'Invalid rating' in r.data


def test_empty_assessment_rejected(client):
    _register_and_profile(client)
    r = client.post('/assessment/submit', data={})
    assert r.status_code == 302
    r = client.get('/assessment')
    assert b'rate at least one skill' in r.data


def test_unrated_skill_excluded_from_average(client):
    _register_and_profile(client)
    _submit(client, {'Python': 2, 'SQL': 4})
    r = client.get('/dashboard')
    assert r.status_code == 200
    # Programming average of 2 and 4 is 3 -> readiness 60%
    assert b'60.0%' in r.data


def test_dashboard_with_ratings_absent_shows_friendly_message(client):
    _register_and_profile(client)
    # Create an assessment with no scores directly (bypasses form guard)
    conn = sqlite3.connect(client.db_path)
    cur = conn.execute("INSERT INTO assessments (student_id, role_id) VALUES (1, 1)")
    conn.commit()
    conn.close()
    assert cur.lastrowid

    r = client.get('/dashboard')
    assert r.status_code == 200
    assert b'no averages to show' in r.data
    assert b'Complete assessment' in r.data


def test_project_added_appears_only_for_owner(client):
    _register_and_profile(client, email='a@example.com', name='Alice')
    r = client.post('/projects', data={
        'title': 'Alice Project', 'description': 'd', 'technologies': 'Python, SQL', 'project_url': ''
    })
    assert r.status_code == 302
    r = client.get('/projects')
    assert b'Alice Project' in r.data

    client.get('/logout')
    _register_and_profile(client, email='b@example.com', name='Bob')
    r = client.get('/projects')
    assert b'Alice Project' not in r.data


def test_history_lists_and_opens_assessment(client):
    _register_and_profile(client)
    _submit(client, {'Python': 3})

    r = client.get('/history')
    assert r.status_code == 200

    conn = sqlite3.connect(client.db_path)
    aid = conn.execute("SELECT id FROM assessments ORDER BY id DESC LIMIT 1").fetchone()[0]
    conn.close()

    r = client.get(f'/history/{aid}')
    assert r.status_code == 200
    assert b'historical view' in r.data


def test_cannot_read_another_students_assessment(client):
    _register_and_profile(client, email='a@example.com', name='Alice')
    _submit(client, {'Python': 3})
    conn = sqlite3.connect(client.db_path)
    aid = conn.execute("SELECT id FROM assessments ORDER BY id DESC LIMIT 1").fetchone()[0]
    conn.close()

    client.get('/logout')
    _register_and_profile(client, email='b@example.com', name='Bob')

    r = client.get(f'/history/{aid}')
    assert r.status_code == 302
    assert '/history' in r.headers['Location']

    r = client.get('/history')
    assert f'Assessment #{aid}'.encode() not in r.data


def test_cannot_read_another_students_dashboard_data(client):
    _register_and_profile(client, email='a@example.com', name='Alice')
    _submit(client, {'Python': 1})

    client.get('/logout')
    _register_and_profile(client, email='b@example.com', name='Bob')

    # Bob has no assessment yet -> redirected to assessment, never sees Alice's data
    r = client.get('/dashboard')
    assert r.status_code == 302
    assert '/assessment' in r.headers['Location']

def test_dashboard_reflects_project_evidence_and_recommendation(client):
    """Adding projects must visibly update the evidence count and clear the portfolio rule."""
    _register_and_profile(client)
    _submit(client, {'Python': 5, 'SQL': 5, 'Git': 5, 'Communication': 5})

    r = client.get('/dashboard')
    assert b'projects logged as evidence' in r.data
    assert b'Build one complete project' in r.data

    client.post('/projects', data={
        'title': 'Project One', 'description': '', 'technologies': '', 'project_url': ''
    })
    r = client.get('/dashboard')
    assert b'project logged as evidence' in r.data
    assert b'Build one complete project' in r.data

    client.post('/projects', data={
        'title': 'Project Two', 'description': '', 'technologies': '', 'project_url': ''
    })
    r = client.get('/dashboard')
    assert b'projects logged as evidence' in r.data
    assert b'Build one complete project' not in r.data


def test_stale_session_redirects_to_login(client):
    """A session pointing at a deleted user must not render the profile page."""
    with client.session_transaction() as sess:
        sess['user_id'] = 999

    r = client.get('/profile')
    assert r.status_code == 302
    assert '/login' in r.headers['Location']

    with client.session_transaction() as sess:
        assert 'user_id' not in sess
