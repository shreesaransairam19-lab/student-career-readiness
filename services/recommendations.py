"""
Recommendation service for Student Career Readiness System.
Rule-based recommendations traceable to specific skill gaps.
"""

from typing import Dict, List, Any, Optional


class RecommendationService:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path

    @staticmethod
    def get_recommendations(gaps: Dict[int, Dict[str, Any]], user_id: int, project_count: int = 0) -> List[Dict[str, Any]]:
        """
        Generate recommendations based on skill gaps and project count.
        
        Args:
            gaps: Dict of skill_id -> gap info (from ScoringService.compute_gaps)
            user_id: Student ID (for future extensibility)
            project_count: Number of projects logged by student
            
        Returns:
            List of recommendation dicts with: action, trigger_skill, trigger_gap
        """
        LEARN_LINKS = {'Python': 'https://www.w3schools.com/python/', 'JavaScript': 'https://developer.mozilla.org/en-US/docs/Web/JavaScript', 'SQL': 'https://www.w3schools.com/sql/', 'Git': 'https://learngitbranching.js.org/', 'Testing': 'https://jestjs.io/docs/getting-started', 'HTML/CSS': 'https://developer.mozilla.org/en-US/docs/Learn/HTML', 'React': 'https://react.dev/learn', 'Node.js': 'https://nodejs.org/en/learn', 'REST APIs': 'https://developer.mozilla.org/en-US/docs/Glossary/REST', 'Authentication': 'https://developer.mozilla.org/en-US/docs/Learn/Server-side/First_steps/Website_security', 'Pandas': 'https://pandas.pydata.org/docs/getting_started/intro_tutorials/', 'NumPy': 'https://numpy.org/learn/', 'Data Visualization': 'https://matplotlib.org/stable/tutorials/index.html', 'Statistics': 'https://www.khanacademy.org/math/statistics-probability', 'Machine Learning Basics': 'https://scikit-learn.org/stable/tutorial/', 'Communication': 'https://www.coursera.org/learn/wharton-communication-skills', 'Problem Solving': 'https://leetcode.com/problemset/', 'Teamwork': 'https://www.mindtools.com/pages/article/newTMM_80.htm', 'Time Management': 'https://www.mindtools.com/pages/main/newMN_HTE.htm', 'Interview Prep': 'https://www.indeed.com/career-advice/interviewing', 'Projects': 'https://www.freecodecamp.org/learn/'}
        recommendations = []
        
        # Rule 1: Programming skills below target
        for skill_id, gap_info in gaps.items():
            if gap_info['status'] != 'below_target':
                continue
                
            skill_name = gap_info['skill_name']
            category = gap_info['category']
            gap = gap_info['gap']
            
            if category == 'Programming':
                if skill_name == 'SQL':
                    recommendations.append({
                        'action': 'Practice schema design, joins, and constraints',
                        'trigger_skill': skill_name,
                        'trigger_gap': gap,
                    'link': LEARN_LINKS.get(skill_name)
                    })
                elif skill_name in ['Python', 'JavaScript']:
                    recommendations.append({
                        'action': f'Complete focused exercises and build one small program to improve {skill_name}',
                        'trigger_skill': skill_name,
                        'trigger_gap': gap,
                    'link': LEARN_LINKS.get(skill_name)
                    })
                elif skill_name == 'Git':
                    recommendations.append({
                        'action': 'Practice commits, branches, merges, and resolving a conflict',
                        'trigger_skill': skill_name,
                        'trigger_gap': gap,
                    'link': LEARN_LINKS.get(skill_name)
                    })
                elif skill_name == 'Testing':
                    recommendations.append({
                        'action': 'Write unit tests for a recent project; aim for 80% coverage',
                        'trigger_skill': skill_name,
                        'trigger_gap': gap,
                    'link': LEARN_LINKS.get(skill_name)
                    })
                else:
                    recommendations.append({
                        'action': f'Complete focused exercises to improve {skill_name}',
                        'trigger_skill': skill_name,
                        'trigger_gap': gap,
                    'link': LEARN_LINKS.get(skill_name)
                    })
            
            # Rule 2: Framework/Web Development skills below target
            elif category == 'Web Development':
                if skill_name in ['React', 'Node.js', 'HTML/CSS', 'REST APIs', 'Authentication']:
                    recommendations.append({
                        'action': f'Build a CRUD app using {skill_name}',
                        'trigger_skill': skill_name,
                        'trigger_gap': gap,
                    'link': LEARN_LINKS.get(skill_name)
                    })
                else:
                    recommendations.append({
                        'action': f'Complete a project focused on {skill_name}',
                        'trigger_skill': skill_name,
                        'trigger_gap': gap,
                    'link': LEARN_LINKS.get(skill_name)
                    })
            
            # Rule 3: Data Analysis skills below target
            elif category == 'Data Analysis':
                if skill_name in ['Pandas', 'NumPy']:
                    recommendations.append({
                        'action': f'Practice data manipulation with {skill_name} on real datasets',
                        'trigger_skill': skill_name,
                        'trigger_gap': gap,
                    'link': LEARN_LINKS.get(skill_name)
                    })
                elif skill_name == 'Data Visualization':
                    recommendations.append({
                        'action': 'Create 3 different chart types from a dataset; explain insights',
                        'trigger_skill': skill_name,
                        'trigger_gap': gap,
                    'link': LEARN_LINKS.get(skill_name)
                    })
                elif skill_name == 'Statistics':
                    recommendations.append({
                        'action': 'Practice descriptive and inferential statistics on sample data',
                        'trigger_skill': skill_name,
                        'trigger_gap': gap,
                    'link': LEARN_LINKS.get(skill_name)
                    })
                elif skill_name == 'Machine Learning Basics':
                    recommendations.append({
                        'action': 'Complete a scikit-learn tutorial end-to-end',
                        'trigger_skill': skill_name,
                        'trigger_gap': gap,
                    'link': LEARN_LINKS.get(skill_name)
                    })
                else:
                    recommendations.append({
                        'action': f'Complete exercises for {skill_name}',
                        'trigger_skill': skill_name,
                        'trigger_gap': gap,
                    'link': LEARN_LINKS.get(skill_name)
                    })
            
            # Rule 4: Soft Skills below target
            elif category == 'Soft Skills':
                if skill_name == 'Communication':
                    recommendations.append({
                        'action': 'Explain one project aloud in 2 minutes; get feedback from a peer',
                        'trigger_skill': skill_name,
                        'trigger_gap': gap,
                    'link': LEARN_LINKS.get(skill_name)
                    })
                elif skill_name == 'Problem Solving':
                    recommendations.append({
                        'action': 'Solve 3 algorithmic problems; write up your approach for each',
                        'trigger_skill': skill_name,
                        'trigger_gap': gap,
                    'link': LEARN_LINKS.get(skill_name)
                    })
                elif skill_name == 'Teamwork':
                    recommendations.append({
                        'action': 'Participate in a group coding exercise or hackathon',
                        'trigger_skill': skill_name,
                        'trigger_gap': gap,
                    'link': LEARN_LINKS.get(skill_name)
                    })
                elif skill_name == 'Time Management':
                    recommendations.append({
                        'action': 'Use a task board for one week; track time spent per task',
                        'trigger_skill': skill_name,
                        'trigger_gap': gap,
                    'link': LEARN_LINKS.get(skill_name)
                    })
                elif skill_name == 'Interview Prep':
                    recommendations.append({
                        'action': 'Practice role-specific technical and behavioral questions with a partner',
                        'trigger_skill': skill_name,
                        'trigger_gap': gap,
                    'link': LEARN_LINKS.get(skill_name)
                    })
                else:
                    recommendations.append({
                        'action': f'Focus on improving {skill_name} through deliberate practice',
                        'trigger_skill': skill_name,
                        'trigger_gap': gap,
                    'link': LEARN_LINKS.get(skill_name)
                    })
        
        # Rule 5: Fewer than 2 projects logged
        if project_count < 2:
            recommendations.append({
                'action': 'Build one complete project for your target role and log it',
                'trigger_skill': 'Projects',
                'trigger_gap': 2 - project_count,
                'link': LEARN_LINKS.get('Projects')
            })
        
        return recommendations