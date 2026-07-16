# -*- coding: utf-8 -*-
"""
Data Preprocessor for AI Career Advisor
Converts raw datasets â†’ optimized JSON indices for fast querying
Run once: python preprocess.py
"""

import pandas as pd
import json
import os
import re
import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent
DATASETS_DIR = BASE_DIR.parent / "datasets"
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

import sys
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf8', buffering=1)

def log(msg):
    print(f"[PREPROCESS] {msg}", flush=True)

# â”€â”€â”€ 1. SKILLS TAXONOMY â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
def build_skills_taxonomy():
    log("Building skills taxonomy...")
    
    all_skills = set()
    
    # From link/skills.csv
    skills_file = DATASETS_DIR / "link" / "skills.csv"
    if skills_file.exists():
        df = pd.read_csv(skills_file)
        for col in df.columns:
            if 'skill' in col.lower() or 'name' in col.lower():
                all_skills.update(df[col].dropna().str.strip().tolist())
        log(f"  -> link/skills.csv: {len(all_skills)} skills loaded")

    # From skil/job_skills.csv (extract unique skill names)
    job_skills_file = DATASETS_DIR / "skil" / "job_skills.csv"
    if job_skills_file.exists():
        df = pd.read_csv(job_skills_file)
        if 'job_skills' in df.columns:
            for row in df['job_skills'].dropna():
                parts = [s.strip() for s in str(row).split(',')]
                all_skills.update(parts)
        log(f"  -> skil/job_skills.csv: cumulative {len(all_skills)} skills")

    # From link/job_skills.csv (skill_abr)
    link_job_skills = DATASETS_DIR / "link" / "job_skills.csv"
    if link_job_skills.exists():
        df = pd.read_csv(link_job_skills)
        if 'skill_abr' in df.columns:
            all_skills.update(df['skill_abr'].dropna().tolist())

    # Clean skills
    cleaned = []
    for s in all_skills:
        s = str(s).strip()
        if len(s) >= 2 and len(s) <= 60 and not s.startswith('http'):
            cleaned.append(s)

    skills_list = sorted(set(cleaned))
    
    # Replace arrow chars in log
    output = {
        "total": len(skills_list),
        "skills": skills_list
    }
    
    with open(DATA_DIR / "skills_taxonomy.json", "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    log(f"  âœ“ Saved {len(skills_list)} unique skills to skills_taxonomy.json")
    return skills_list


# â”€â”€â”€ 2. JOB INDEX (sampled from LinkedIn datasets) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
def build_jobs_index():
    log("Building jobs index...")
    
    jobs = []
    
    # Primary: skil/job_postings.csv + skil/job_skills.csv (JOIN on job_link)
    postings_file = DATASETS_DIR / "skil" / "job_postings.csv"
    skills_file = DATASETS_DIR / "skil" / "job_skills.csv"
    
    if postings_file.exists() and skills_file.exists():
        df_posts = pd.read_csv(postings_file)
        df_skills = pd.read_csv(skills_file)
        df = df_posts.merge(df_skills, on='job_link', how='left')
        
        for _, row in df.iterrows():
            skills_raw = str(row.get('job_skills', ''))
            skills_list = [s.strip() for s in skills_raw.split(',') if s.strip() and s.strip() != 'nan']
            
            jobs.append({
                "id": str(row.get('job_link', '')).split('/')[-1][:20],
                "title": str(row.get('job_title', 'Unknown')),
                "company": str(row.get('company', 'N/A')),
                "location": str(row.get('job_location', 'N/A')),
                "level": str(row.get('job_level', 'N/A')),
                "type": str(row.get('job_type', 'N/A')),
                "skills": skills_list,
                "url": str(row.get('job_link', '')),
                "source": "LinkedIn (skil)"
            })
        log(f"  â†’ skil dataset: {len(jobs)} jobs")
    
    # Secondary: link/postings.csv (sample 3000 rows since it's 500MB)
    link_postings = DATASETS_DIR / "link" / "postings.csv"
    link_job_skills = DATASETS_DIR / "link" / "job_skills.csv"
    link_skills_ref = DATASETS_DIR / "link" / "skills.csv"
    
    if link_postings.exists():
        log("  Loading link/postings.csv (large file, sampling 3000 rows)...")
        df_link = pd.read_csv(link_postings, nrows=3000, on_bad_lines='skip')
        
        # Load skills reference
        skill_map = {}
        if link_skills_ref.exists():
            df_sref = pd.read_csv(link_skills_ref)
            if 'skill_abr' in df_sref.columns and 'skill_name' in df_sref.columns:
                skill_map = dict(zip(df_sref['skill_abr'], df_sref['skill_name']))
        
        # Load job skills
        job_skill_map = {}
        if link_job_skills.exists():
            df_js = pd.read_csv(link_job_skills)
            for jid, grp in df_js.groupby('job_id'):
                abrs = grp['skill_abr'].tolist()
                job_skill_map[jid] = [skill_map.get(a, a) for a in abrs]
        
        for _, row in df_link.iterrows():
            jid = row.get('job_id')
            skills_desc = str(row.get('skills_desc', ''))
            skills = job_skill_map.get(jid, [])
            
            # Extract skills from description if no structured skills
            if not skills and skills_desc and skills_desc != 'nan':
                skills = [s.strip() for s in skills_desc.split(',') if s.strip()][:15]
            
            # Parse salary
            max_sal = row.get('max_salary')
            min_sal = row.get('min_salary')
            salary_str = "N/A"
            if pd.notna(max_sal) and pd.notna(min_sal):
                period = str(row.get('pay_period', '')).upper()
                salary_str = f"${int(min_sal):,} - ${int(max_sal):,} {period}"
            elif pd.notna(max_sal):
                salary_str = f"Up to ${int(max_sal):,}"
            
            jobs.append({
                "id": str(jid),
                "title": str(row.get('title', 'Unknown')),
                "company": str(row.get('company_name', 'N/A')),
                "location": str(row.get('location', 'N/A')),
                "level": str(row.get('formatted_experience_level', 'N/A')),
                "type": str(row.get('formatted_work_type', 'N/A')),
                "skills": skills[:20],
                "salary": salary_str,
                "url": str(row.get('job_posting_url', '')),
                "source": "LinkedIn"
            })
        log(f"  â†’ link dataset: cumulative {len(jobs)} jobs")
    
    # Remove duplicates by title+company
    seen = set()
    unique_jobs = []
    for j in jobs:
        key = (j['title'].lower()[:30], j['company'].lower()[:20])
        if key not in seen and j['title'] != 'Unknown' and j['title'] != 'nan':
            seen.add(key)
            unique_jobs.append(j)
    
    with open(DATA_DIR / "jobs_index.json", "w", encoding="utf-8") as f:
        json.dump(unique_jobs, f, indent=2, ensure_ascii=False)
    
    log(f"  âœ“ Saved {len(unique_jobs)} unique jobs to jobs_index.json")
    return unique_jobs


# â”€â”€â”€ 3. COURSE INDEX â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
def build_courses_index():
    log("Building courses index...")
    courses = []
    
    # Udemy courses
    udemy_file = DATASETS_DIR / "udemy" / "udemy_courses.csv"
    if udemy_file.exists():
        df = pd.read_csv(udemy_file)
        for _, row in df.iterrows():
            courses.append({
                "id": f"udemy_{row.get('course_id', len(courses))}",
                "title": str(row.get('course_title', '')),
                "platform": "Udemy",
                "url": str(row.get('url', '')),
                "price": row.get('price', 0),
                "is_paid": bool(row.get('is_paid', True)),
                "subscribers": int(row.get('num_subscribers', 0)) if pd.notna(row.get('num_subscribers')) else 0,
                "rating": None,
                "level": str(row.get('level', 'All Levels')),
                "duration": str(row.get('content_duration', '')),
                "subject": str(row.get('subject', '')),
                "keywords": str(row.get('course_title', '')).lower().split()
            })
        log(f"  â†’ Udemy: {len(courses)} courses")
    
    # Coursera courses
    coursera_file = DATASETS_DIR / "course" / "coursea_data.csv"
    if coursera_file.exists():
        df = pd.read_csv(coursera_file)
        for _, row in df.iterrows():
            enrolled_raw = str(row.get('course_students_enrolled', '0'))
            enrolled = 0
            try:
                enrolled_raw = enrolled_raw.replace('k', '000').replace('m', '000000')
                enrolled = int(float(re.sub(r'[^\d.]', '', enrolled_raw)))
            except:
                pass
            
            rating = 0
            try:
                rating = float(str(row.get('course_rating', 0)))
            except:
                pass
            
            courses.append({
                "id": f"coursera_{len(courses)}",
                "title": str(row.get('course_title', '')),
                "platform": "Coursera",
                "url": f"https://www.coursera.org/learn/{str(row.get('course_title','x')).lower().replace(' ','-')[:50]}",
                "price": 0,
                "is_paid": str(row.get('course_Certificate_type','')).upper() in ['SPECIALIZATION'],
                "subscribers": enrolled,
                "rating": rating,
                "level": str(row.get('course_difficulty', 'Beginner')),
                "duration": "",
                "subject": str(row.get('course_organization', '')),
                "keywords": str(row.get('course_title', '')).lower().split()
            })
        log(f"  â†’ Coursera + Udemy total: {len(courses)} courses")
    
    with open(DATA_DIR / "courses_index.json", "w", encoding="utf-8") as f:
        json.dump(courses, f, indent=2, ensure_ascii=False)
    
    log(f"  âœ“ Saved {len(courses)} courses to courses_index.json")
    return courses


# â”€â”€â”€ 4. CAREER CATEGORIES (from Resume dataset) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
def build_career_categories():
    log("Building career categories...")
    
    categories = {}
    
    # From UpdatedResumeDataSet.csv
    updated_file = DATASETS_DIR / "up_resume" / "UpdatedResumeDataSet.csv"
    if updated_file.exists():
        df = pd.read_csv(updated_file)
        for cat in df['Category'].unique():
            subset = df[df['Category'] == cat]['Resume'].dropna()
            # Extract common words as representative skills
            all_text = ' '.join(subset.tolist()).lower()
            categories[cat] = {
                "name": cat,
                "count": len(subset),
                "sample_text": str(subset.iloc[0])[:300] if len(subset) > 0 else ""
            }
        log(f"  â†’ UpdatedResumeDataSet: {len(categories)} categories")
    
    # Add PDF categories from resume/data/data/
    resume_data_dir = DATASETS_DIR / "resume" / "data" / "data"
    if resume_data_dir.exists():
        for cat_dir in resume_data_dir.iterdir():
            if cat_dir.is_dir():
                cat_name = cat_dir.name.replace('-', ' ').title()
                if cat_name not in categories:
                    categories[cat_name] = {
                        "name": cat_name,
                        "count": len(list(cat_dir.glob("*.pdf"))),
                        "sample_text": ""
                    }
        log(f"  â†’ Resume PDFs: total {len(categories)} categories")
    
    with open(DATA_DIR / "career_categories.json", "w", encoding="utf-8") as f:
        json.dump(categories, f, indent=2, ensure_ascii=False)
    
    log(f"  âœ“ Saved {len(categories)} career categories")
    return categories


# â”€â”€â”€ MAIN â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
if __name__ == "__main__":
    log("=" * 50)
    log("AI Career Advisor â€” Data Preprocessor")
    log("=" * 50)
    
    try:
        skills = build_skills_taxonomy()
        log("")
        jobs = build_jobs_index()
        log("")
        courses = build_courses_index()
        log("")
        categories = build_career_categories()
        log("")
        log("=" * 50)
        log(f"âœ… ALL DONE!")
        log(f"   Skills: {len(skills)}")
        log(f"   Jobs:   {len(jobs)}")
        log(f"   Courses:{len(courses)}")
        log(f"   Categories: {len(categories)}")
        log("=" * 50)
    except Exception as e:
        log(f"âŒ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

