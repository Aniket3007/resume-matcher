from utils.llm_client import TogetherLLMClient

class SummarizerAgent:
    def __init__(self):
        self.llm_client = TogetherLLMClient()
    
    def generate_summary(self, resume_data: dict) -> str:
        """
        Generate a professional 4-5 sentence summary of the candidate
        using the parsed resume data
        """
        prompt = f"""Generate a professional 4-5 sentence summary of this candidate in third-person voice.
        Focus on their key skills, experience, and achievements. Keep it under 120 tokens.
        
        Candidate Information:
        Name: {resume_data.get('name', 'The candidate')}
        Years of Experience: {resume_data.get('total_years_experience', 'N/A')}
        Skills: {', '.join(resume_data.get('skills', []))}
        Achievements: {' '.join(resume_data.get('achievements', []))}
        """
        
        # Get LLM response
        response = self.llm_client.get_completion(prompt)
        # Extract summary string from response object
        summary_text = ""
        if hasattr(response, "choices") and len(response.choices) > 0:
            summary_text = getattr(response.choices[0].message, "content", "")
        return summary_text
