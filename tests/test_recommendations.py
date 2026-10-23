"""
Unit tests for RecommendationService.
Run with: python -m pytest tests/test_recommendations.py -v
"""

import pytest
from services.recommendations import RecommendationService


class TestRecommendationService:
    """Tests for RecommendationService.get_recommendations method."""
    
    def test_programming_below_target(self):
        """Programming rating below target triggers exercise recommendation."""
        gaps = {
            1: {
                'skill_name': 'Python',
                'category': 'Programming',
                'target': 5,
                'actual': 3,
                'gap': 2,
                'status': 'below_target'
            }
        }
        
        recommendations = RecommendationService.get_recommendations(gaps, 1)
        
        assert len(recommendations) >= 1
        rec = recommendations[0]
        assert 'Python' in rec['action'] or 'programming' in rec['action'].lower()
        assert rec['trigger_gap'] == 2
        assert rec['trigger_skill'] == 'Python'
    
    def test_framework_below_target(self):
        """Framework rating below target triggers CRUD app recommendation."""
        gaps = {
            4: {
                'skill_name': 'React',
                'category': 'Web Development',
                'target': 5,
                'actual': 2,
                'gap': 3,
                'status': 'below_target'
            }
        }
        
        recommendations = RecommendationService.get_recommendations(gaps, 1)
        
        assert len(recommendations) >= 1
        rec = recommendations[0]
        assert 'CRUD' in rec['action'] or 'crud' in rec['action'].lower()
        assert rec['trigger_gap'] == 3
        assert rec['trigger_skill'] == 'React'
    
    def test_database_below_target(self):
        """Database rating below target triggers schema practice recommendation."""
        gaps = {
            2: {
                'skill_name': 'SQL',
                'category': 'Programming',
                'target': 4,
                'actual': 2,
                'gap': 2,
                'status': 'below_target'
            }
        }
        
        recommendations = RecommendationService.get_recommendations(gaps, 1)
        
        assert len(recommendations) >= 1
        rec = recommendations[0]
        assert 'schema' in rec['action'].lower() or 'join' in rec['action'].lower() or 'constraint' in rec['action'].lower()
        assert rec['trigger_gap'] == 2
        assert rec['trigger_skill'] == 'SQL'
    
    def test_git_below_target(self):
        """Git rating below target triggers Git practice recommendation."""
        gaps = {
            3: {
                'skill_name': 'Git',
                'category': 'Programming',
                'target': 4,
                'actual': 2,
                'gap': 2,
                'status': 'below_target'
            }
        }
        
        recommendations = RecommendationService.get_recommendations(gaps, 1)
        
        assert len(recommendations) >= 1
        rec = recommendations[0]
        assert 'commit' in rec['action'].lower() or 'branch' in rec['action'].lower() or 'merge' in rec['action'].lower() or 'conflict' in rec['action'].lower()
        assert rec['trigger_gap'] == 2
        assert rec['trigger_skill'] == 'Git'
    
    def test_communication_below_target(self):
        """Communication rating below target triggers presentation practice."""
        gaps = {
            5: {
                'skill_name': 'Communication',
                'category': 'Soft Skills',
                'target': 4,
                'actual': 2,
                'gap': 2,
                'status': 'below_target'
            }
        }
        
        recommendations = RecommendationService.get_recommendations(gaps, 1)
        
        assert len(recommendations) >= 1
        rec = recommendations[0]
        assert 'explain' in rec['action'].lower() or 'aloud' in rec['action'].lower() or 'feedback' in rec['action'].lower()
        assert rec['trigger_gap'] == 2
        assert rec['trigger_skill'] == 'Communication'
    
    def test_fewer_than_two_projects(self):
        """Fewer than 2 projects triggers build project recommendation."""
        gaps = {}  # No skill gaps
        # We need to simulate the user having fewer than 2 projects
        # This is checked via the user_id in the service
        
        recommendations = RecommendationService.get_recommendations(gaps, 1, project_count=1)
        
        assert len(recommendations) >= 1
        rec = recommendations[0]
        assert 'project' in rec['action'].lower() or 'build' in rec['action'].lower()
    
    def test_interview_prep_below_target(self):
        """Interview prep rating below target triggers practice recommendation."""
        gaps = {
            6: {
                'skill_name': 'Interview Prep',
                'category': 'Soft Skills',
                'target': 3,
                'actual': 1,
                'gap': 2,
                'status': 'below_target'
            }
        }
        
        recommendations = RecommendationService.get_recommendations(gaps, 1)
        
        assert len(recommendations) >= 1
        rec = recommendations[0]
        assert 'interview' in rec['action'].lower() or 'practice' in rec['action'].lower() or 'question' in rec['action'].lower()
        assert rec['trigger_gap'] == 2
        assert rec['trigger_skill'] == 'Interview Prep'
    
    def test_meets_target_no_recommendation(self):
        """Skills meeting target should not trigger recommendations."""
        gaps = {
            1: {
                'skill_name': 'Python',
                'category': 'Programming',
                'target': 5,
                'actual': 5,
                'gap': 0,
                'status': 'meets_target'
            }
        }
        
        recommendations = RecommendationService.get_recommendations(gaps, 1)
        
        # Should not have programming recommendation for this skill
        programming_recs = [r for r in recommendations if 'python' in r['action'].lower() or 'programming' in r['action'].lower()]
        assert len(programming_recs) == 0
    
    def test_exceeds_target_no_recommendation(self):
        """Skills exceeding target should not trigger recommendations."""
        gaps = {
            1: {
                'skill_name': 'Python',
                'category': 'Programming',
                'target': 4,
                'actual': 5,
                'gap': -1,
                'status': 'exceeds_target'
            }
        }
        
        recommendations = RecommendationService.get_recommendations(gaps, 1)
        
        programming_recs = [r for r in recommendations if 'python' in r['action'].lower() or 'programming' in r['action'].lower()]
        assert len(programming_recs) == 0
    
    def test_multiple_gaps_multiple_recommendations(self):
        """Multiple below-target skills should generate multiple recommendations."""
        gaps = {
            1: {
                'skill_name': 'Python',
                'category': 'Programming',
                'target': 5,
                'actual': 2,
                'gap': 3,
                'status': 'below_target'
            },
            4: {
                'skill_name': 'React',
                'category': 'Web Development',
                'target': 5,
                'actual': 1,
                'gap': 4,
                'status': 'below_target'
            },
            5: {
                'skill_name': 'Communication',
                'category': 'Soft Skills',
                'target': 4,
                'actual': 2,
                'gap': 2,
                'status': 'below_target'
            }
        }
        
        recommendations = RecommendationService.get_recommendations(gaps, 1)
        
        # Should have at least 3 recommendations (one per gap)
        assert len(recommendations) >= 3
        
        # Check each recommendation traces to its gap
        for rec in recommendations:
            assert 'trigger_gap' in rec
            assert 'trigger_skill' in rec
            assert rec['trigger_gap'] > 0
    
    def test_recommendation_structure(self):
        """Each recommendation should have required fields."""
        gaps = {
            1: {
                'skill_name': 'Python',
                'category': 'Programming',
                'target': 5,
                'actual': 3,
                'gap': 2,
                'status': 'below_target'
            }
        }
        
        recommendations = RecommendationService.get_recommendations(gaps, 1)
        
        for rec in recommendations:
            assert 'action' in rec
            assert 'trigger_skill' in rec
            assert 'trigger_gap' in rec
            assert isinstance(rec['action'], str)
            assert len(rec['action']) > 0
    
    def test_no_gaps_returns_empty_or_project_rec(self):
        """No skill gaps should return empty list or project recommendation."""
        gaps = {}
        
        recommendations = RecommendationService.get_recommendations(gaps, 1, project_count=3)
        
        # With 3+ projects and no gaps, should be empty
        assert recommendations == []
    
    def test_project_count_zero_triggers_recommendation(self):
        """Zero projects should trigger build project recommendation."""
        gaps = {}
        
        recommendations = RecommendationService.get_recommendations(gaps, 1, project_count=0)
        
        assert len(recommendations) >= 1
        rec = recommendations[0]
        assert 'project' in rec['action'].lower()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

