"""
CV Analyzer — Extracts skills from CV text using NLP + skill taxonomy matching
"""

import json
import re
import os
from pathlib import Path
from typing import List, Dict, Set
import io

DATA_DIR = Path(__file__).parent / "data"

# Common English stopwords + resume-specific non-skill words
STOPWORDS = {
    'a','an','the','and','or','but','in','on','at','to','for','of','with',
    'by','from','is','are','was','were','be','been','being','have','has',
    'had','do','does','did','will','would','could','should','may','might',
    'shall','can','need','i','my','me','we','our','you','your','he','she',
    'it','they','them','their','this','that','these','those','as','if',
    'then','than','so','yet','both','nor','not','no','yes','well','very',
    'also','just','more','some','any','each','all','both','few','most',
    'other','into','through','during','before','after','above','below',
    'between','out','off','over','under','again','further','once','here',
    'there','when','where','why','how','who','which','what','work','worked',
    'working','experience','years','year','month','strong','good','great',
    # Resume-specific non-skill words to exclude
    'education','computer','science','engineer','senior','junior','lead',
    'manager','analyst','developer','specialist','architect','consultant',
    'associate','director','intern','student','graduate','bachelor','master',
    'data','skills','skill','technical','professional','summary','objective',
    'responsible','ability','knowledge','understanding','familiar','proficient',
    'background','degree','university','college','gpa','graduated','certified',
    'scientist','researcher','position','role','team','project','company',
    'organization','business','industry','customer','service','management',
    'software','systems','solutions','applications','tools','technologies',
    'development','design','analysis','testing','deployment','support',
    'communication','collaboration','presentation','reporting','documentation'
}

# Known professional/technical skill patterns (must match these criteria)
SKILL_MIN_LENGTH = 2
SKILL_MAX_LENGTH = 50
# Skills that are single common words must be in this whitelist
SINGLE_WORD_SKILL_WHITELIST = {
    'python', 'java', 'javascript', 'typescript', 'golang', 'rust', 'scala',
    'kotlin', 'swift', 'ruby', 'php', 'perl', 'matlab', 'r', 'sql', 'nosql',
    'html', 'css', 'xml', 'json', 'yaml', 'bash', 'powershell', 'linux',
    'react', 'angular', 'vue', 'jquery', 'bootstrap', 'flask', 'django',
    'fastapi', 'spring', 'laravel', 'rails', 'nodejs', 'express',
    'tensorflow', 'pytorch', 'keras', 'sklearn', 'pandas', 'numpy', 'scipy',
    'matplotlib', 'seaborn', 'plotly', 'opencv', 'nltk', 'spacy',
    'docker', 'kubernetes', 'jenkins', 'ansible', 'terraform', 'vagrant',
    'aws', 'azure', 'gcp', 'heroku', 'netlify', 'vercel',
    'mysql', 'postgresql', 'mongodb', 'redis', 'cassandra', 'elasticsearch',
    'kafka', 'spark', 'hadoop', 'airflow', 'dbt', 'snowflake', 'tableau',
    'excel', 'powerbi', 'looker', 'grafana', 'kibana', 'prometheus',
    'git', 'github', 'gitlab', 'bitbucket', 'jira', 'confluence', 'slack',
    'figma', 'sketch', 'photoshop', 'illustrator', 'autocad', 'solidworks',
    'pytorch', 'cuda', 'openai', 'langchain', 'huggingface',
    'agile', 'scrum', 'kanban', 'devops', 'mlops', 'dataops',
    'seo', 'crm', 'erp', 'sap', 'salesforce', 'hubspot',
    'accounting', 'auditing', 'budgeting', 'forecasting',
    'negotiation', 'leadership', 'communication', 'mentoring',
    'c', 'c++', 'c#', 'vba', 'matlab', 'labview',
    'oop', 'mvc', 'api', 'rest', 'graphql', 'grpc', 'soap',
    'microservices', 'serverless', 'blockchain', 'solidity',
    'android', 'ios', 'flutter', 'react native', 'xamarin',
    'nlp', 'cv', 'gan', 'lstm', 'bert', 'gpt', 'transformers',
    'statistics', 'regression', 'clustering', 'classification',
    'cybersecurity', 'networking', 'penetration', 'firewalls', 'encryption',
    'project', 'product', 'marketing', 'finance', 'healthcare',
}

