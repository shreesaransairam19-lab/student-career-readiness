"""
Scoring service for Student Career Readiness System.
Computes gaps, category averages, readiness percentage, and handles assessment persistence.
"""

import sqlite3
from typing import Dict, List, Optional, Any


class ScoringService:
    TECH_ALIASES = {
        'js': 'javascript', 'node': 'node.js', 'nodejs': 'node.js',
        'rest': 'rest apis', 'rest api': 'rest apis', 'api': 'rest apis',
        'auth': 'authentication', 'html': 'html/css', 'css': 'html/css',
        'ml': 'machine learning basics', 'matplotlib': 'data visualization',
        'visualization': 'data visualization', 'interview': 'interview prep',
    }

    def __init__(self, db_path: str):
        self.db_path = db_path

    def get_project_skill_evidence(self, student_id: int) -> Dict[str, int]:
        """Count distinct projects whose technologies name each skill."""
        try:
            conn = self._get_conn()
        except Exception:
            return {}
        try:
            cursor = conn.cursor()
            skills = {row['name'].lower(): row['name'] for row in cursor.execute("SELECT name FROM skills")}
            counts: Dict[str, int] = {}
            cursor.execute("SELECT technologies FROM projects WHERE student_id = ?", (student_id,))
            for row in cursor.fetchall():
                matched = set()
                for raw in (row['technologies'] or '').split(','):
                    tech = raw.strip().lower()
                    if not tech:
                        continue
                    name = skills.get(tech) or skills.get(self.TECH_ALIASES.get(tech, tech))
                    if name:
                        matched.add(name)
                for name in matched:
                    counts[name] = counts.get(name, 0) + 1
            return counts
        except Exception:
            return {}
        finally:
            try:
                conn.close()
            except Exception:
                pass
    
    def _get_conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        conn.row_factory = sqlite3.Row
        return conn
    
    def get_skills_for_role(self, role_id: int) -> List[Dict[str, Any]]:
        """Get all skills for a role with their target ratings."""
        conn = self._get_conn()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT s.id, s.name, s.category, s.description, rst.target_rating
                   FROM skills s
                   JOIN role_skill_targets rst ON s.id = rst.skill_id
                   WHERE rst.role_id = ?
                   ORDER BY s.category, s.name""",
                (role_id,)
            )
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()
    
    def save_assessment(self, student_id: int, role_id: int, ratings: Dict[int, int]) -> int:
        """
        Save a new assessment with skill ratings.
        Returns assessment_id.
        Raises ValueError if any rating is outside 1-5.
        """
        # Validate all ratings
        for skill_id, rating in ratings.items():
            if not isinstance(rating, int) or rating < 1 or rating > 5:
                raise ValueError("Rating must be between 1 and 5")
        
        conn = self._get_conn()
        try:
            cursor = conn.cursor()
            
            # Create assessment
            cursor.execute(
                "INSERT INTO assessments (student_id, role_id) VALUES (?, ?)",
                (student_id, role_id)
            )
            assessment_id = cursor.lastrowid
            
            # Save scores
            for skill_id, rating in ratings.items():
                cursor.execute(
                    "INSERT INTO assessment_scores (assessment_id, skill_id, rating) VALUES (?, ?, ?)",
                    (assessment_id, skill_id, rating)
                )
            
            conn.commit()
            return assessment_id
        finally:
            conn.close()
    
    def get_latest_assessment(self, student_id: int, role_id: int) -> Optional[Dict[str, Any]]:
        """Get the most recent assessment for a student/role."""
        conn = self._get_conn()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT * FROM assessments 
                   WHERE student_id = ? AND role_id = ?
                   ORDER BY created_at DESC LIMIT 1""",
                (student_id, role_id)
            )
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()
    
    def get_assessment_history(self, student_id: int, role_id: int) -> List[Dict[str, Any]]:
        """Get all assessments for a student/role, newest first."""
        conn = self._get_conn()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT * FROM assessments 
                   WHERE student_id = ? AND role_id = ?
                   ORDER BY created_at DESC""",
                (student_id, role_id)
            )
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()
    
    def get_assessment_by_id(self, student_id: int, role_id: int, assessment_id: int) -> Optional[Dict[str, Any]]:
        """Get a specific assessment with its scores (access controlled)."""
        conn = self._get_conn()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT a.* FROM assessments a
                   WHERE a.id = ? AND a.student_id = ? AND a.role_id = ?""",
                (assessment_id, student_id, role_id)
            )
            assessment = cursor.fetchone()
            if not assessment:
                return None
            
            # Get scores
            cursor.execute(
                """SELECT s.id as skill_id, s.name, s.category, s.description, 
                          ast.rating, rst.target_rating
                   FROM assessment_scores ast
                   JOIN skills s ON ast.skill_id = s.id
                   JOIN role_skill_targets rst ON s.id = rst.skill_id AND rst.role_id = ?
                   WHERE ast.assessment_id = ?
                   ORDER BY s.category, s.name""",
                (role_id, assessment_id)
            )
            scores = [dict(row) for row in cursor.fetchall()]
            
            result = dict(assessment)
            result['scores'] = scores
            return result
        finally:
            conn.close()
    
    def compute_gaps(self, student_id: int, role_id: int, assessment_id: int, include_projects: bool = False) -> Dict[int, Dict[str, Any]]:
        """
        Compute gaps for all rated skills in an assessment.
        Returns dict: skill_id -> {skill_name, category, target, actual, gap, status}
        gap = target - actual. include_projects adds up to +2 from matching projects.
        Unrated skills are excluded.
        """
        conn = self._get_conn()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT s.id as skill_id, s.name, s.category, rst.target_rating, ast.rating as actual_rating
                   FROM assessment_scores ast
                   JOIN skills s ON ast.skill_id = s.id
                   JOIN role_skill_targets rst ON s.id = rst.skill_id AND rst.role_id = ?
                   WHERE ast.assessment_id = ?
                   ORDER BY s.category, s.name""",
                (role_id, assessment_id)
            )
            
            evidence = self.get_project_skill_evidence(student_id) if include_projects else {}
            gaps = {}
            for row in cursor.fetchall():
                skill_id = row['skill_id']
                target = row['target_rating']
                base = row['actual_rating']
                bonus = min(2, evidence.get(row['name'], 0))
                actual = min(5, base + bonus)
                gap = target - actual
                
                if gap > 0:
                    status = 'below_target'
                elif gap == 0:
                    status = 'meets_target'
                else:
                    status = 'exceeds_target'
                
                gaps[skill_id] = {
                    'skill_name': row['name'],
                    'category': row['category'],
                    'target': target,
                    'actual': actual,
                    'self_rating': base,
                    'evidence': evidence.get(row['name'], 0),
                    'gap': gap,
                    'status': status
                }
            
            return gaps
        finally:
            conn.close()
    
    def compute_category_averages(self, student_id: int, role_id: int, assessment_id: int, include_projects: bool = False) -> Dict[str, float]:
        """
        Compute average rating per category for assessed skills only.
        Returns dict: category -> average_rating
        include_projects adds up to +2 from matching projects.
        Unassessed skills are excluded. Categories with no assessed skills are omitted.
        """
        conn = self._get_conn()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT s.name, s.category, ast.rating
                   FROM assessment_scores ast
                   JOIN skills s ON ast.skill_id = s.id
                   JOIN role_skill_targets rst ON s.id = rst.skill_id AND rst.role_id = ?
                   WHERE ast.assessment_id = ?""",
                (role_id, assessment_id)
            )
            
            # Group ratings by category
            evidence = self.get_project_skill_evidence(student_id) if include_projects else {}
            category_ratings: Dict[str, List[int]] = {}
            for row in cursor.fetchall():
                category = row['category']
                rating = min(5, row['rating'] + min(2, evidence.get(row['name'], 0)))
                if category not in category_ratings:
                    category_ratings[category] = []
                category_ratings[category].append(rating)
            
            # Compute averages
            averages = {}
            for category, ratings in category_ratings.items():
                if ratings:  # Guard against empty list
                    averages[category] = sum(ratings) / len(ratings)
            
            return averages
        finally:
            conn.close()
    
    def compute_readiness_percentage(self, category_averages: Dict[str, float]) -> float:
        """
        Compute overall readiness percentage.
        Formula: (average of category averages / 5) * 100
        Returns 0.0 if no categories assessed.
        """
        if not category_averages:
            return 0.0
        
        avg_of_averages = sum(category_averages.values()) / len(category_averages)
        return round((avg_of_averages / 5.0) * 100, 1)