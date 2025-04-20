# Resume Matcher

A production-ready web application that helps recruiters match resumes with job descriptions using AI.

## Features

- Upload multiple PDF resumes via drag-and-drop interface
- Parse resumes into structured JSON using hybrid approach (LLM + NLP)
- Generate professional summaries for candidates
- Store parsed data in Firebase Firestore
- Filter candidates by skills, experience, and CGPA
- Match resumes against job descriptions with AI scoring
- Modern Bootstrap UI with responsive design

## Tech Stack

- Python 3.10 with Flask 3.0
- PyMuPDF for PDF processing
- spaCy for NER
- LangGraph + LangChain for agent orchestration
- Together.ai (Llama-3.3-70B) for AI features
- Firebase Firestore for storage
- Bootstrap 5 for UI
- Docker for containerization

## Quick Start

1. Clone the repository
2. Create a `.env` file with:
   ```
   TOGETHER_API_KEY=your_api_key
   GOOGLE_APPLICATION_CREDENTIALS=path/to/serviceAccountKey.json
   ```
3. Build and run with Docker:
   ```bash
   docker build -t resume-matcher .
   docker run -p 5000:5000 -v $(pwd)/.env:/app/.env resume-matcher
   ```
4. Visit http://localhost:5000

## Development Setup

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # or venv\Scripts\activate on Windows
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   python -m spacy download en_core_web_sm
   ```

3. Run the development server:
   ```bash
   flask run
   ```

## Project Structure

```
resume_matcher/
├── app.py                  # Flask application
├── requirements.txt        # Python dependencies
├── Dockerfile             # Container configuration
├── .env                   # Environment variables
├── agents/                # AI agents
├── workflows/             # LangGraph workflows
├── utils/                # Helper utilities
├── templates/            # Jinja2 templates
└── static/              # CSS and other assets
```

## License

MIT License
