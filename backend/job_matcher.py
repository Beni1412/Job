"""
Job Matcher — Matches extracted CV skills to job postings with improved accuracy
"""

import json
import re
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from collections import Counter

DATA_DIR = Path(__file__).parent / "data"

# ─── Skill Aliases — normalize variants ke bentuk canonical ──────────────────
SKILL_ALIASES = {
    # Python ecosystem
    "sklearn": "scikit-learn", "sci-kit learn": "scikit-learn",
    "scikit learn": "scikit-learn",
    # JavaScript
    "node": "node.js", "nodejs": "node.js", "node js": "node.js",
    "reactjs": "react", "react js": "react",
    "vuejs": "vue.js", "vue js": "vue.js",
    "angularjs": "angular",
    "ts": "typescript",
    # Database
    "postgres": "postgresql", "postgre sql": "postgresql",
    "mongo": "mongodb", "mongo db": "mongodb",
    "mssql": "sql server", "ms sql": "sql server",
    # Cloud
    "amazon web services": "aws", "amazon aws": "aws",
    "google cloud": "gcp", "google cloud platform": "gcp",
    "microsoft azure": "azure",
    "k8s": "kubernetes", "kube": "kubernetes",
    # ML/AI
    "ml": "machine learning",
    "dl": "deep learning",
    "computer vision": "computer vision",  # keep as-is
    "nlp": "natural language processing",
    "llm": "large language models",
    "tf": "tensorflow",
    # C family
    "c plus plus": "c++", "cplusplus": "c++",
    "c sharp": "c#", "csharp": "c#",
    # Other
    "powerbi": "power bi", "power-bi": "power bi",
    "gitlab ci": "gitlab", "github actions": "github",
    "rest": "rest api", "restful": "rest api",
    "tableau software": "tableau",
}

# ─── Category → job title keywords (untuk category-aware boosting) ────────────
CATEGORY_JOB_KEYWORDS = {
    "Data Science": ["data scientist", "ml engineer", "machine learning", "ai engineer",
                     "research scientist", "data analyst", "computer vision", "nlp engineer"],
    "Software Engineering": ["software engineer", "software developer", "backend developer",
                              "frontend developer", "full stack", "fullstack", "web developer",
                              "application developer", "platform engineer"],
    "Data Engineering": ["data engineer", "etl developer", "data pipeline", "analytics engineer",
                          "big data", "spark developer"],
    "DevOps/Cloud": ["devops", "cloud engineer", "sre", "site reliability", "platform engineer",
                     "infrastructure engineer", "cloud architect"],
    "Mobile Development": ["mobile developer", "android developer", "ios developer",
                            "flutter developer", "react native"],
    "UX/UI Design": ["ux designer", "ui designer", "product designer", "ux researcher",
                     "interaction designer"],
    "Cybersecurity": ["security engineer", "security analyst", "penetration tester",
                      "infosec", "cyber security", "information security"],
    "Product Management": ["product manager", "product owner", "product lead"],
    "Marketing": ["marketing", "seo specialist", "growth", "digital marketing",
                  "content manager", "social media"],
    "Finance/Accounting": ["financial analyst", "accountant", "finance manager",
                            "investment analyst", "cfo", "controller"],
}


def _normalize_skill(skill: str) -> str:
    """Normalize skill name via alias lookup."""
    s = skill.lower().strip()
    return SKILL_ALIASES.get(s, s)


