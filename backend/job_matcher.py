"""
Job Matcher — Matches extracted CV skills to job postings using TF-IDF cosine similarity
"""

import json
import re
import math
from pathlib import Path
from typing import List, Dict, Tuple
from collections import Counter

DATA_DIR = Path(__file__).parent / "data"

class JobMatcher:
    def __init__(self):
        self.jobs: List[Dict] = []
        self.jobs_loaded = False
        self._load_jobs()
    
    def _load_jobs(self):
        """Load jobs index from preprocessed JSON"""
        jobs_file = DATA_DIR / "jobs_index.json"
        if jobs_file.exists():
            with open(jobs_file, "r", encoding="utf-8") as f:
                self.jobs = json.load(f)
            self.jobs_loaded = True
        else:
            # Fallback sample jobs for demo
            self.jobs = self._get_fallback_jobs()
            self.jobs_loaded = True
    
    def _get_fallback_jobs(self) -> List[Dict]:
        """Fallback job data if preprocessing hasn't run yet"""
        return [
            {
                "id": "1", "title": "Machine Learning Engineer", "company": "Tech Corp",
                "location": "Remote", "level": "Mid-Senior", "type": "Full-time",
                "skills": ["Python", "TensorFlow", "PyTorch", "Machine Learning", "Deep Learning", "SQL"],
                "salary": "$120,000 - $160,000 YEARLY", "url": "#", "source": "Demo"
            },
            {
                "id": "2", "title": "Data Scientist", "company": "Analytics Inc",
                "location": "New York, NY", "level": "Entry Level", "type": "Full-time",
                "skills": ["Python", "R", "Machine Learning", "Statistics", "SQL", "Pandas", "NumPy"],
                "salary": "$90,000 - $130,000 YEARLY", "url": "#", "source": "Demo"
            },
            {
                "id": "3", "title": "Full Stack Developer", "company": "StartupXYZ",
                "location": "San Francisco, CA", "level": "Mid-Senior", "type": "Full-time",
                "skills": ["React", "Node.js", "JavaScript", "TypeScript", "SQL", "Docker", "AWS"],
                "salary": "$110,000 - $150,000 YEARLY", "url": "#", "source": "Demo"
            },
            {
                "id": "4", "title": "Data Engineer", "company": "DataFlow",
                "location": "Austin, TX", "level": "Mid-Senior", "type": "Full-time",
                "skills": ["Python", "Apache Spark", "Kafka", "Airflow", "SQL", "AWS", "dbt"],
                "salary": "$115,000 - $145,000 YEARLY", "url": "#", "source": "Demo"
            },
            {
                "id": "5", "title": "DevOps Engineer", "company": "CloudOps",
                "location": "Remote", "level": "Mid-Senior", "type": "Full-time",
                "skills": ["Docker", "Kubernetes", "AWS", "Terraform", "CI/CD", "Linux", "Python"],
                "salary": "$100,000 - $140,000 YEARLY", "url": "#", "source": "Demo"
            }
        ]
    
    def _jaccard_similarity(self, set1: set, set2: set) -> float:
        """Compute Jaccard similarity between two skill sets"""
        if not set1 or not set2:
            return 0.0
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        return intersection / union if union > 0 else 0.0
    
    def _skill_overlap_score(self, user_skills: List[str], job_skills: List[str]) -> Tuple[float, List[str], List[str]]:
        """
        Compute skill overlap with matching and missing skills
        Returns: (score, matched_skills, missing_skills)
        """
        user_set = {s.lower() for s in user_skills}
        job_set = {s.lower(): s for s in job_skills}
        
        matched = []
        missing = []
        
        for job_skill_lower, job_skill_orig in job_set.items():
            # Fuzzy match: check if job skill is contained in user skills or vice versa
            found = False
            for user_skill in user_set:
                if (job_skill_lower in user_skill or user_skill in job_skill_lower or
                    job_skill_lower == user_skill):
                    found = True
                    break
            if found:
                matched.append(job_skill_orig)
            else:
                missing.append(job_skill_orig)
        
        jaccard = self._jaccard_similarity(user_set, set(job_set.keys()))
        # Boost score by match ratio
        match_ratio = len(matched) / max(len(job_skills), 1)
        score = (jaccard * 0.5) + (match_ratio * 0.5)
        
        return score, matched, missing[:5]  # Return top 5 missing skills
    
    def find_matches(self, user_skills: List[str], top_n: int = 8, 
                     career_category: str = None) -> List[Dict]:
        """
        Find top N matching jobs for given user skills
        """
        if not user_skills:
            # Return diverse sample jobs if no skills
            return self.jobs[:top_n]
        
        scored_jobs = []
        
        for job in self.jobs:
            job_skills = job.get("skills", [])
            if not job_skills:
                continue
            
            score, matched, missing = self._skill_overlap_score(user_skills, job_skills)
            
            if score > 0:
                scored_jobs.append({
                    **job,
                    "match_score": round(score * 100, 1),
                    "matched_skills": matched,
                    "missing_skills": missing,
                    "match_percentage": round(len(matched) / max(len(job_skills), 1) * 100, 1)
                })
        
        # Sort by match score
        scored_jobs.sort(key=lambda x: x["match_score"], reverse=True)
        
        # Diversity: ensure different titles/companies
        seen_titles = set()
        diverse_jobs = []
        for job in scored_jobs:
            title_key = job["title"].lower().split()[:2]
            title_key = " ".join(title_key)
            if title_key not in seen_titles or len(diverse_jobs) < 3:
                seen_titles.add(title_key)
                diverse_jobs.append(job)
            if len(diverse_jobs) >= top_n:
                break
        
        return diverse_jobs
    
    def get_skill_gap_analysis(self, user_skills: List[str], top_jobs: List[Dict]) -> Dict:
        """Analyze skill gaps across top matched jobs"""
        all_missing = []
        for job in top_jobs:
            all_missing.extend(job.get("missing_skills", []))
        
        skill_freq = Counter(all_missing)
        top_missing = [{"skill": skill, "demand": count} 
                      for skill, count in skill_freq.most_common(10)]
        
        return {
            "top_missing_skills": top_missing,
            "total_unique_missing": len(set(all_missing)),
            "your_skill_count": len(user_skills)
        }
