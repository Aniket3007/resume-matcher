from typing import Dict, Any, List
from agents.parser_agent import ParserAgent
from agents.summarizer_agent import SummarizerAgent
from agents.matcher_agent import MatcherAgent
from utils.local_db import LocalDB

class ResumeWorkflow:
    def __init__(self):
        self.parser = ParserAgent()
        self.summarizer = SummarizerAgent()
        self.matcher = MatcherAgent()
        self.db = LocalDB()
    
    def process_resume(self, resume_text: str) -> Dict[str, Any]:
        """
        Process a single resume through the parse → summarize workflow
        """
        try:
            print("\n[DEBUG] ===== Starting process_resume =====")
            print(f"[DEBUG] Resume text length: {len(resume_text)}")
            print(f"[DEBUG] First 100 chars: {resume_text[:100]}...")
            
            # Parse resume
            print("\n[DEBUG] ----- Parsing Resume -----")
            try:
                parsed_data = self.parser.parse_resume(resume_text)
                print(f"[DEBUG] Parsed data type: {type(parsed_data)}")
                print(f"[DEBUG] Parsed data: {parsed_data}")
            except Exception as e:
                print(f"[DEBUG] ERROR in parse_resume: {str(e)}")
                print(f"[DEBUG] Error type: {type(e)}")
                raise
            
            # Generate summary
            print("\n[DEBUG] ----- Generating Summary -----")
            try:
                summary = self.summarizer.generate_summary(parsed_data)
                print(f"[DEBUG] Summary type: {type(summary)}")
                print(f"[DEBUG] Summary: {summary}")
                parsed_data['professional_summary'] = summary
            except Exception as e:
                print(f"[DEBUG] ERROR in generate_summary: {str(e)}")
                print(f"[DEBUG] Error type: {type(e)}")
                raise
            
            # Save to database
            print("\n[DEBUG] ----- Saving to Database -----")
            try:
                # Map parsed_data to DB columns and sanitize
                db_resume = {
                    'filename': parsed_data.get('filename', ''),
                    'content': parsed_data.get('content', ''),
                    'name': parsed_data.get('name', ''),
                    'summary': parsed_data.get('professional_summary', ''),
                    'skills': parsed_data.get('skills', []),
                    'experience': parsed_data.get('total_years_experience', 0),
                    'cgpa': parsed_data.get('cgpa', 0.0),
                }
                doc_id = self.db.save_resume(db_resume)
                print(f"[DEBUG] doc_id type: {type(doc_id)}")
                print(f"[DEBUG] doc_id: {doc_id}")
                parsed_data['document_id'] = doc_id
            except Exception as e:
                print(f"[DEBUG] ERROR in save_resume: {str(e)}")
                print(f"[DEBUG] Error type: {type(e)}")
                raise
            
            print("\n[DEBUG] ===== Completed process_resume =====")
            return parsed_data
            
        except Exception as e:
            print(f"\n[DEBUG] !!!!! CRITICAL ERROR in process_resume: {str(e)}")
            print(f"[DEBUG] Error type: {type(e)}")
            raise
    
    def process_resumes(self, resume_texts: List[str]) -> List[Dict[str, Any]]:
        """
        Process multiple resumes in sequence
        """
        print("[DEBUG] Starting process_resumes")
        print(f"[DEBUG] Number of resumes to process: {len(resume_texts)}")
        
        results = []
        for i, resume_text in enumerate(resume_texts):
            print(f"\n[DEBUG] Processing resume {i+1}/{len(resume_texts)}")
            print(f"[DEBUG] Resume text length: {len(resume_text)}")
            try:
                print("[DEBUG] Calling process_resume")
                result = self.process_resume(resume_text)
                print(f"[DEBUG] Result type: {type(result)}")
                print(f"[DEBUG] Result content: {result}")
                results.append(result)
            except Exception as e:
                print(f"[DEBUG] Error processing resume: {str(e)}")
                print(f"[DEBUG] Error type: {type(e)}")
                raise  # Re-raise to handle in the upload route
        return results
    
    def match_resumes(self, job_description: str, num_matches: int = 5) -> List[Dict[str, Any]]:
        """
        Match resumes against a job description
        """
        resumes = self.db.get_all_resumes()
        scored_resumes = []
        for resume in resumes:
            score, explanation = self.matcher.score_resume(
                resume, job_description
            )
            resume['match_score'] = score
            resume['match_explanation'] = explanation
            scored_resumes.append(resume)
        scored_resumes.sort(key=lambda x: x['match_score'], reverse=True)
        return scored_resumes[:num_matches]
    
