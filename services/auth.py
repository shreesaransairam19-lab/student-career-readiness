"""
Authentication service for Student Career Readiness System.
Handles user registration, login, password hashing, and profile management.
"""

import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash


class AuthService:
    def __init__(self, db_path):
        self.db_path = db_path
    
    def _get_conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        conn.row_factory = sqlite3.Row
        return conn
    
    def register(self, email, password, name):
        """Register a new user. Returns user_id on success."""
        conn = self._get_conn()
        try:
            # Check if email already exists
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM students WHERE email = ?", (email,))
            if cursor.fetchone():
                raise ValueError("Email already registered.")
            
            password_hash = generate_password_hash(password)
            cursor.execute(
                "INSERT INTO students (name, email, password_hash) VALUES (?, ?, ?)",
                (name, email, password_hash)
            )
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()
    
    def login(self, email, password):
        """Authenticate user. Returns user dict on success, None on failure."""
        conn = self._get_conn()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM students WHERE email = ?", (email,))
            user = cursor.fetchone()
            
            if user and check_password_hash(user['password_hash'], password):
                return dict(user)
            return None
        finally:
            conn.close()
    
    def get_user_by_id(self, user_id):
        """Get user by ID. Returns dict or None."""
        conn = self._get_conn()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM students WHERE id = ?", (user_id,))
            user = cursor.fetchone()
            return dict(user) if user else None
        finally:
            conn.close()
    
    def update_profile(self, user_id, name, department, study_year, career_goal):
        """Update user profile."""
        conn = self._get_conn()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """UPDATE students 
                   SET name = ?, department = ?, study_year = ?, career_goal = ?
                   WHERE id = ?""",
                (name, department, study_year, career_goal, user_id)
            )
            conn.commit()
        finally:
            conn.close()
    
    def get_all_roles(self):
        """Get all available roles."""
        conn = self._get_conn()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM roles ORDER BY name")
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()
    
    def get_role_by_name(self, name):
        """Get role by name."""
        conn = self._get_conn()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM roles WHERE name = ?", (name,))
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()
    
    def get_role_by_id(self, role_id):
        """Get role by ID."""
        conn = self._get_conn()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM roles WHERE id = ?", (role_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()
    
    def add_project(self, student_id, title, description, technologies, project_url):
        """Add a project for a student."""
        conn = self._get_conn()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO projects (student_id, title, description, technologies, project_url)
                   VALUES (?, ?, ?, ?, ?)""",
                (student_id, title, description, technologies, project_url)
            )
            conn.commit()
        finally:
            conn.close()
    
    def get_user_projects(self, student_id):
        """Get all projects for a student."""
        conn = self._get_conn()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM projects WHERE student_id = ? ORDER BY created_at DESC",
                (student_id,)
            )
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()