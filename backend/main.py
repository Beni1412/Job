"""
AI Career Advisor — FastAPI Backend
"""

import os
import json
from pathlib import Path
from typing import Optional, List

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from cv_analyzer import CVAnalyzer
from job_matcher import JobMatcher
from course_recommender import CourseRecommender

# ─── App Setup ────────────────────────────────────────────────────────────────
app = FastAPI(
    title="AI Career Advisor API",
    description="Analyzes CVs and recommends careers + courses using real job market data",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Initialize Services ─────────────────────────────────────────────────────
print("[STARTUP] Loading AI Career Advisor services...")
analyzer = CVAnalyzer()
matcher = JobMatcher()
recommender = CourseRecommender()
print(f"[STARTUP] ✓ Skills taxonomy: {len(analyzer.skills_taxonomy)} skills")
print(f"[STARTUP] ✓ Jobs index: {len(matcher.jobs)} jobs")
print(f"[STARTUP] ✓ Courses index: {len(recommender.courses)} courses")

# ─── Serve Frontend ──────────────────────────────────────────────────────────
FRONTEND_DIR = Path(__file__).parent.parent / "frontend"

@app.get("/")
async def serve_frontend():
    if FRONTEND_DIR.exists():
        return FileResponse(str(FRONTEND_DIR / "index.html"))
    return {"message": "Frontend not found"}

@app.get("/style.css")
async def serve_css():
    return FileResponse(str(FRONTEND_DIR / "style.css"), media_type="text/css")

@app.get("/app.js")
async def serve_js():
    return FileResponse(str(FRONTEND_DIR / "app.js"), media_type="application/javascript")

if FRONTEND_DIR.exists():
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIR)), name="assets")

# ─── Models ───────────────────────────────────────────────────────────────────
class TextAnalysisRequest(BaseModel):
    text: str
    top_jobs: Optional[int] = 8
    top_courses: Optional[int] = 6

class AnalysisResponse(BaseModel):
    success: bool
    cv_analysis: dict
    job_recommendations: list
    course_recommendations: list
    skill_gap: dict

# ─── API Routes ───────────────────────────────────────────────────────────────

@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "skills_loaded": len(analyzer.skills_taxonomy),
        "jobs_loaded": len(matcher.jobs),
        "courses_loaded": len(recommender.courses)
    }

@app.post("/api/analyze/upload")
async def analyze_cv_upload(file: UploadFile = File(...)):
    """Analyze CV from uploaded PDF file"""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    
    ext = Path(file.filename).suffix.lower()
    allowed = [".pdf", ".txt", ".doc"]
    
    if ext not in allowed:
        raise HTTPException(
            status_code=400, 
            detail=f"File type '{ext}' not supported. Please upload PDF or TXT."
        )
    
    content = await file.read()
    
    if ext == ".pdf":
        cv_text = analyzer.extract_text_from_pdf(content)
    else:
        cv_text = content.decode("utf-8", errors="ignore")
    
    if not cv_text or len(cv_text.strip()) < 30:
        raise HTTPException(status_code=422, detail="Could not extract text from file")
    
    return await _run_analysis(cv_text)

@app.post("/api/analyze/text")
async def analyze_cv_text(request: TextAnalysisRequest):
    """Analyze CV from raw text input"""
    if not request.text or len(request.text.strip()) < 30:
        raise HTTPException(status_code=400, detail="CV text is too short")
    
    return await _run_analysis(request.text, request.top_jobs, request.top_courses)

async def _run_analysis(cv_text: str, top_jobs: int = 8, top_courses: int = 6) -> dict:
    """Core analysis pipeline"""
    
    # Step 1: Analyze CV
    cv_analysis = analyzer.analyze(cv_text)
    
    if "error" in cv_analysis:
        raise HTTPException(status_code=422, detail=cv_analysis["error"])
    
    extracted_skills = cv_analysis.get("all_skills", [])
    career_category = cv_analysis.get("career_category", "")
    
    # Step 2: Find matching jobs
    job_matches = matcher.find_matches(
        user_skills=extracted_skills,
        top_n=top_jobs,
        career_category=career_category
    )
    
    # Step 3: Skill gap analysis
    skill_gap = matcher.get_skill_gap_analysis(extracted_skills, job_matches)
    missing_skills = [item["skill"] for item in skill_gap.get("top_missing_skills", [])]
    
    # Step 4: Course recommendations
    course_recs = recommender.recommend(
        missing_skills=missing_skills,
        all_skills=extracted_skills,
        top_n=top_courses
    )
    
    # Clean up course data for response
    clean_courses = []
    for course in course_recs:
        clean_courses.append({
            "id": course.get("id", ""),
            "title": course.get("title", ""),
            "platform": course.get("platform", ""),
            "url": course.get("url", ""),
            "level": course.get("level", ""),
            "rating": course.get("rating"),
            "subscribers": course.get("subscribers", 0),
            "is_paid": course.get("is_paid", True),
            "price": course.get("price", 0),
            "subject": course.get("subject", ""),
            "relevance_score": course.get("relevance_score", 0),
        })
    
    return {
        "success": True,
        "cv_analysis": cv_analysis,
        "job_recommendations": job_matches,
        "course_recommendations": clean_courses,
        "skill_gap": skill_gap,
        "cv_preview": cv_text[:500] + "..." if len(cv_text) > 500 else cv_text
    }

@app.get("/api/jobs")
async def get_jobs(limit: int = 20, offset: int = 0):
    """Get paginated job listings"""
    jobs = matcher.jobs[offset:offset + limit]
    return {
        "jobs": jobs,
        "total": len(matcher.jobs),
        "offset": offset,
        "limit": limit
    }

@app.get("/api/courses")
async def get_courses(limit: int = 20):
    """Get course listings"""
    return {
        "courses": recommender.courses[:limit],
        "total": len(recommender.courses)
    }

@app.get("/api/stats")
async def get_stats():
    """Get dataset statistics"""
    DATA_DIR = Path(__file__).parent / "data"
    categories_file = DATA_DIR / "career_categories.json"
    
    categories = {}
    if categories_file.exists():
        with open(categories_file, "r") as f:
            categories = json.load(f)
    
    return {
        "total_jobs": len(matcher.jobs),
        "total_courses": len(recommender.courses),
        "total_skills": len(analyzer.skills_taxonomy),
        "career_categories": len(categories),
        "datasets": ["LinkedIn Jobs", "Udemy Courses", "Coursera", "Resume Dataset"]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)
