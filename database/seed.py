#!/usr/bin/env python3
"""
Seed script for Student Career Readiness System.
Populates roles, skills, and role-skill targets.
Run with: python database/seed.py
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'career_readiness.db')
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), 'schema.sql')

# Skills data: (name, category, description)
SKILLS = [
    # Programming
    ("Python", "Programming", "Core Python language proficiency"),
    ("JavaScript", "Programming", "JavaScript/TypeScript proficiency"),
    ("SQL", "Programming", "Structured Query Language for databases"),
    ("Git", "Programming", "Version control with Git"),
    ("Testing", "Programming", "Unit, integration, and E2E testing"),
    
    # Web Development
    ("HTML/CSS", "Web Development", "Semantic HTML and modern CSS"),
    ("React", "Web Development", "React.js component development"),
    ("Node.js", "Web Development", "Backend development with Node.js"),
    ("REST APIs", "Web Development", "Designing and consuming RESTful APIs"),
    ("Authentication", "Web Development", "Auth patterns: JWT, OAuth, sessions"),
    
    # Data Analysis
    ("Pandas", "Data Analysis", "Data manipulation with pandas"),
    ("NumPy", "Data Analysis", "Numerical computing with NumPy"),
    ("Data Visualization", "Data Analysis", "Matplotlib, Seaborn, Plotly"),
    ("Statistics", "Data Analysis", "Descriptive and inferential statistics"),
    ("Machine Learning Basics", "Data Analysis", "Scikit-learn fundamentals"),
    
    # Soft Skills
    ("Communication", "Soft Skills", "Written and verbal communication"),
    ("Problem Solving", "Soft Skills", "Analytical and creative problem solving"),
    ("Teamwork", "Soft Skills", "Collaboration and team dynamics"),
    ("Time Management", "Soft Skills", "Prioritization and deadline management"),
    ("Interview Prep", "Soft Skills", "Technical and behavioral interview preparation"),
]

# Roles data: (name, description)
ROLES = [
    ("Python Developer", "Backend development with Python, APIs, databases, and testing"),
    ("Web Developer", "Full-stack web development with React, Node.js, and modern tooling"),
    ("Data Analyst", "Data analysis, visualization, and statistical modeling with Python"),
]

# Role-skill targets: role_name -> {skill_name: target_rating}
ROLE_SKILL_TARGETS = {
    "Python Developer": {
        "Python": 5,
        "SQL": 4,
        "Git": 4,
        "Testing": 4,
        "REST APIs": 4,
        "JavaScript": 2,
        "HTML/CSS": 2,
        "React": 2,
        "Node.js": 2,
        "Authentication": 3,
        "Pandas": 3,
        "NumPy": 3,
        "Data Visualization": 2,
        "Statistics": 3,
        "Machine Learning Basics": 2,
        "Communication": 4,
        "Problem Solving": 5,
        "Teamwork": 4,
        "Time Management": 4,
        "Interview Prep": 3,
    },
    "Web Developer": {
        "JavaScript": 5,
        "HTML/CSS": 5,
        "React": 5,
        "Node.js": 4,
        "REST APIs": 4,
        "Authentication": 4,
        "Git": 4,
        "Testing": 3,
        "Python": 2,
        "SQL": 3,
        "Pandas": 2,
        "NumPy": 2,
        "Data Visualization": 3,
        "Statistics": 2,
        "Machine Learning Basics": 1,
        "Communication": 4,
        "Problem Solving": 5,
        "Teamwork": 4,
        "Time Management": 4,
        "Interview Prep": 3,
    },
    "Data Analyst": {
        "Python": 4,
        "SQL": 5,
        "Pandas": 5,
        "NumPy": 4,
        "Data Visualization": 5,
        "Statistics": 5,
        "Machine Learning Basics": 4,
        "Git": 3,
        "Testing": 3,
        "JavaScript": 2,
        "HTML/CSS": 2,
        "React": 1,
        "Node.js": 1,
        "REST APIs": 2,
        "Authentication": 2,
        "Communication": 4,
        "Problem Solving": 5,
        "Teamwork": 4,
        "Time Management": 4,
        "Interview Prep": 3,
    },
}


def get_db_connection():
    """Get database connection with foreign keys enabled."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn


def init_database():
    """Initialize database from schema."""
    with open(SCHEMA_PATH, 'r') as f:
        schema = f.read()
    
    conn = get_db_connection()
    conn.executescript(schema)
    conn.commit()
    conn.close()
    print("Database schema created.")


def seed_skills(conn):
    """Seed skills table."""
    cursor = conn.cursor()
    for name, category, description in SKILLS:
        cursor.execute(
            "INSERT OR IGNORE INTO skills (name, category, description) VALUES (?, ?, ?)",
            (name, category, description)
        )
    conn.commit()
    print(f"Seeded {len(SKILLS)} skills.")


def seed_roles(conn):
    """Seed roles table."""
    cursor = conn.cursor()
    for name, description in ROLES:
        cursor.execute(
            "INSERT OR IGNORE INTO roles (name, description) VALUES (?, ?)",
            (name, description)
        )
    conn.commit()
    print(f"Seeded {len(ROLES)} roles.")


def seed_role_skill_targets(conn):
    """Seed role_skill_targets table."""
    cursor = conn.cursor()
    
    # Get role IDs
    role_ids = {}
    for role_name, _ in ROLES:
        cursor.execute("SELECT id FROM roles WHERE name = ?", (role_name,))
        row = cursor.fetchone()
        if row:
            role_ids[role_name] = row['id']
    
    # Get skill IDs
    skill_ids = {}
    for name, _, _ in SKILLS:
        cursor.execute("SELECT id FROM skills WHERE name = ?", (name,))
        row = cursor.fetchone()
        if row:
            skill_ids[name] = row['id']
    
    # Insert targets
    count = 0
    for role_name, targets in ROLE_SKILL_TARGETS.items():
        role_id = role_ids.get(role_name)
        if not role_id:
            continue
        for skill_name, target_rating in targets.items():
            skill_id = skill_ids.get(skill_name)
            if not skill_id:
                continue
            cursor.execute(
                """INSERT OR IGNORE INTO role_skill_targets (role_id, skill_id, target_rating)
                   VALUES (?, ?, ?)""",
                (role_id, skill_id, target_rating)
            )
            count += 1
    
    conn.commit()
    print(f"Seeded {count} role-skill targets.")


def main():
    print("Initializing database...")
    init_database()
    
    conn = get_db_connection()
    try:
        seed_skills(conn)
        seed_roles(conn)
        seed_role_skill_targets(conn)
        print("Seeding complete!")
    finally:
        conn.close()


if __name__ == "__main__":
    main()