@pytest.mark.parametrize('category,skill,expected', [
    ('Programming', 'Rust', 'focused exercises to improve Rust'),
    ('Programming', 'Testing', 'unit tests'),
    ('Web Development', 'Vue', 'Complete a project focused on Vue'),
    ('Data Analysis', 'Pandas', 'data manipulation with Pandas'),
    ('Data Analysis', 'NumPy', 'data manipulation with NumPy'),
    ('Data Analysis', 'Data Visualization', 'Create 3 different chart types'),
    ('Data Analysis', 'Statistics', 'descriptive and inferential statistics'),
    ('Data Analysis', 'Machine Learning Basics', 'scikit-learn tutorial'),
    ('Data Analysis', 'Excel', 'Complete exercises for Excel'),
    ('Soft Skills', 'Problem Solving', 'Solve 3 algorithmic problems'),
    ('Soft Skills', 'Teamwork', 'group coding exercise'),
    ('Soft Skills', 'Time Management', 'task board for one week'),
    ('Soft Skills', 'Leadership', 'Focus on improving Leadership'),
])
def test_category_specific_rules(category, skill, expected):
    """Every rule branch maps a below-target skill to a concrete action."""
    gaps = {
        99: {
            'skill_name': skill,
            'category': category,
            'target': 5,
            'actual': 1,
            'gap': 4,
            'status': 'below_target',
        }
    }

    recommendations = RecommendationService.get_recommendations(gaps, 1, project_count=2)

    assert len(recommendations) == 1
    rec = recommendations[0]
    assert expected in rec['action']
    assert rec['trigger_skill'] == skill
    assert rec['trigger_gap'] == 4


def test_unknown_category_produces_no_skill_recommendation():
    """A skill outside the known categories is ignored by skill rules."""
    gaps = {99: {
        'skill_name': 'Underwater Basket Weaving',
        'category': 'Other',
        'target': 3,
        'actual': 1,
        'gap': 2,
        'status': 'below_target',
    }}

    assert RecommendationService.get_recommendations(gaps, 1, project_count=2) == []
