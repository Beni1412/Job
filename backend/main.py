"""
AI Career Advisor v2.0 — FastAPI Backend
"""

import os
import sys
import json
from pathlib import Path
from typing import Optional, List

import uvicorn
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, EmailStr
import io

from cv_analyzer import CVAnalyzer
from job_matcher import JobMatcher
from course_recommender import CourseRecommender
from database import get_supabase
from auth import hash_password, verify_password, create_access_token, get_current_user
from cv_builder import build_resume_pdf

# ─── App Setup ────────────────────────────────────────────────────────────────
app = FastAPI(
    title="AI Career Advisor API v2",
    description="Career platform with auth, CV builder, and job matching",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Load AI Services ─────────────────────────────────────────────────────────
print("[STARTUP] Loading AI Career Advisor v2 services...")
analyzer   = CVAnalyzer()
matcher    = JobMatcher()
recommender = CourseRecommender()
print(f"[STARTUP] Skills: {len(analyzer.skills_taxonomy)} | Jobs: {len(matcher.jobs)} | Courses: {len(recommender.courses)}")

# ─── Serve Frontend ──────────────────────────────────────────────────────────
FRONTEND_DIR = Path(__file__).parent.parent / "frontend"

@app.get("/")
async def serve_index():
    return FileResponse(str(FRONTEND_DIR / "index.html"))

@app.get("/auth")
async def serve_auth():
    return FileResponse(str(FRONTEND_DIR / "auth.html"))

@app.get("/dashboard")
async def serve_dashboard():
    return FileResponse(str(FRONTEND_DIR / "dashboard.html"))

@app.get("/builder")
async def serve_builder():
    return FileResponse(str(FRONTEND_DIR / "builder.html"))

@app.get("/style.css")
async def serve_css():
    return FileResponse(str(FRONTEND_DIR / "style.css"), media_type="text/css")

@app.get("/app.js")
async def serve_js():
    return FileResponse(str(FRONTEND_DIR / "app.js"), media_type="application/javascript")

@app.get("/auth.js")
async def serve_auth_js():
    return FileResponse(str(FRONTEND_DIR / "auth.js"), media_type="application/javascript")

@app.get("/dashboard.js")
async def serve_dashboard_js():
    return FileResponse(str(FRONTEND_DIR / "dashboard.js"), media_type="application/javascript")

@app.get("/builder.js")
async def serve_builder_js():
    return FileResponse(str(FRONTEND_DIR / "builder.js"), media_type="application/javascript")

# ─── Pydantic Models ──────────────────────────────────────────────────────────
class RegisterRequest(BaseModel):
    email: str
    password: str

class LoginRequest(BaseModel):
    email: str
    password: str

class ProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    title: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    linkedin: Optional[str] = None
    github: Optional[str] = None
    about_me: Optional[str] = None

class SkillCreate(BaseModel):
    skill_name: str
    category: Optional[str] = "technical"
    level: Optional[str] = "intermediate"

class ExperienceCreate(BaseModel):
    company: str
    title: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    is_current: Optional[bool] = False
    description: Optional[str] = None

class EducationCreate(BaseModel):
    institution: str
    degree: Optional[str] = None
    field: Optional[str] = None
    grad_year: Optional[str] = None
    gpa: Optional[str] = None

class TextAnalysisRequest(BaseModel):
    text: str
    top_jobs: Optional[int] = 8
    top_courses: Optional[int] = 6

# ─── Health ───────────────────────────────────────────────────────────────────
@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "version": "2.0.0",
        "skills_loaded": len(analyzer.skills_taxonomy),
        "jobs_loaded": len(matcher.jobs),
        "courses_loaded": len(recommender.courses)
    }

@app.get("/api/stats")
async def get_stats():
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
    }

