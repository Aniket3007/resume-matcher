import os
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify, flash, redirect, url_for

# Load environment variables from .env file
load_dotenv()
from werkzeug.utils import secure_filename
from utils.pdf_utils import validate_pdf, extract_text_from_pdf
from utils.local_db import LocalDB
from workflows.resume_workflow import ResumeWorkflow
from agents.filter_agent import FilterAgent
from agents.matcher_agent import MatcherAgent

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Initialize components
db = LocalDB()
workflow = ResumeWorkflow()
filter_agent = FilterAgent()
matcher_agent = MatcherAgent()

# Configure upload folder
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() == 'pdf'

@app.route('/')
def index():
    resumes = db.get_all_resumes()
    return render_template('index.html', resumes=resumes)

@app.route('/delete_all_resumes')
def delete_all_resumes():
    db.delete_all_resumes()
    return redirect(url_for('index'))

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        print("[DEBUG] POST request received at /upload")
        if 'files[]' not in request.files:
            print("[DEBUG] No files found in request")
            return 'No files selected', 400, {'Content-Type': 'text/plain'}
            
        valid_files = []
        resume_texts = []
        invalid_files = []
            
        files = request.files.getlist('files[]')
        print(f"[DEBUG] Number of files received: {len(files)}")
        
        for file in files:
            print(f"[DEBUG] Processing file: {file.filename if file else 'None'}")
            if not file or not file.filename:
                print("[DEBUG] Empty file or no filename")
                continue
                
            if not allowed_file(file.filename):
                print(f"[DEBUG] Invalid file type: {file.filename}")
                invalid_files.append(f"{file.filename} (not a PDF)")
                continue
                
            filename = secure_filename(file.filename)
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            
            # Create upload folder if it doesn't exist
            os.makedirs(UPLOAD_FOLDER, exist_ok=True)
            
            print(f"[DEBUG] About to save file: {filename}")
            print(f"[DEBUG] Full save path: {os.path.abspath(filepath)}")
            print(f"[DEBUG] File object type: {type(file)}")
            print(f"[DEBUG] File object attributes: {dir(file)}")
            
            # Save the file in binary mode
            file.save(filepath)
            
            # Verify the saved file
            if os.path.exists(filepath):
                size = os.path.getsize(filepath)
                print(f"[DEBUG] File saved successfully. Size: {size} bytes")
                # Read first few bytes to check PDF signature
                with open(filepath, 'rb') as f:
                    header = f.read(20)
                    print(f"[DEBUG] Saved file header: {header}")
            else:
                print(f"[DEBUG] Error: File was not saved to {filepath}")
            
            if not validate_pdf(filepath):
                print(f"[DEBUG] Invalid PDF: {filename}")
                invalid_files.append(f"{filename} (invalid PDF format)")
                continue
                
            valid_files.append(filename)
        
        if invalid_files:
            error_msg = "The following files could not be processed:\n" + "\n".join(f"• {f}" for f in invalid_files)
            return error_msg, 400, {'Content-Type': 'text/plain'}
                
        # Process all resumes
        if valid_files:
            print("[DEBUG] Extracting text from PDFs")
            resume_texts = []
            processed_resumes = []
            
            for filename in valid_files:
                filepath = os.path.join(UPLOAD_FOLDER, filename)
                print(f"\n[DEBUG] ===== Processing file: {filename} =====")
                
                # Extract text from PDF
                print(f"[DEBUG] Starting text extraction from: {filepath}")
                text = extract_text_from_pdf(filepath)
                
                if not text:
                    print(f"[DEBUG] No text extracted from {filename}")
                    continue
                    
                print(f"[DEBUG] Extracted text length: {len(text)}")
                print(f"[DEBUG] First 200 chars of extracted text:\n{text[:200]}...")
                
                # Process resume
                print(f"\n[DEBUG] ----- Processing resume text -----")
                workflow = ResumeWorkflow()
                
                try:
                    # Process the resume and get the parsed data
                    processed_resume = workflow.process_resume(text)
                    print(f"[DEBUG] Resume processing result: {processed_resume}")
                    
                    if processed_resume is None:
                        print("[DEBUG] No resume data returned from processing")
                        processed_resume = {
                            'name': 'Unnamed',
                            'total_years_experience': 0,
                            'skills': [],
                            'achievements': []
                        }
                    elif not isinstance(processed_resume, dict):
                        print(f"[DEBUG] Converting non-dict result to dict: {type(processed_resume)}")
                        # Try to convert from a generator or other type
                        try:
                            if hasattr(processed_resume, '__next__') or hasattr(processed_resume, '__iter__'):
                                # If it's a generator or iterator, take the first item
                                first_item = next(iter(processed_resume), None)
                                if isinstance(first_item, dict):
                                    processed_resume = first_item
                                else:
                                    print(f"[DEBUG] First item is not a dict: {type(first_item)}")
                                    processed_resume = {
                                        'name': str(first_item) if first_item else 'Unnamed',
                                        'total_years_experience': 0,
                                        'skills': [],
                                        'achievements': []
                                    }
                            else:
                                # Try to convert object attributes to dict
                                processed_resume = {
                                    'name': str(getattr(processed_resume, 'name', 'Unnamed')),
                                    'total_years_experience': int(getattr(processed_resume, 'total_years_experience', 0)),
                                    'skills': list(getattr(processed_resume, 'skills', [])),
                                    'achievements': list(getattr(processed_resume, 'achievements', []))
                                }
                        except Exception as e:
                            print(f"[DEBUG] Error converting to dict: {str(e)}")
                            processed_resume = {
                                'name': 'Unnamed',
                                'total_years_experience': 0,
                                'skills': [],
                                'achievements': []
                            }
                    
                    processed_resumes.append(processed_resume)
                    
                except Exception as e:
                    print(f"[DEBUG] Error processing resume: {str(e)}")
                    print(f"[DEBUG] Error type: {type(e)}")
                    continue
                
                # Convert resume data to text format
                print("[DEBUG] Converting to text format")
                achievements = '\n'.join([f'• {a}' for a in processed_resume.get('achievements', [])]) if processed_resume.get('achievements', []) else 'None listed'
                resume_text = f"""
                Name: {processed_resume.get('name', 'Unnamed')}
                Experience: {processed_resume.get('total_years_experience', 0)} years
                Skills: {', '.join(str(s) for s in processed_resume.get('skills', []))}
                Achievements:
                {achievements}
                """.strip()
                try:
                    for resume in processed_resumes:
                        print(f"[DEBUG] Processing resume: {type(resume)}")
                        print(f"[DEBUG] Resume content: {resume}")
                        
                        if not isinstance(resume, dict):
                            print(f"[DEBUG] Converting resume to dict: {resume}")
                            resume = {
                                'name': str(resume.name) if hasattr(resume, 'name') else 'Unnamed',
                                'total_years_experience': getattr(resume, 'total_years_experience', 0),
                                'skills': list(getattr(resume, 'skills', [])),
                                'achievements': list(getattr(resume, 'achievements', []))
                            }
                        
                        # Format skills as comma-separated list
                        skills = resume.get('skills', [])
                        if not isinstance(skills, list):
                            skills = list(skills) if skills else []
                        skills_text = ', '.join(str(s) for s in skills)
                        
                        # Format achievements as bullet points
                        achievements = resume.get('achievements', [])
                        if not isinstance(achievements, list):
                            achievements = list(achievements) if achievements else []
                        achievements_text = '\n'.join([f'• {a}' for a in achievements]) if achievements else 'None listed'
                        
                        resume_text = f"""
                        Name: {resume.get('name', 'Unnamed')}
                        Experience: {resume.get('total_years_experience', 0)} years
                        Skills: {skills_text}
                        Achievements:
                        {achievements_text}
                        """.strip()
                        
                        print(f"[DEBUG] Formatted resume text:\n{resume_text}")
                        resume_texts.append(resume_text)
                    
                    response_text = f"Successfully processed {len(processed_resumes)} resumes\n\n" + "\n\n---\n\n".join(resume_texts)
                    return response_text, 200, {'Content-Type': 'text/plain'}
                except Exception as e:
                    error_message = f'Error processing resumes: {str(e)}'
                    print(f'[DEBUG] {error_message}')
                    return error_message, 500, {'Content-Type': 'text/plain'}
        
        return 'No valid files to process', 400, {'Content-Type': 'text/plain'}
    
    if request.method == 'GET':
        return render_template('upload.html')
    
    return jsonify({
        'success': False,
        'message': 'Invalid request method'
    })

