import sqlite3
import json
from typing import Dict, Any, List, Optional
import os

class LocalDB:
    def __init__(self):
        db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database')
        if not os.path.exists(db_path):
            os.makedirs(db_path)
        
        self.db_file = os.path.join(db_path, 'resumes.db')
        self._init_db()
    
    def _init_db(self):
        """Initialize the database with required tables and columns"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        # Create resumes table if not exists (without 'name')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS resumes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                content TEXT NOT NULL,
                summary TEXT,
                skills TEXT,
                experience INTEGER,
                cgpa REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Add 'name' column if it does not exist
        cursor.execute("PRAGMA table_info(resumes)")
        columns = [row[1] for row in cursor.fetchall()]
        if 'name' not in columns:
            cursor.execute("ALTER TABLE resumes ADD COLUMN name TEXT DEFAULT ''")
        
        conn.commit()
        conn.close()
    
    def save_resume(self, resume_data: Dict[str, Any]) -> int:
        """Save resume data to SQLite and return the document ID"""
        print("[DEBUG] Starting save_resume")
        print(f"[DEBUG] Input resume_data type: {type(resume_data)}")
        print(f"[DEBUG] Input resume_data content: {resume_data}")
        
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        # Convert lists/dicts to JSON strings for storage
        if 'skills' in resume_data and isinstance(resume_data['skills'], list):
            print("[DEBUG] Converting skills list to JSON string")
            resume_data['skills'] = json.dumps(resume_data['skills'])
        
        cursor.execute('''
            INSERT INTO resumes (filename, content, name, summary, skills, experience, cgpa)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            resume_data.get('filename', ''),
            resume_data.get('content', ''),
            resume_data.get('name', ''),
            resume_data.get('summary', ''),
            resume_data.get('skills', '[]'),
            resume_data.get('experience', 0),
            resume_data.get('cgpa', 0.0)
        ))
        
        last_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return last_id
    
    def get_resume(self, resume_id: int) -> Optional[Dict[str, Any]]:
        """Retrieve a specific resume by ID"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM resumes WHERE id = ?', (resume_id,))
        row = cursor.fetchone()
        
        if row:
            columns = [desc[0] for desc in cursor.description]
            resume_dict = dict(zip(columns, row))
            
            # Convert JSON strings back to Python objects
            if resume_dict.get('skills'):
                resume_dict['skills'] = json.loads(resume_dict['skills'])
            # Map DB fields to app fields
            resume_dict['professional_summary'] = resume_dict.get('summary', '')
            resume_dict['total_years_experience'] = int(resume_dict.get('experience', 0) or 0)
            resume_dict['experience'] = int(resume_dict.get('experience', 0) or 0)
            # Map name if present in content or summary
            if 'name' not in resume_dict or not resume_dict['name']:
                # Try to extract from content or summary if possible
                resume_dict['name'] = resume_dict.get('filename', 'Unnamed')
            # Optionally, remove DB-specific keys if not needed
            
            return resume_dict
        
        conn.close()
        return None
    
    def delete_all_resumes(self):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM resumes')
        conn.commit()
        conn.close()

    def get_all_resumes(self) -> List[Dict[str, Any]]:
        """Retrieve all resumes"""
        print("[DEBUG] Starting get_all_resumes")
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM resumes ORDER BY created_at DESC')
        rows = cursor.fetchall()
        print(f"[DEBUG] Retrieved {len(rows)} rows from database")
        
        columns = [desc[0] for desc in cursor.description]
        print(f"[DEBUG] Database columns: {columns}")
        
        resumes = []
        for i, row in enumerate(rows):
            print(f"[DEBUG] Processing row {i+1}/{len(rows)}")
            resume_dict = dict(zip(columns, row))
            print(f"[DEBUG] Created resume dict: {resume_dict}")
            
            # Convert JSON strings back to Python objects
            if resume_dict.get('skills'):
                print("[DEBUG] Converting skills JSON string back to list")
                resume_dict['skills'] = json.loads(resume_dict['skills'])
            
            resumes.append(resume_dict)
            print(f"[DEBUG] Added resume to list, current count: {len(resumes)}")
        
        conn.close()
        return resumes
