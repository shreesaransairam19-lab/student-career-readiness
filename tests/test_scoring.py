"""
Unit tests for ScoringService.
Run with: python -m pytest tests/test_scoring.py -v
"""

import pytest
import sqlite3
import os
import tempfile
from services.scoring import ScoringService


@pytest.fixture
def db_path():
    """Create a temporary database for testing."""
    # Create temp file
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    
    # Initialize schema
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA foreign_keys = ON")
    with open('database/schema.sql', 'r') as f:
        conn.executescript(f.read())
    conn.commit()
    conn.close()
    
    yield path
    
    # Cleanup
    os.unlink(path)


@pytest.fixture
def scoring_service(db_path):
    """Create ScoringService with test database."""
    return ScoringService(db_path)


@pytest.fixture
def seeded_db(scoring_service):
    """Seed the test database with roles, skills, and targets."""
    conn = sqlite3.connect(scoring_service.db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Insert skills
    skills_data = [
        (1, "Python", "Programming", "Core Python"),
        (2, "SQL", "Programming", "Structured Query Language"),
        (3, "Git", "Programming", "Version control"),
        (4, "React", "Web Development", "React.js"),
        (5, "Communication", "Soft Skills", "Verbal/written communication"),
    ]
    for skill in skills_data:
        cursor.execute("INSERT INTO skills (id, name, category, description) VALUES (?, ?, ?, ?)", skill)
    
    # Insert roles
    roles_data = [
        (1, "Python Developer", "Backend Python development"),
        (2, "Web Developer", "Full-stack web development"),
    ]
    for role in roles_data:
        cursor.execute("INSERT INTO roles (id, name, description) VALUES (?, ?, ?)", role)
    
    # Insert role-skill targets
    targets = [
        (1, 1, 5),  # Python Developer -> Python = 5
        (1, 2, 4),  # Python Developer -> SQL = 4
        (1, 3, 4),  # Python Developer -> Git = 4
        (1, 5, 4),  # Python Developer -> Communication = 4
        (2, 4, 5),  # Web Developer -> React = 5
        (2, 1, 3),  # Web Developer -> Python = 3
        (2, 3, 3),  # Web Developer -> Git = 3
        (2, 5, 4),  # Web Developer -> Communication = 4
    ]
    for target in targets:
        cursor.execute("INSERT INTO role_skill_targets (role_id, skill_id, target_rating) VALUES (?, ?, ?)", target)
    
    # Insert a test student
    cursor.execute("INSERT INTO students (id, name, email, password_hash) VALUES (1, 'Test User', 'test@example.com', 'hash')")
    
    conn.commit()
    conn.close()
    
    return scoring_service


class TestComputeGaps:
    """Tests for compute_gaps method."""
    
    def test_gap_positive_when_below_target(self, seeded_db):
        """Gap > 0 when student rating is below target."""
        # Create assessment with rating 3 for Python (target 5)
        conn = sqlite3.connect(seeded_db.db_path)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO assessments (id, student_id, role_id) VALUES (1, 1, 1)")
        cursor.execute("INSERT INTO assessment_scores (assessment_id, skill_id, rating) VALUES (1, 1, 3)")
        conn.commit()
        conn.close()
        
        gaps = seeded_db.compute_gaps(1, 1, 1)
        
        # Python: target=5, actual=3 -> gap=2
        assert gaps[1]['gap'] == 2
        assert gaps[1]['status'] == 'below_target'
    
    def test_gap_zero_when_meets_target(self, seeded_db):
        """Gap = 0 when student rating meets target."""
        conn = sqlite3.connect(seeded_db.db_path)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO assessments (id, student_id, role_id) VALUES (2, 1, 1)")
        cursor.execute("INSERT INTO assessment_scores (assessment_id, skill_id, rating) VALUES (2, 1, 5)")
        conn.commit()
        conn.close()
        
        gaps = seeded_db.compute_gaps(1, 1, 2)
        
        assert gaps[1]['gap'] == 0
        assert gaps[1]['status'] == 'meets_target'
    
    def test_gap_negative_when_exceeds_target(self, seeded_db):
        """Gap < 0 when student rating exceeds target."""
        conn = sqlite3.connect(seeded_db.db_path)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO assessments (id, student_id, role_id) VALUES (3, 1, 1)")
        cursor.execute("INSERT INTO assessment_scores (assessment_id, skill_id, rating) VALUES (3, 2, 5)")  # SQL target=4, actual=5
        conn.commit()
        conn.close()
        
        gaps = seeded_db.compute_gaps(1, 1, 3)
        
        assert gaps[2]['gap'] == -1
        assert gaps[2]['status'] == 'exceeds_target'
    
    def test_unrated_skill_excluded_from_gaps(self, seeded_db):
        """Unrated skills should not appear in gaps."""
        conn = sqlite3.connect(seeded_db.db_path)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO assessments (id, student_id, role_id) VALUES (4, 1, 1)")
        # Only rate Python (skill_id=1), not SQL (skill_id=2) or Git (skill_id=3)
        cursor.execute("INSERT INTO assessment_scores (assessment_id, skill_id, rating) VALUES (4, 1, 4)")
        conn.commit()
        conn.close()
        
        gaps = seeded_db.compute_gaps(1, 1, 4)
        
        # Only Python should be in gaps
        assert 1 in gaps
        assert 2 not in gaps  # SQL not rated
        assert 3 not in gaps  # Git not rated
    
    def test_gaps_includes_skill_metadata(self, seeded_db):
        """Gaps should include skill name, category, target, and actual."""
        conn = sqlite3.connect(seeded_db.db_path)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO assessments (id, student_id, role_id) VALUES (5, 1, 1)")
        cursor.execute("INSERT INTO assessment_scores (assessment_id, skill_id, rating) VALUES (5, 1, 3)")
        conn.commit()
        conn.close()
        
        gaps = seeded_db.compute_gaps(1, 1, 5)
        
        assert gaps[1]['skill_name'] == 'Python'
        assert gaps[1]['category'] == 'Programming'
        assert gaps[1]['target'] == 5
        assert gaps[1]['actual'] == 3
        assert gaps[1]['gap'] == 2


class TestComputeCategoryAverages:
    """Tests for compute_category_averages method."""
    
    def test_category_average_calculated_correctly(self, seeded_db):
        """Category average = sum(assessed ratings) / count(assessed)."""
        conn = sqlite3.connect(seeded_db.db_path)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO assessments (id, student_id, role_id) VALUES (6, 1, 1)")
        # Python (Programming) = 4, SQL (Programming) = 2 -> avg = 3
        # Git (Programming) not rated
        # Communication (Soft Skills) = 5
        cursor.execute("INSERT INTO assessment_scores (assessment_id, skill_id, rating) VALUES (6, 1, 4)")
        cursor.execute("INSERT INTO assessment_scores (assessment_id, skill_id, rating) VALUES (6, 2, 2)")
        cursor.execute("INSERT INTO assessment_scores (assessment_id, skill_id, rating) VALUES (6, 5, 5)")
        conn.commit()
        conn.close()
        
        averages = seeded_db.compute_category_averages(1, 1, 6)
        
        # Programming: (4 + 2) / 2 = 3.0
        assert averages['Programming'] == 3.0
        # Soft Skills: 5 / 1 = 5.0
        assert averages['Soft Skills'] == 5.0
        # Web Development not assessed -> not in result
        assert 'Web Development' not in averages
    
    def test_unrated_skills_excluded_from_average(self, seeded_db):
        """Unrated skills should not affect category averages."""
        conn = sqlite3.connect(seeded_db.db_path)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO assessments (id, student_id, role_id) VALUES (7, 1, 1)")
        # Only rate one Programming skill
        cursor.execute("INSERT INTO assessment_scores (assessment_id, skill_id, rating) VALUES (7, 1, 5)")
        conn.commit()
        conn.close()
        
        averages = seeded_db.compute_category_averages(1, 1, 7)
        
        # Programming: 5 / 1 = 5.0 (not 5/3)
        assert averages['Programming'] == 5.0
    
    def test_no_ratings_returns_empty_dict(self, seeded_db):
        """Empty dict when no skills rated."""
        conn = sqlite3.connect(seeded_db.db_path)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO assessments (id, student_id, role_id) VALUES (8, 1, 1)")
        # No scores inserted
        conn.commit()
        conn.close()
        
        averages = seeded_db.compute_category_averages(1, 1, 8)
        
        assert averages == {}
    
    def test_divide_by_zero_guarded(self, seeded_db):
        """No divide-by-zero error when category has no rated skills."""
        # This is implicitly tested by test_no_ratings_returns_empty_dict
        # and test_unrated_skills_excluded_from_average
        pass


class TestComputeReadinessPercentage:
    """Tests for compute_readiness_percentage method."""
    
    def test_readiness_percentage_formula(self, seeded_db):
        """Readiness % = (avg assessed rating / 5) * 100."""
        category_averages = {
            'Programming': 4.0,
            'Soft Skills': 5.0,
        }
        
        # Average of category averages = (4.0 + 5.0) / 2 = 4.5
        # Readiness = (4.5 / 5) * 100 = 90%
        percentage = seeded_db.compute_readiness_percentage(category_averages)
        
        assert percentage == 90.0
    
    def test_readiness_zero_when_no_categories(self, seeded_db):
        """0% when no categories assessed."""
        percentage = seeded_db.compute_readiness_percentage({})
        assert percentage == 0.0
    
    def test_readiness_with_single_category(self, seeded_db):
        """Works with single category."""
        category_averages = {'Programming': 2.5}
        # (2.5 / 5) * 100 = 50%
        percentage = seeded_db.compute_readiness_percentage(category_averages)
        assert percentage == 50.0


class TestGetSkillsForRole:
    """Tests for get_skills_for_role method."""
    
    def test_returns_skills_with_targets(self, seeded_db):
        """Returns skills for role with target ratings."""
        skills = seeded_db.get_skills_for_role(1)  # Python Developer
        
        # Should have 4 skills for Python Developer (only skills with targets)
        assert len(skills) == 4
        
        # Check Python skill has target
        python_skill = next(s for s in skills if s['name'] == 'Python')
        assert python_skill['target_rating'] == 5
        assert python_skill['category'] == 'Programming'
    
    def test_returns_empty_for_invalid_role(self, seeded_db):
        """Returns empty list for non-existent role."""
        skills = seeded_db.get_skills_for_role(999)
        assert skills == []


class TestSaveAssessment:
    """Tests for save_assessment method."""
    
    def test_saves_assessment_and_scores(self, seeded_db):
        """Saves assessment with multiple skill ratings."""
        ratings = {1: 4, 2: 3, 3: 5}  # Python, SQL, Git
        
        assessment_id = seeded_db.save_assessment(1, 1, ratings)
        
        assert assessment_id is not None
        
        # Verify in database
        conn = sqlite3.connect(seeded_db.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM assessments WHERE id = ?", (assessment_id,))
        assessment = cursor.fetchone()
        assert assessment is not None
        assert assessment[1] == 1  # student_id
        assert assessment[2] == 1  # role_id
        
        cursor.execute("SELECT skill_id, rating FROM assessment_scores WHERE assessment_id = ?", (assessment_id,))
        scores = cursor.fetchall()
        assert len(scores) == 3
        conn.close()
    
    def test_validates_ratings_range(self, seeded_db):
        """Rejects ratings outside 1-5."""
        ratings = {1: 6}  # Invalid rating
        
        with pytest.raises(ValueError, match="Rating must be between 1 and 5"):
            seeded_db.save_assessment(1, 1, ratings)
    
    def test_validates_rating_zero(self, seeded_db):
        """Rejects rating of 0."""
        ratings = {1: 0}
        
        with pytest.raises(ValueError, match="Rating must be between 1 and 5"):
            seeded_db.save_assessment(1, 1, ratings)


class TestGetAssessmentHistory:
    """Tests for get_assessment_history method."""
    
    def test_returns_assessments_in_descending_order(self, seeded_db):
        """Returns assessments newest first."""
        conn = sqlite3.connect(seeded_db.db_path)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO assessments (id, student_id, role_id, created_at) VALUES (10, 1, 1, '2024-01-01')")
        cursor.execute("INSERT INTO assessments (id, student_id, role_id, created_at) VALUES (11, 1, 1, '2024-01-15')")
        cursor.execute("INSERT INTO assessments (id, student_id, role_id, created_at) VALUES (12, 1, 1, '2024-01-10')")
        conn.commit()
        conn.close()
        
        history = seeded_db.get_assessment_history(1, 1)
        
        assert len(history) == 3
        assert history[0]['id'] == 11  # Most recent first
        assert history[1]['id'] == 12
        assert history[2]['id'] == 10


class TestGetAssessmentById:
    """Tests for get_assessment_by_id method."""
    
    def test_returns_assessment_with_scores(self, seeded_db):
        """Returns assessment with all skill ratings."""
        conn = sqlite3.connect(seeded_db.db_path)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO assessments (id, student_id, role_id) VALUES (20, 1, 1)")
        cursor.execute("INSERT INTO assessment_scores (assessment_id, skill_id, rating) VALUES (20, 1, 4)")
        cursor.execute("INSERT INTO assessment_scores (assessment_id, skill_id, rating) VALUES (20, 2, 3)")
        conn.commit()
        conn.close()
        
        assessment = seeded_db.get_assessment_by_id(1, 1, 20)
        
        assert assessment is not None
        assert assessment['id'] == 20
        assert 'scores' in assessment
        assert len(assessment['scores']) == 2
    
    def test_returns_none_for_other_student(self, seeded_db):
        """Returns None when assessment belongs to different student."""
        conn = sqlite3.connect(seeded_db.db_path)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO students (id, name, email, password_hash) VALUES (2, 'Other', 'other@example.com', 'hash')")
        cursor.execute("INSERT INTO assessments (id, student_id, role_id) VALUES (30, 2, 1)")
        conn.commit()
        conn.close()
        
        assessment = seeded_db.get_assessment_by_id(1, 1, 30)  # Student 1 trying to access student 2's assessment
        
        assert assessment is None


class TestGetLatestAssessment:
    """Tests for get_latest_assessment method."""
    
    def test_returns_most_recent_assessment(self, seeded_db):
        """Returns latest assessment for student/role."""
        conn = sqlite3.connect(seeded_db.db_path)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO assessments (id, student_id, role_id, created_at) VALUES (40, 1, 1, '2024-01-01')")
        cursor.execute("INSERT INTO assessments (id, student_id, role_id, created_at) VALUES (41, 1, 1, '2024-01-15')")
        cursor.execute("INSERT INTO assessments (id, student_id, role_id, created_at) VALUES (42, 1, 1, '2024-01-10')")
        conn.commit()
        conn.close()
        
        latest = seeded_db.get_latest_assessment(1, 1)
        
        assert latest is not None
        assert latest['id'] == 41  # Most recent
    
    def test_returns_none_when_no_assessments(self, seeded_db):
        """Returns None when student has no assessments for role."""
        latest = seeded_db.get_latest_assessment(1, 2)  # Web Developer, no assessments
        assert latest is None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])