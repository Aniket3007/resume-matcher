import spacy
import re
import json
from typing import Dict, Any, Optional
from utils.llm_client import TogetherLLMClient

class ParserAgent:
    def __init__(self):
        self.nlp = spacy.load("en_core_web_sm")
        self.llm_client = TogetherLLMClient()
        
        # Common regex patterns
        self.email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        self.phone_pattern = r'\b(\+\d{1,2}\s?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}\b'
        self.years_pattern = r'(\d+)\+?\s*(?:years?|yrs?)'
        self.cgpa_pattern = r'(?:CGPA|GPA):\s*(\d+\.?\d*)'
        
    def _extract_with_regex(self, text: str) -> Dict[str, Any]:
        """Fallback extraction using regex patterns"""
        email = re.search(self.email_pattern, text)
        phone = re.search(self.phone_pattern, text)
        years_exp = re.search(self.years_pattern, text)
        cgpa = re.search(self.cgpa_pattern, text)
        
        return {
            "email": email.group(0) if email else None,
            "phone": phone.group(0) if phone else None,
            "total_years_experience": int(years_exp.group(1)) if years_exp else None,
            "cgpa": float(cgpa.group(1)) if cgpa else None
        }
    
    def _extract_with_spacy(self, text: str) -> Dict[str, Any]:
        """Extract entities using spaCy NER"""
        doc = self.nlp(text)
        
        return {
            "name": next((ent.text for ent in doc.ents if ent.label_ == "PERSON"), None),
            "skills": [ent.text for ent in doc.ents if ent.label_ == "PRODUCT"],
            "achievements": [sent.text.strip() for sent in doc.sents 
                           if any(keyword in sent.text.lower() 
                                 for keyword in ["achieved", "award", "recognition", "led", "developed"])]
        }
    
    def parse_resume(self, text: str) -> Dict[str, Any]:
        """
        Parse resume text using a hybrid approach:
        1. Try LLM structured output first
        2. Fall back to regex + spaCy if LLM fails
        """
        print(f"[DEBUG] Starting resume parsing for text length: {len(text)}")
        
        # Initialize with default values
        parsed_data = {
            'name': 'Unnamed',
            'email': '',
            'phone': '',
            'total_years_experience': 0,
            'skills': [],
            'achievements': [],
            'cgpa': 0.0
        }
        
        # First attempt: LLM-based structured extraction
        try:
            llm_prompt = """Extract the following information from this resume. For each field, provide ONLY the extracted information, no explanations:

            Name: [full name]
            Email: [email]
            Phone: [phone number]
            Years of Experience: [number only]
            Skills: [comma-separated list]
            Achievements: [semicolon-separated list]
            CGPA: [cgpa value]

            Resume text:
            {text}"""
            
            llm_response = self.llm_client.get_completion(llm_prompt.format(text=text))
            # Extract the actual content string from the response object
            content = ""
            if hasattr(llm_response, "choices") and len(llm_response.choices) > 0:
                content = llm_response.choices[0].message.content
            print(f"[DEBUG] LLM Content:\n{content}")

            # Parse the content string line by line
            lines = content.strip().split('\n')
            for line in lines:
                print(f"[DEBUG] Parsing line: {line}")
                line = line.strip()
                if not line or ':' not in line:
                    continue
                key, value = [x.strip() for x in line.split(':', 1)]
                key = key.lower()
                if 'name' in key:
                    parsed_data['name'] = value or 'Unnamed'
                elif 'email' in key:
                    parsed_data['email'] = value
                elif 'phone' in key:
                    parsed_data['phone'] = value
                elif 'experience' in key:
                    try:
                        # Extract first number from the text
                        match = re.search(r'\d+', value)
                        parsed_data['total_years_experience'] = int(match.group()) if match else 0
                    except (ValueError, AttributeError):
                        parsed_data['total_years_experience'] = 0
                elif 'skills' in key:
                    # Split skills by comma and clean
                    skills = [s.strip().strip('"').strip("'") for s in value.split(',') if s.strip()]
                    parsed_data['skills'] = skills
                elif 'achievements' in key:
                    # Split achievements by semicolon and clean
                    achievements = [a.strip() for a in value.split(';') if a.strip()]
                    parsed_data['achievements'] = achievements
                elif 'cgpa' in key:
                    try:
                        parsed_data['cgpa'] = float(value)
                    except ValueError:
                        parsed_data['cgpa'] = 0.0
            print(f"[DEBUG] Parsed data: {parsed_data}")
            # If we got here, we have some parsed data
            return parsed_data
            
        except Exception as e:
            print(f"[DEBUG] LLM extraction failed: {str(e)}. Falling back to regex + spaCy")
            
            try:
                # Try regex extraction
                regex_data = self._extract_with_regex(text)
                print(f"[DEBUG] Regex extraction results: {regex_data}")
                
                # Try spaCy extraction
                spacy_data = self._extract_with_spacy(text)
                print(f"[DEBUG] Spacy extraction results: {spacy_data}")
                
                # Update parsed_data with any found values
                if regex_data.get('email'):
                    parsed_data['email'] = regex_data['email']
                if regex_data.get('phone'):
                    parsed_data['phone'] = regex_data['phone']
                if regex_data.get('total_years_experience'):
                    parsed_data['total_years_experience'] = regex_data['total_years_experience']
                
                if spacy_data.get('name'):
                    parsed_data['name'] = spacy_data['name']
                if spacy_data.get('skills'):
                    parsed_data['skills'] = spacy_data['skills']
                if spacy_data.get('achievements'):
                    parsed_data['achievements'] = spacy_data['achievements']
                
                print(f"[DEBUG] Final parsed data: {parsed_data}")
                return parsed_data
                
            except Exception as inner_e:
                print(f"[DEBUG] Fallback extraction failed: {str(inner_e)}")
                # Return the default parsed_data if all extraction methods fail
                return parsed_data
