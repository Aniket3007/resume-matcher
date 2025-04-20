from typing import List, Dict, Any
from utils.local_db import LocalDB

class FilterAgent:
    def __init__(self):
        self.db = LocalDB()
        
    def filter_by_skills(self, skills: List[str], require_all: bool = False) -> List[Dict[str, Any]]:
        """
        Filter resumes by required skills
        """
        resumes = self.db.get_all_resumes()
        
        if not skills or all(not s.strip() for s in skills):
            return resumes
        
        skills_lower = [s.strip().lower() for s in skills if s.strip()]
        
        filtered = []
        for resume in resumes:
            candidate_skills = [str(s).strip().lower() for s in resume.get('skills', []) if s]
            
            if require_all:
                if all(skill in candidate_skills for skill in skills_lower):
                    filtered.append(resume)
            else:
                if any(skill in candidate_skills for skill in skills_lower):
                    filtered.append(resume)
        
        return filtered
    
    def filter_by_experience(self, min_years: int = None, max_years: int = None) -> List[Dict[str, Any]]:
        """
        Filter resumes by years of experience range
        """
        filters = {}
        if min_years is not None:
            filters['total_years_experience'] = min_years
        
        resumes = self.db.filter_resumes(filters)
        
        if max_years is not None:
            resumes = [r for r in resumes 
                      if r.get('total_years_experience', 0) <= max_years]
        
        return resumes
    
    def filter_by_cgpa(self, min_cgpa: float) -> List[Dict[str, Any]]:
        """
        Filter resumes by minimum CGPA
        """
        return self.db.filter_resumes({'cgpa': min_cgpa})