def _skills_match(user_skill: str, job_skill: str) -> bool:
    """
    Determine if a user skill matches a job skill.
    Uses exact match first, then careful partial match to avoid false positives
    like 'Java' matching 'JavaScript'.
    """
    u = _normalize_skill(user_skill)
    j = _normalize_skill(job_skill)

    # 1. Exact match
    if u == j:
        return True

    # 2. Only do substring match when BOTH sides are long enough
    #    AND the shorter string is at least 60% of the longer string's length
    #    This prevents 'r' matching 'rust', 'java' matching 'javascript', etc.
    min_len = min(len(u), len(j))
    max_len = max(len(u), len(j))

    if min_len < 4:
        return False  # Too short to safely substring-match

    ratio = min_len / max_len
    if ratio < 0.6:
        return False  # One is much longer — too risky

    # Safe to do substring check
    if u in j or j in u:
        return True

    return False


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
            self.jobs = self._get_fallback_jobs()
            self.jobs_loaded = True

    def _get_fallback_jobs(self) -> List[Dict]:
        return [
            {
                "id": "1", "title": "Machine Learning Engineer", "company": "Tech Corp",
                "location": "Remote", "level": "Mid-Senior", "type": "Full-time",
                "skills": ["Python", "TensorFlow", "PyTorch", "Machine Learning",
                           "Deep Learning", "SQL", "scikit-learn"],
                "salary": "$120,000 - $160,000 YEARLY", "url": "#", "source": "Demo"
            },
            {
                "id": "2", "title": "Data Scientist", "company": "Analytics Inc",
                "location": "New York, NY", "level": "Entry Level", "type": "Full-time",
                "skills": ["Python", "R", "Machine Learning", "Statistics",
                           "SQL", "Pandas", "NumPy"],
                "salary": "$90,000 - $130,000 YEARLY", "url": "#", "source": "Demo"
            },
            {
                "id": "3", "title": "Full Stack Developer", "company": "StartupXYZ",
                "location": "San Francisco, CA", "level": "Mid-Senior", "type": "Full-time",
                "skills": ["React", "Node.js", "JavaScript", "TypeScript",
                           "SQL", "Docker", "AWS"],
                "salary": "$110,000 - $150,000 YEARLY", "url": "#", "source": "Demo"
            },
            {
                "id": "4", "title": "Data Engineer", "company": "DataFlow",
                "location": "Austin, TX", "level": "Mid-Senior", "type": "Full-time",
                "skills": ["Python", "Apache Spark", "Kafka", "Airflow",
                           "SQL", "AWS", "dbt"],
                "salary": "$115,000 - $145,000 YEARLY", "url": "#", "source": "Demo"
            },
            {
                "id": "5", "title": "DevOps Engineer", "company": "CloudOps",
                "location": "Remote", "level": "Mid-Senior", "type": "Full-time",
                "skills": ["Docker", "Kubernetes", "AWS", "Terraform",
                           "CI/CD", "Linux", "Python"],
                "salary": "$100,000 - $140,000 YEARLY", "url": "#", "source": "Demo"
            },
        ]

    def _skill_overlap_score(
        self, user_skills: List[str], job_skills: List[str]
    ) -> Tuple[float, List[str], List[str]]:
        """
        Compute skill overlap using fixed matching (no Java/JavaScript false positives).
        Returns: (score 0-1, matched_skills, missing_skills)
        """
        if not user_skills or not job_skills:
            return 0.0, [], list(job_skills)

        matched = []
        missing = []

        for job_skill in job_skills:
            found = any(_skills_match(u, job_skill) for u in user_skills)
            if found:
                matched.append(job_skill)
            else:
                missing.append(job_skill)

        # Jaccard on normalized sets
        u_norm = {_normalize_skill(s) for s in user_skills}
        j_norm = {_normalize_skill(s) for s in job_skills}
        intersection = sum(
            1 for js in j_norm
            if any(_skills_match(us, js) for us in u_norm)
        )
        union = len(u_norm | j_norm)
        jaccard = intersection / union if union > 0 else 0.0

        match_ratio = len(matched) / max(len(job_skills), 1)
        score = (jaccard * 0.4) + (match_ratio * 0.6)   # weight match_ratio more

        return score, matched, missing

    def _category_boost(self, job: Dict, career_category: Optional[str]) -> float:
        """
        Return a boost multiplier (1.0–1.4) if the job matches the detected category.
        This fixes the bug where career_category was accepted but never used.
        """
        if not career_category:
            return 1.0
        title_lower = job.get("title", "").lower()
        kws = CATEGORY_JOB_KEYWORDS.get(career_category, [])
        if any(kw in title_lower for kw in kws):
            return 1.35   # 35% boost for category match
        return 1.0

    def find_matches(
        self, user_skills: List[str], top_n: int = 8,
        career_category: Optional[str] = None
    ) -> List[Dict]:
        """Find top N matching jobs, with career_category boosting."""
        if not user_skills:
            return self.jobs[:top_n]

        scored_jobs = []

        for job in self.jobs:
            job_skills = job.get("skills", [])
            if not job_skills:
                continue

            score, matched, missing = self._skill_overlap_score(user_skills, job_skills)

            if score > 0:
                # Apply category boost — this now ACTUALLY works
                boost = self._category_boost(job, career_category)
                final_score = min(score * boost, 1.0)

                scored_jobs.append({
                    **job,
                    "match_score": round(final_score * 100, 1),
                    "matched_skills": matched,
                    "missing_skills": missing,    # return ALL missing, not just 5
                    "match_percentage": round(len(matched) / max(len(job_skills), 1) * 100, 1),
                    "category_match": boost > 1.0,
                })

        # Sort by match score
        scored_jobs.sort(key=lambda x: x["match_score"], reverse=True)

        # Diversity: avoid identical titles but keep minimum 3 results
        seen_titles = set()
        diverse_jobs = []
        for job in scored_jobs:
            # Use full title for dedup (fixed: was only using first 2 words before)
            title_key = re.sub(r'\s+', ' ', job["title"].lower().strip())
            if title_key not in seen_titles or len(diverse_jobs) < 3:
                seen_titles.add(title_key)
                diverse_jobs.append(job)
            if len(diverse_jobs) >= top_n:
                break

        return diverse_jobs

    def get_skill_gap_analysis(self, user_skills: List[str], top_jobs: List[Dict]) -> Dict:
        """Analyze skill gaps across top matched jobs."""
        all_missing = []
        for job in top_jobs:
            all_missing.extend(job.get("missing_skills", []))

        skill_freq = Counter(all_missing)
        top_missing = [
            {"skill": skill, "demand": count}
            for skill, count in skill_freq.most_common(10)
        ]

        return {
            "top_missing_skills": top_missing,
            "total_unique_missing": len(set(all_missing)),
            "your_skill_count": len(user_skills),
        }