class CVAnalyzer:
    def __init__(self):
        self.skills_taxonomy: List[str] = []
        self.skills_lower: Dict[str, str] = {}  # lowercase → original
        self._load_skills()
    
    def _load_skills(self):
        """Load skills taxonomy from preprocessed JSON — filtered to real skills"""
        skills_file = DATA_DIR / "skills_taxonomy.json"
        if skills_file.exists():
            with open(skills_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                raw_skills = data.get("skills", [])
            
            # Filter: only keep skills that are either:
            # 1. Multi-word phrases (likely a real skill)
            # 2. Single words in the whitelist
            # 3. Not in stopwords and not too short/long
            filtered = []
            for s in raw_skills:
                s_stripped = s.strip()
                s_lower = s_stripped.lower()
                words = s_lower.split()
                
                if len(s_stripped) < SKILL_MIN_LENGTH or len(s_stripped) > SKILL_MAX_LENGTH:
                    continue
                if s_lower in STOPWORDS:
                    continue
                if not s_stripped or s_stripped.startswith('http'):
                    continue
                # Single word: must be in whitelist
                if len(words) == 1:
                    if s_lower not in SINGLE_WORD_SKILL_WHITELIST:
                        continue
                # Multi-word: skip if first word is a stopword or too generic
                if len(words) >= 2:
                    if words[0] in STOPWORDS and words[-1] in STOPWORDS:
                        continue
                
                filtered.append(s_stripped)
            
            self.skills_taxonomy = filtered
        else:
            # Fallback: hardcoded common skills
            self.skills_taxonomy = [
                "Python", "Java", "JavaScript", "TypeScript", "C++", "C#", "Go", "Rust",
                "SQL", "MySQL", "PostgreSQL", "MongoDB", "Redis", "SQLite",
                "Machine Learning", "Deep Learning", "NLP", "Computer Vision",
                "TensorFlow", "PyTorch", "scikit-learn", "Keras", "Pandas", "NumPy",
                "React", "Angular", "Vue.js", "Node.js", "Django", "FastAPI", "Flask",
                "Docker", "Kubernetes", "AWS", "Azure", "GCP", "Git", "Linux",
                "Data Analysis", "Data Science", "Data Engineering", "ETL",
                "Excel", "Tableau", "Power BI", "R", "MATLAB",
                "HTML", "CSS", "REST API", "GraphQL", "Microservices",
                "Project Management", "Agile", "Scrum", "Communication",
                "Leadership", "Problem Solving", "Team Collaboration",
                "Marketing", "SEO", "Content Writing", "Social Media",
                "Financial Analysis", "Accounting", "Business Development",
                "AutoCAD", "Photoshop", "Figma", "UI/UX Design",
                "Cybersecurity", "Network Security", "Penetration Testing",
                "Android", "iOS", "Flutter", "React Native",
                "Spark", "Hadoop", "Kafka", "Airflow", "dbt",
            ]
        
        # Build lowercase lookup for fast matching
        self.skills_lower = {s.lower(): s for s in self.skills_taxonomy}
    
    def extract_text_from_pdf(self, pdf_bytes: bytes) -> str:
        """Extract text from PDF bytes using pdfplumber"""
        try:
            import pdfplumber
            with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
                text_parts = []
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)
                return "\n".join(text_parts)
        except Exception as e:
            return f"Error extracting PDF: {e}"
    
    def extract_skills(self, cv_text: str) -> List[str]:
        """Extract skills from CV text using keyword matching"""
        found_skills: Set[str] = set()
        text_lower = cv_text.lower()
        
        # Multi-word skill matching (check longer phrases first)
        for skill_lower, skill_orig in sorted(self.skills_lower.items(), 
                                               key=lambda x: len(x[0]), reverse=True):
            # Use word boundary matching for accuracy
            pattern = r'\b' + re.escape(skill_lower) + r'\b'
            if re.search(pattern, text_lower):
                found_skills.add(skill_orig)
        
        # Also extract capitalized words that look like technologies/tools
        # (likely not caught by taxonomy)
        cap_words = re.findall(r'\b[A-Z][a-zA-Z+#]{2,20}\b', cv_text)
        common_tech = {'Python', 'Java', 'JavaScript', 'React', 'Angular', 'Vue',
                       'AWS', 'Azure', 'Docker', 'Kubernetes', 'GitHub', 'Jenkins',
                       'MongoDB', 'PostgreSQL', 'MySQL', 'Redis', 'Linux', 'Git'}
        for word in cap_words:
            if word in common_tech and word not in found_skills:
                found_skills.add(word)
        
        return sorted(found_skills)

    def detect_career_category(self, cv_text: str, extracted_skills: List[str]) -> Dict:
        """Detect most likely career category based on CV content"""
        text_lower = cv_text.lower()
        skills_text = " ".join(s.lower() for s in extracted_skills)
        combined = text_lower + " " + skills_text

        # Category keyword signatures — more keywords = more precise detection
        CATEGORY_KEYWORDS = {
            "Data Science": [
                "machine learning", "deep learning", "data science", "tensorflow",
                "pytorch", "pandas", "numpy", "scikit", "scikit-learn", "jupyter",
                "statistics", "neural network", "nlp", "computer vision",
                "model training", "feature engineering", "data scientist",
                "gradient boosting", "xgboost", "lightgbm", "classification",
                "regression", "clustering", "random forest", "bert", "transformer",
            ],
            "Software Engineering": [
                "software engineer", "backend developer", "frontend developer",
                "full stack", "fullstack", "api development", "microservices",
                "object-oriented", "algorithm", "system design", "rest api",
                "software development", "agile", "code review", "unit testing",
                "ci/cd", "version control", "software architecture",
            ],
            "Data Engineering": [
                "data pipeline", "etl", "spark", "apache spark", "hadoop", "kafka",
                "airflow", "data warehouse", "dbt", "bigquery", "snowflake",
                "data engineer", "data ingestion", "batch processing",
                "stream processing", "data lake", "redshift",
            ],
            "DevOps/Cloud": [
                "devops", "ci/cd", "jenkins", "docker", "kubernetes",
                "infrastructure as code", "terraform", "ansible", "cloud infrastructure",
                "aws", "azure", "gcp", "site reliability", "sre", "monitoring",
                "deployment pipeline", "containerization", "helm",
            ],
            "Mobile Development": [
                "android", "ios", "flutter", "react native", "swift",
                "kotlin", "mobile app", "xcode", "mobile development",
                "app store", "play store", "mobile ui",
            ],
            "UX/UI Design": [
                "ux", "ui design", "user experience", "figma", "sketch",
                "wireframe", "prototype", "usability", "design thinking",
                "adobe xd", "user research", "interaction design",
                "visual design", "design system",
            ],
            "Cybersecurity": [
                "penetration testing", "ethical hacking", "firewall", "vulnerability",
                "siem", "encryption", "network security", "cybersecurity",
                "information security", "threat analysis", "incident response",
                "soc analyst", "malware analysis",
            ],
            "Product Management": [
                "product manager", "product roadmap", "stakeholder", "kpi",
                "user story", "backlog", "product strategy", "product owner",
                "go-to-market", "okr", "product discovery",
            ],
            "Marketing": [
                "digital marketing", "seo", "sem", "social media marketing",
                "content marketing", "google analytics", "brand management",
                "email marketing", "paid ads", "marketing strategy",
                "conversion rate", "copywriting",
            ],
            "Finance/Accounting": [
                "financial analysis", "accounting", "cpa", "balance sheet", "audit",
                "tax", "budgeting", "financial modeling", "gaap", "ifrs",
                "investment analysis", "valuation", "financial reporting",
            ],
            "HR/Recruitment": [
                "human resources", "recruitment", "talent acquisition", "onboarding",
                "payroll", "performance management", "employee relations", "hris",
                "talent management", "compensation", "hr business partner",
            ],
            "Sales/Business Dev": [
                "sales", "business development", "b2b", "crm",
                "lead generation", "revenue growth", "account management",
                "salesforce", "pipeline management", "negotiation",
            ],
            "Healthcare": [
                "clinical", "patient care", "nursing", "hospital", "ehr",
                "pharmaceuticals", "medical device", "clinical trials",
                "healthcare management", "telemedicine",
            ],
        }

        scores = {}
        for cat, keywords in CATEGORY_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in combined)
            # Require at least 2 keywords to match before assigning a category
            # (prevents single keyword false positives like 'aws' → DevOps)
            if score >= 2:
                scores[cat] = score

        if not scores:
            # Try with 1 keyword as fallback
            for cat, keywords in CATEGORY_KEYWORDS.items():
                score = sum(1 for kw in keywords if kw in combined)
                if score >= 1:
                    scores[cat] = score

        if not scores:
            return {"category": "General Professional", "confidence": 0.3, "all_scores": {}}

        best_cat = max(scores, key=scores.get)
        best_score = scores[best_cat]
        max_possible = len(CATEGORY_KEYWORDS[best_cat])

        # Fixed formula: was hitting 100% at 40% match
        # Now needs 70% keyword coverage to reach 100% confidence
        confidence = min(best_score / max(max_possible * 0.7, 1), 1.0)

        # Normalize scores for display (percentage of max)
        normalized = {
            cat: round(s / len(CATEGORY_KEYWORDS[cat]) * 100, 1)
            for cat, s in scores.items()
        }

        return {
            "category": best_cat,
            "confidence": round(confidence, 2),
            "all_scores": dict(sorted(normalized.items(), key=lambda x: x[1], reverse=True)[:5])
        }
    
    def analyze(self, cv_text: str) -> Dict:
        """Full CV analysis: skills + category"""
        if len(cv_text.strip()) < 50:
            return {
                "error": "CV text too short",
                "skills": [],
                "category": "Unknown",
                "confidence": 0
            }
        
        skills = self.extract_skills(cv_text)
        career_info = self.detect_career_category(cv_text, skills)
        
        # Categorize skills by type
        tech_skills = []
        soft_skills = []
        tool_skills = []
        
        SOFT_SKILL_KEYWORDS = {'communication', 'leadership', 'teamwork', 'problem solving',
                               'time management', 'creativity', 'adaptability', 'collaboration',
                               'critical thinking', 'presentation', 'negotiation'}
        TOOL_KEYWORDS = {'excel', 'tableau', 'photoshop', 'figma', 'git', 'jira', 
                         'slack', 'docker', 'jenkins', 'ansible', 'terraform'}
        
        for skill in skills:
            sl = skill.lower()
            if any(s in sl for s in SOFT_SKILL_KEYWORDS):
                soft_skills.append(skill)
            elif any(t in sl for t in TOOL_KEYWORDS):
                tool_skills.append(skill)
            else:
                tech_skills.append(skill)
        
        return {
            "all_skills": skills,
            "tech_skills": tech_skills,
            "soft_skills": soft_skills,
            "tool_skills": tool_skills,
            "skill_count": len(skills),
            "career_category": career_info["category"],
            "confidence": career_info["confidence"],
            "career_scores": career_info["all_scores"]
        }
