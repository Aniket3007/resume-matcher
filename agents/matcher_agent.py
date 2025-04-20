import re
from typing import Dict, List, Tuple
from utils.llm_client import TogetherLLMClient

class MatcherAgent:
    def __init__(self):
        self.llm_client = TogetherLLMClient()
    
    def score_resume(self, resume_data: Dict, job_description: str, 
                    required_skills: List[str] = None, 
                    min_years: int = None,
                    min_cgpa: float = None) -> Tuple[int, str]:
        """
        Score a resume against job requirements and return (score, explanation)
        """
        # First check hard requirements
        if min_years and (not resume_data.get('total_years_experience') or 
                         resume_data['total_years_experience'] < min_years):
            return 0, f"Does not meet minimum experience requirement of {min_years} years"
            
        if min_cgpa and (not resume_data.get('cgpa') or 
                        resume_data['cgpa'] < min_cgpa):
            return 0, f"Does not meet minimum CGPA requirement of {min_cgpa}"
            
        if required_skills:
            candidate_skills = set(s.lower() for s in resume_data.get('skills', []))
            missing_skills = [s for s in required_skills 
                            if s.lower() not in candidate_skills]
            if missing_skills:
                return 2, f"Missing required skills: {', '.join(missing_skills)}"
        
        # Use LLM for detailed scoring
        prompt = f"""Score this candidate for the job. Only output an integer between 1 and 10 (inclusive), where 10 is best fit and 1 is worst fit. Format: "<score>: <explanation>"
        
        Job Description:
        {job_description}
        
        Candidate Profile:
        - Experience: {resume_data.get('total_years_experience')} years
        - Skills: {', '.join(resume_data.get('skills', []))}
        - Achievements: {' '.join(resume_data.get('achievements', []))}
        - CGPA: {resume_data.get('cgpa', 'Not specified')}
        """
        
        response = self.llm_client.get_completion(prompt)
        # Extract the actual message content (string) from the response object
        if hasattr(response, "choices") and len(response.choices) > 0:
            response_text = getattr(response.choices[0].message, "content", "")
        else:
            response_text = str(response)  # fallback

        # Extract score and explanation
        match = re.match(r'(\d+):\s*(.+)', response_text)
        if match:
            score = int(match.group(1))
            # Clamp score to 1-10
            score = max(1, min(score, 10))
            explanation = match.group(2)
            return score, explanation
        
        return 5, "Score extraction failed, defaulting to neutral score"
    
    def rank_candidates(self, resumes: List[Dict], job_description: str, 
                       required_skills: List[str] = None,
                       min_years: int = None,
                       min_cgpa: float = None) -> List[Dict]:
        """
        Rank all candidates for a job and return sorted results with scores
        """
        scored_candidates = []
        
        for resume in resumes:
            score, explanation = self.score_resume(
                resume, job_description, required_skills, min_years, min_cgpa
            )
            scored_candidates.append({
                **resume,
                "match_score": score,
                "match_explanation": explanation
            })
        
        return sorted(scored_candidates, 
                     key=lambda x: x['match_score'], 
                     reverse=True)