@app.route('/resume/<resume_id>')
def resume_detail(resume_id):
    resume = db.get_resume(resume_id)
    if resume:
        return render_template('resume_detail.html', resume=resume)
    flash('Resume not found')
    return redirect(url_for('index'))

@app.route('/match', methods=['GET', 'POST'])
def match():
    if request.method == 'POST':
        job_description = request.form.get('job_description')
        if not job_description:
            flash('Please provide a job description')
            return redirect(request.url)
        
        try:
            required_skills = request.form.get('required_skills', '').split(',')
            required_skills = [s.strip() for s in required_skills if s.strip()]
            min_years = request.form.get('min_years')
            min_years = int(min_years) if min_years else None
            min_cgpa = request.form.get('min_cgpa')
            min_cgpa = float(min_cgpa) if min_cgpa else None
            matched_resumes = workflow.match_resumes(job_description)
            return render_template(
                'match_result.html',
                candidates=matched_resumes,
                required_skills=required_skills,
                min_years=min_years,
                min_cgpa=min_cgpa
            )
        except Exception as e:
            flash(f"An error occurred: {str(e)}")
            return redirect(request.url)
        resumes = filter_agent.db.get_all_resumes()
        try:
            matched = matcher_agent.rank_candidates(
                resumes, job_description, required_skills, min_years, min_cgpa)
            return render_template('match.html', resumes=matched, job_description=job_description)
        except Exception as e:
            return render_template('match.html', resumes=[], job_description=job_description, error=f"Error matching resumes: {e}")
        except Exception as e:
            return render_template('match.html', resumes=[], job_description=job_description, error=f"Error matching resumes: {e}")
    else:
        return render_template('match.html', resumes=[], job_description='')

@app.route('/api/filter')
def filter_resumes():
    skills = request.args.get('skills', '').split(',')
    skills = [s.strip() for s in skills if s.strip()]
    min_years = request.args.get('min_years')
    min_years = int(min_years) if min_years else None
    min_cgpa = request.args.get('min_cgpa')
    min_cgpa = float(min_cgpa) if min_cgpa else None

    resumes = filter_agent.db.get_all_resumes()
    results = []
    for resume in resumes:
        # Skills filter: match if any skill substring matches (case-insensitive)
        if skills:
            candidate_skills = [str(s).strip().lower() for s in resume.get('skills', []) if s]
            if not any(any(skill in cs for cs in candidate_skills) for skill in [sk.lower() for sk in skills]):
                continue
        # Experience filter
        if min_years is not None:
            if int(resume.get('total_years_experience', resume.get('experience', 0)) or 0) < min_years:
                continue
        # CGPA filter
        if min_cgpa is not None:
            if float(resume.get('cgpa', 0.0) or 0.0) < min_cgpa:
                continue
        results.append(resume)
    return jsonify(results)

@app.route('/database')
def view_database():
    resumes = db.get_all_resumes()
    return render_template('database.html', resumes=resumes)

if __name__ == '__main__':
    app.run(debug=True)
