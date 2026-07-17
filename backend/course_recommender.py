"""
Course Recommender — Matches skill gaps to courses from Udemy + Coursera datasets
"""

import json
import re
from pathlib import Path
from typing import List, Dict
from collections import defaultdict

DATA_DIR = Path(__file__).parent / "data"

# Skill → Course subject/keyword mapping
SKILL_TO_SUBJECT = {
    "python": ["python", "programming", "data science", "machine learning", "automation"],
    "machine learning": ["machine learning", "deep learning", "ai", "neural network"],
    "deep learning": ["deep learning", "neural network", "tensorflow", "pytorch"],
    "sql": ["sql", "database", "data analysis", "mysql", "postgresql"],
    "data science": ["data science", "data analysis", "statistics", "machine learning"],
    "javascript": ["javascript", "web development", "react", "node", "frontend"],
    "react": ["react", "javascript", "frontend", "web development"],
    "node.js": ["node", "javascript", "backend", "web development"],
    "aws": ["aws", "cloud", "amazon web services", "devops"],
    "docker": ["docker", "kubernetes", "devops", "containerization"],
    "tensorflow": ["tensorflow", "machine learning", "deep learning", "keras"],
    "pytorch": ["pytorch", "deep learning", "machine learning"],
    "java": ["java", "programming", "backend", "spring", "android"],
    "excel": ["excel", "spreadsheet", "data analysis", "microsoft office"],
    "tableau": ["tableau", "data visualization", "business intelligence", "power bi"],
    "r": ["r programming", "statistics", "data science", "data analysis"],
    "data analysis": ["data analysis", "excel", "sql", "python", "tableau"],
    "cybersecurity": ["cybersecurity", "security", "ethical hacking", "network security"],
    "figma": ["figma", "ui design", "ux design", "web design"],
    "android": ["android", "mobile development", "kotlin", "java"],
    "ios": ["ios", "swift", "mobile development", "apple"],
    "flutter": ["flutter", "dart", "mobile development", "cross-platform"],
    "spark": ["apache spark", "big data", "pyspark", "data engineering"],
    "git": ["git", "version control", "github", "devops"],
    "c++": ["c++", "programming", "game development", "systems programming"],
    "marketing": ["marketing", "digital marketing", "seo", "social media"],
    "communication": ["communication", "public speaking", "presentation", "leadership"],
    "project management": ["project management", "agile", "scrum", "pmp"],
    "accounting": ["accounting", "finance", "bookkeeping", "financial analysis"],
    "nlp": ["natural language processing", "nlp", "text mining", "python"],
    "devops": ["devops", "ci/cd", "docker", "kubernetes", "jenkins"],
}