# ─── AUTH ROUTES ─────────────────────────────────────────────────────────────
@app.post("/api/auth/register")
async def register(req: RegisterRequest):
    db = get_supabase()
    email = req.email.strip().lower()

    if len(req.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")

    # Check if email already exists
    existing = db.table("users").select("id").eq("email", email).execute()
    if existing.data:
        raise HTTPException(status_code=409, detail="Email already registered")

    # Create user
    pw_hash = hash_password(req.password)
    result = db.table("users").insert({"email": email, "password_hash": pw_hash}).execute()
    user = result.data[0]

    # Create empty profile
    db.table("user_profiles").insert({"user_id": user["id"]}).execute()

    token = create_access_token(user["id"], email)
    return {"access_token": token, "token_type": "bearer", "email": email}


@app.post("/api/auth/login")
async def login(req: LoginRequest):
    db = get_supabase()
    email = req.email.strip().lower()

    result = db.table("users").select("*").eq("email", email).execute()
    if not result.data:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    user = result.data[0]
    if not verify_password(req.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token(user["id"], email)
    return {"access_token": token, "token_type": "bearer", "email": email}


# ─── PROFILE ROUTES ───────────────────────────────────────────────────────────
@app.get("/api/profile")
async def get_profile(current_user: dict = Depends(get_current_user)):
    db = get_supabase()
    user_id = current_user["sub"]
    result = db.table("user_profiles").select("*").eq("user_id", user_id).execute()
    if not result.data:
        return {}
    return result.data[0]


@app.put("/api/profile")
async def update_profile(data: ProfileUpdate, current_user: dict = Depends(get_current_user)):
    db = get_supabase()
    user_id = current_user["sub"]
    update_data = {k: v for k, v in data.dict().items() if v is not None}
    result = db.table("user_profiles").update(update_data).eq("user_id", user_id).execute()
    return result.data[0] if result.data else {}


# ─── SKILLS ROUTES ────────────────────────────────────────────────────────────
@app.get("/api/skills")
async def get_skills(current_user: dict = Depends(get_current_user)):
    db = get_supabase()
    user_id = current_user["sub"]
    result = db.table("user_skills").select("*").eq("user_id", user_id).order("created_at").execute()
    return result.data


@app.post("/api/skills")
async def add_skill(skill: SkillCreate, current_user: dict = Depends(get_current_user)):
    db = get_supabase()
    user_id = current_user["sub"]
    result = db.table("user_skills").insert({
        "user_id": user_id,
        "skill_name": skill.skill_name.strip(),
        "category": skill.category,
        "level": skill.level,
    }).execute()
    return result.data[0]


@app.delete("/api/skills/{skill_id}")
async def delete_skill(skill_id: str, current_user: dict = Depends(get_current_user)):
    db = get_supabase()
    user_id = current_user["sub"]
    db.table("user_skills").delete().eq("id", skill_id).eq("user_id", user_id).execute()
    return {"deleted": skill_id}


# ─── EXPERIENCE ROUTES ────────────────────────────────────────────────────────
@app.get("/api/experience")
async def get_experience(current_user: dict = Depends(get_current_user)):
    db = get_supabase()
    user_id = current_user["sub"]
    result = db.table("user_experience").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
    return result.data


@app.post("/api/experience")
async def add_experience(exp: ExperienceCreate, current_user: dict = Depends(get_current_user)):
    db = get_supabase()
    user_id = current_user["sub"]
    result = db.table("user_experience").insert({
        "user_id": user_id,
        **exp.dict()
    }).execute()
    return result.data[0]


@app.delete("/api/experience/{exp_id}")
async def delete_experience(exp_id: str, current_user: dict = Depends(get_current_user)):
    db = get_supabase()
    user_id = current_user["sub"]
    db.table("user_experience").delete().eq("id", exp_id).eq("user_id", user_id).execute()
    return {"deleted": exp_id}


# ─── EDUCATION ROUTES ─────────────────────────────────────────────────────────
@app.get("/api/education")
async def get_education(current_user: dict = Depends(get_current_user)):
    db = get_supabase()
    user_id = current_user["sub"]
    result = db.table("user_education").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
    return result.data


@app.post("/api/education")
async def add_education(edu: EducationCreate, current_user: dict = Depends(get_current_user)):
    db = get_supabase()
    user_id = current_user["sub"]
    result = db.table("user_education").insert({
        "user_id": user_id,
        **edu.dict()
    }).execute()
    return result.data[0]


@app.delete("/api/education/{edu_id}")
async def delete_education(edu_id: str, current_user: dict = Depends(get_current_user)):
    db = get_supabase()
    user_id = current_user["sub"]
    db.table("user_education").delete().eq("id", edu_id).eq("user_id", user_id).execute()
    return {"deleted": edu_id}


# ─── CV DOWNLOAD ──────────────────────────────────────────────────────────────
@app.get("/api/cv/download")
async def download_cv(current_user: dict = Depends(get_current_user)):
    db = get_supabase()
    user_id = current_user["sub"]
    email   = current_user.get("email", "")

    profile_res = db.table("user_profiles").select("*").eq("user_id", user_id).execute()
    skills_res  = db.table("user_skills").select("*").eq("user_id", user_id).execute()
    exp_res     = db.table("user_experience").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
    edu_res     = db.table("user_education").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()

    profile = profile_res.data[0] if profile_res.data else {}
    profile["email"] = email

    pdf_bytes = build_resume_pdf(
        profile=profile,
        skills=skills_res.data or [],
        experience=exp_res.data or [],
        education=edu_res.data or [],
    )

    name = (profile.get("full_name") or "resume").replace(" ", "_")
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{name}_resume.pdf"'}
    )


# ─── ANALYZE ROUTES (original, now supports saved skills too) ─────────────────
@app.post("/api/analyze/upload")
async def analyze_cv_upload(file: UploadFile = File(...)):
    ext = Path(file.filename).suffix.lower()
    if ext not in [".pdf", ".txt"]:
        raise HTTPException(status_code=400, detail="Only PDF or TXT supported")
    content = await file.read()
    cv_text = analyzer.extract_text_from_pdf(content) if ext == ".pdf" else content.decode("utf-8", errors="ignore")
    if not cv_text or len(cv_text.strip()) < 30:
        raise HTTPException(status_code=422, detail="Could not extract text from file")
    return await _run_analysis(cv_text)


@app.post("/api/analyze/text")
async def analyze_cv_text(request: TextAnalysisRequest):
    if not request.text or len(request.text.strip()) < 30:
        raise HTTPException(status_code=400, detail="CV text too short")
    return await _run_analysis(request.text, request.top_jobs, request.top_courses)


@app.post("/api/analyze/saved-skills")
async def analyze_saved_skills(current_user: dict = Depends(get_current_user)):
    """Analyze jobs/courses using skills already saved in user's profile"""
    db = get_supabase()
    user_id = current_user["sub"]
    skills_res = db.table("user_skills").select("skill_name").eq("user_id", user_id).execute()
    skills = [s["skill_name"] for s in (skills_res.data or [])]
    if not skills:
        raise HTTPException(status_code=400, detail="No skills saved yet. Add skills in your profile first.")
    job_matches = matcher.find_matches(user_skills=skills, top_n=8)
    skill_gap   = matcher.get_skill_gap_analysis(skills, job_matches)
    missing     = [i["skill"] for i in skill_gap.get("top_missing_skills", [])]
    course_recs = recommender.recommend(missing_skills=missing, all_skills=skills, top_n=6)
    return {
        "success": True,
        "skills_used": skills,
        "job_recommendations": job_matches,
        "course_recommendations": course_recs,
        "skill_gap": skill_gap,
    }


async def _run_analysis(cv_text: str, top_jobs: int = 8, top_courses: int = 6):
    cv_analysis  = analyzer.analyze(cv_text)
    if "error" in cv_analysis:
        raise HTTPException(status_code=422, detail=cv_analysis["error"])
    skills       = cv_analysis.get("all_skills", [])
    job_matches  = matcher.find_matches(user_skills=skills, top_n=top_jobs,
                                        career_category=cv_analysis.get("career_category"))
    skill_gap    = matcher.get_skill_gap_analysis(skills, job_matches)
    missing      = [i["skill"] for i in skill_gap.get("top_missing_skills", [])]
    course_recs  = recommender.recommend(missing_skills=missing, all_skills=skills, top_n=top_courses)
    return {
        "success": True,
        "cv_analysis": cv_analysis,
        "job_recommendations": job_matches,
        "course_recommendations": course_recs,
        "skill_gap": skill_gap,
        "cv_preview": cv_text[:500] + "..." if len(cv_text) > 500 else cv_text
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)