class CourseRecommender:
    def __init__(self):
        self.courses: List[Dict] = []
        self._load_courses()
    
    def _load_courses(self):
        """Load courses from preprocessed JSON"""
        courses_file = DATA_DIR / "courses_index.json"
        if courses_file.exists():
            with open(courses_file, "r", encoding="utf-8") as f:
                self.courses = json.load(f)
        else:
            self.courses = self._get_fallback_courses()
    
    def _get_fallback_courses(self) -> List[Dict]:
        """Fallback courses for demo"""
        return [
            {"id": "u1", "title": "Python for Everybody", "platform": "Coursera",
             "url": "https://www.coursera.org/specializations/python", "price": 0,
             "subscribers": 1500000, "rating": 4.8, "level": "Beginner",
             "subject": "Programming", "keywords": ["python", "programming", "beginner"]},
            {"id": "u2", "title": "Machine Learning A-Z", "platform": "Udemy",
             "url": "https://www.udemy.com/course/machinelearning/", "price": 15,
             "subscribers": 900000, "rating": 4.5, "level": "All Levels",
             "subject": "Machine Learning", "keywords": ["machine learning", "python", "r"]},
            {"id": "u3", "title": "The Complete SQL Bootcamp", "platform": "Udemy",
             "url": "https://www.udemy.com/course/the-complete-sql-bootcamp-go-from-zero-to-hero/", "price": 15,
             "subscribers": 750000, "rating": 4.7, "level": "Beginner",
             "subject": "Databases", "keywords": ["sql", "database", "postgresql"]},
            {"id": "u4", "title": "React - The Complete Guide", "platform": "Udemy",
             "url": "https://www.udemy.com/course/react-the-complete-guide-incl-redux/", "price": 15,
             "subscribers": 820000, "rating": 4.6, "level": "All Levels",
             "subject": "Web Development", "keywords": ["react", "javascript", "redux"]},
            {"id": "u5", "title": "Docker and Kubernetes: The Complete Guide", "platform": "Udemy",
             "url": "https://www.udemy.com/course/docker-and-kubernetes-the-complete-guide/", "price": 15,
             "subscribers": 500000, "rating": 4.6, "level": "Intermediate",
             "subject": "DevOps", "keywords": ["docker", "kubernetes", "devops"]},
            {"id": "u6", "title": "Deep Learning Specialization", "platform": "Coursera",
             "url": "https://www.coursera.org/specializations/deep-learning", "price": 0,
             "subscribers": 800000, "rating": 4.9, "level": "Intermediate",
             "subject": "Deep Learning", "keywords": ["deep learning", "tensorflow", "neural network"]},
        ]
    
    def _compute_relevance(self, course: Dict, target_keywords: List[str]) -> float:
        """Compute course relevance score for target keywords"""
        course_text = (
            str(course.get("title", "")).lower() + " " +
            str(course.get("subject", "")).lower() + " " +
            " ".join(str(k).lower() for k in course.get("keywords", []))
        )
        
        score = 0.0
        for kw in target_keywords:
            kw_lower = kw.lower()
            if kw_lower in course_text:
                # Exact match in title is more valuable
                if kw_lower in course.get("title", "").lower():
                    score += 3.0
                else:
                    score += 1.0
        
        return score
    
    def _popularity_bonus(self, course: Dict) -> float:
        """Normalize popularity score"""
        subs = course.get("subscribers", 0) or 0
        rating = course.get("rating") or 0
        
        # Log scale for subscribers
        import math
        pop_score = math.log10(max(subs, 1)) / 7  # Normalize to ~0-1
        rating_score = float(rating) / 5.0 if rating else 0.5
        
        return pop_score * 0.3 + rating_score * 0.7
    
    def recommend(self, missing_skills: List[str], all_skills: List[str], 
                  top_n: int = 6) -> List[Dict]:
        """
        Recommend courses based on skill gaps and current skills
        """
        if not self.courses:
            return []
        
        # Build target keywords from missing skills
        target_keywords = []
        for skill in missing_skills:
            skill_lower = skill.lower()
            target_keywords.append(skill_lower)
            # Add related keywords
            for key, related in SKILL_TO_SUBJECT.items():
                if key in skill_lower or skill_lower in key:
                    target_keywords.extend(related)
        
        # Remove duplicates while preserving order
        seen = set()
        target_keywords = [k for k in target_keywords if not (k in seen or seen.add(k))]
        
        # Score all courses
        scored = []
        for course in self.courses:
            title = str(course.get("title", ""))
            if not title or title == "nan":
                continue
            
            relevance = self._compute_relevance(course, target_keywords)
            if relevance > 0:
                popularity = self._popularity_bonus(course)
                final_score = relevance * 0.7 + popularity * 0.3
                
                scored.append({
                    **course,
                    "relevance_score": round(relevance, 2),
                    "final_score": round(final_score, 3)
                })
        
        # Sort by final score
        scored.sort(key=lambda x: x["final_score"], reverse=True)
        
        # Diversity: avoid same platform dominating
        platform_counts = defaultdict(int)
        diverse = []
        for course in scored:
            platform = course.get("platform", "Unknown")
            if platform_counts[platform] < 4:  # Max 4 from same platform
                platform_counts[platform] += 1
                diverse.append(course)
            if len(diverse) >= top_n:
                break
        
        # If not enough courses found, fill with top courses by popularity
        if len(diverse) < top_n:
            all_scored = []
            for course in self.courses:
                title = str(course.get("title", ""))
                if title and title != "nan":
                    pop = self._popularity_bonus(course)
                    all_scored.append({**course, "final_score": pop * 0.1})
            all_scored.sort(key=lambda x: x["final_score"], reverse=True)
            
            existing_ids = {c.get("id") for c in diverse}
            for course in all_scored:
                if course.get("id") not in existing_ids:
                    diverse.append(course)
                    if len(diverse) >= top_n:
                        break
        
        return diverse[:top_n]
