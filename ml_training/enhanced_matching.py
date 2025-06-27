"""
Enhanced matching functions for recommendation system
These functions improve matching quality by handling real-world data variations
"""
from datetime import datetime
from typing import List, Dict, Any, Union, Set, Tuple
import re

def normalize_skills(skills_list: List[str]) -> List[str]:
    """
    Normalize skills by converting to lowercase and handling common variations
    
    Args:
        skills_list: List of skills to normalize
        
    Returns:
        List of normalized skills
    """
    if not skills_list:
        return []
        
    normalized = []
    skill_mapping = {
        # Programming Languages
        "javascript": ["javascript", "js", "java script", "ecmascript"],
        "python": ["python", "py", "python3", "python programming"],
        "java": ["java", "java programming", "core java", "java se", "java ee"],
        "c#": ["c#", "csharp", "c sharp", ".net c#"],
        "c++": ["c++", "cpp", "c plus plus"],
        "php": ["php", "php development", "php programming"],
        "ruby": ["ruby", "ruby programming", "ruby on rails", "rails"],
        "swift": ["swift", "swift programming", "ios development"],
        "kotlin": ["kotlin", "kotlin programming", "android kotlin"],
        "go": ["go", "golang", "go programming"],
        "rust": ["rust", "rust programming"],
        "typescript": ["typescript", "ts", "type script"],
        
        # Frontend Frameworks
        "react": ["react", "reactjs", "react.js", "react js", "react native"],
        "angular": ["angular", "angularjs", "angular js", "angular 2+"],
        "vue": ["vue", "vuejs", "vue.js", "vue js"],
        "svelte": ["svelte", "sveltejs", "svelte framework"],
        "jquery": ["jquery", "jquery library"],
        
        # Backend Frameworks
        "node.js": ["node.js", "nodejs", "node js", "node", "express.js", "expressjs"],
        "django": ["django", "django framework", "python django"],
        "flask": ["flask", "flask framework", "python flask"],
        "spring": ["spring", "spring boot", "spring framework", "java spring"],
        "laravel": ["laravel", "php laravel", "laravel framework"],
        "asp.net": ["asp.net", "asp net", "asp.net mvc", "asp.net core"],
        
        # Mobile Development
        "flutter": ["flutter", "flutter framework", "flutter development", "dart flutter"],
        "react native": ["react native", "react-native", "reactnative"],
        "android": ["android", "android development", "android studio"],
        "ios": ["ios", "ios development", "swift ios", "objective-c"],
        "xamarin": ["xamarin", "xamarin forms", "xamarin.forms"],
        
        # Database
        "sql": ["sql", "structured query language", "sql queries"],
        "mysql": ["mysql", "my sql", "mysql database"],
        "postgresql": ["postgresql", "postgres", "postgres sql", "postgre"],
        "mongodb": ["mongodb", "mongo", "mongo db", "nosql"],
        "sqlite": ["sqlite", "sqlite3", "sql lite"],
        "oracle": ["oracle", "oracle database", "oracle db", "pl/sql"],
        "redis": ["redis", "redis cache", "redis database"],
        "firebase": ["firebase", "firebase database", "firestore"],
        
        # DevOps & Cloud
        "aws": ["aws", "amazon web services", "amazon aws", "ec2", "s3", "lambda"],
        "azure": ["azure", "microsoft azure", "azure cloud"],
        "gcp": ["gcp", "google cloud", "google cloud platform"],
        "docker": ["docker", "docker container", "containerization"],
        "kubernetes": ["kubernetes", "k8s", "k-8-s"],
        "jenkins": ["jenkins", "jenkins ci", "jenkins pipeline"],
        "git": ["git", "github", "gitlab", "git version control"],
        "terraform": ["terraform", "terraform iac", "hashicorp terraform"],
        
        # Web Development
        "html": ["html", "html5", "hypertext markup language"],
        "css": ["css", "css3", "cascading style sheets", "scss", "sass"],
        "bootstrap": ["bootstrap", "bootstrap framework", "bootstrap css"],
        "tailwind": ["tailwind", "tailwindcss", "tailwind css"],
        "web development": ["web development", "web dev", "website development", "frontend development", "backend development"],
        "responsive design": ["responsive design", "responsive web design", "mobile-first design"],
        "pwa": ["pwa", "progressive web app", "progressive web application"],
        
        # Data Science & AI
        "machine learning": ["machine learning", "ml", "machine learning algorithms"],
        "deep learning": ["deep learning", "dl", "neural networks", "cnn", "rnn", "lstm"],
        "data science": ["data science", "data scientist", "data analytics"],
        "data analysis": ["data analysis", "data analytics", "data analyst", "data visualization"],
        "tensorflow": ["tensorflow", "tf", "tensor flow"],
        "pytorch": ["pytorch", "torch", "py torch"],
        "scikit-learn": ["scikit-learn", "sklearn", "scikit learn"],
        "nlp": ["nlp", "natural language processing", "text analytics"],
        "computer vision": ["computer vision", "cv", "image processing", "image recognition"],
        
        # Project Management
        "project management": ["project management", "project mgmt", "project manager", "project lead"],
        "agile": ["agile", "agile methodology", "scrum", "kanban", "sprint planning"],
        "jira": ["jira", "jira software", "atlassian jira"],
        "trello": ["trello", "trello board", "trello management"],
        "scrum master": ["scrum master", "scrum methodology", "agile scrum"],
        "product owner": ["product owner", "product management", "product backlog"],
        
        # Business & Marketing
        "seo": ["seo", "search engine optimization", "search optimization"],
        "digital marketing": ["digital marketing", "online marketing", "internet marketing"],
        "content marketing": ["content marketing", "content strategy", "content creation"],
        "social media marketing": ["social media marketing", "social media management", "smm"],
        "email marketing": ["email marketing", "email campaigns", "newsletter management"],
        "crm": ["crm", "customer relationship management", "salesforce", "hubspot"],
        
        # Design
        "ui design": ["ui design", "user interface design", "interface design"],
        "ux design": ["ux design", "user experience design", "usability"],
        "graphic design": ["graphic design", "visual design", "graphics"],
        "adobe photoshop": ["adobe photoshop", "photoshop", "ps"],
        "adobe illustrator": ["adobe illustrator", "illustrator", "ai"],
        "figma": ["figma", "figma design", "figma prototyping"],
        "sketch": ["sketch", "sketch app", "sketch design"],
        
        # Soft Skills
        "communication": ["communication", "communication skills", "verbal communication", "written communication"],
        "teamwork": ["teamwork", "team collaboration", "team player", "collaborative"],
        "leadership": ["leadership", "team leadership", "people management", "team management"],
        "problem solving": ["problem solving", "critical thinking", "analytical thinking", "analytical skills"],
        "time management": ["time management", "prioritization", "organizational skills"],
        
        # Education
        "bachelor degree": ["bachelor degree", "bachelors", "bachelor degree", "undergraduate degree", "bs", "ba"],
        "master degree": ["master degree", "masters", "master degree", "graduate degree", "ms", "ma", "mba"],
        "phd": ["phd", "doctorate", "doctoral degree", "ph.d", "doctor of philosophy"],
        "certification": ["certification", "professional certification", "industry certification", "certified"],
    }
    
    # Create reverse mapping for easy lookup
    reverse_mapping = {}
    for canonical, variations in skill_mapping.items():
        for var in variations:
            reverse_mapping[var] = canonical
    
    for skill in skills_list:
        if not skill:
            continue
            
        skill_lower = skill.lower().strip()
        
        # Check if this is a known variation
        if skill_lower in reverse_mapping:
            normalized.append(reverse_mapping[skill_lower])
        else:
            normalized.append(skill_lower)
    
    # Remove duplicates while preserving order
    seen = set()
    return [x for x in normalized if not (x in seen or seen.add(x))]

def extract_experience_years(experience_list: List[Dict[str, Any]]) -> float:
    """
    Extract total years of experience from experience entries
    
    Args:
        experience_list: List of experience dictionaries
        
    Returns:
        Total years of experience as a float
    """
    if not experience_list:
        return 0.0
        
    total_years = 0.0
    current_year = datetime.now().year
    
    for exp in experience_list:
        # If years is directly available
        if 'years' in exp and isinstance(exp.get('years'), (int, float)):
            total_years += float(exp['years'])
            continue
            
        # Try to extract from duration field
        if 'duration' in exp:
            duration = exp.get('duration', '')
            if not duration:
                continue
                
            # Handle different duration formats
            try:
                # Format: "2021-2024" or "2021-present"
                if '-' in duration:
                    start_str, end_str = duration.split('-')
                    
                    # Extract years from strings like "2021" or "Jan 2021"
                    start_year = int(re.search(r'\b(19|20)\d{2}\b', start_str).group(0))
                    
                    # Handle "present" or current year
                    if end_str.lower() in ('present', 'now', 'current'):
                        end_year = current_year
                    else:
                        end_year = int(re.search(r'\b(19|20)\d{2}\b', end_str).group(0))
                    
                    # Calculate years, ensuring at least 0
                    years = max(0, end_year - start_year)
                    total_years += years
                    
                # Format: "3 years" or "3.5 years"
                elif 'year' in duration.lower():
                    match = re.search(r'(\d+(?:\.\d+)?)', duration)
                    if match:
                        years = float(match.group(1))
                        total_years += years
            except (ValueError, AttributeError) as e:
                # If parsing fails, log and continue
                print(f"[DEBUG] Failed to parse experience duration: {duration}, error: {str(e)}")
    
    return round(total_years, 1)

def education_level_score(seeker_education: List[Dict[str, Any]], job_requirements: List[Dict[str, Any]]) -> float:
    """
    Calculate education match score based on structured job requirements
    
    Args:
        seeker_education: List of education dictionaries from seeker profile
        job_requirements: List of requirement dictionaries from job posting
        
    Returns:
        Education match score between 0.0 and 1.0
    """
    if not job_requirements:
        return 1.0  # No specific requirements
    
    # Define education level rankings
    education_rank = {
        'no education': 0,
        'ordinary levels': 1,
        'certificate': 2,
        'diploma': 3,
        'bachelor': 4, 
        'degree': 4,
        'masters': 5,
        'phd': 6,
        'doctorate': 6
    }
    
    # Extract education requirements that are specifically of type 'education'
    education_requirements = []
    for req in job_requirements:
        if isinstance(req, dict) and req.get('type') == 'education':
            education_requirements.append(req)
    
    # If no specific education requirements found, check legacy format
    if not education_requirements:
        # Legacy format handling
        required_education = []
        required_fields = []
        
        for req in job_requirements:
            if isinstance(req, str):
                req_lower = req.lower()
                
                # Check for education level requirements
                if 'bachelor' in req_lower or 'degree' in req_lower:
                    required_education.append('bachelor')
                elif 'master' in req_lower:
                    required_education.append('masters')
                elif 'phd' in req_lower or 'doctorate' in req_lower:
                    required_education.append('phd')
                elif 'diploma' in req_lower:
                    required_education.append('diploma')
                
                # Check for field requirements
                fields = ['engineering', 'computer science', 'it', 'software', 
                         'business', 'marketing', 'finance', 'accounting', 
                         'medicine', 'healthcare', 'data science']
                
                for field in fields:
                    if field in req_lower:
                        required_fields.append(field)
        
        # Legacy scoring
        if not required_education and not required_fields:
            return 1.0
            
        # Extract seeker education levels for legacy format
        seeker_levels = []
        seeker_fields = []
        for edu in seeker_education:
            level = edu.get('level', '').lower()
            field = edu.get('field', '').lower()
            type_val = edu.get('type', '').lower()
            
            if level:
                seeker_levels.append(level)
            if field:
                seeker_fields.append(field)
                
            # Map education types to standard levels
            if 'bachelor' in type_val or 'degree' in type_val:
                seeker_levels.append('bachelor')
            elif 'master' in type_val:
                seeker_levels.append('masters')
            elif 'phd' in type_val or 'doctorate' in type_val:
                seeker_levels.append('phd')
            elif 'diploma' in type_val:
                seeker_levels.append('diploma')
        
        # Find seeker's highest education level
        seeker_highest = 0
        for level in seeker_levels:
            for key, rank in education_rank.items():
                if key in level:
                    seeker_highest = max(seeker_highest, rank)
        
        # Find job's required education level
        required_highest = 0
        for level in required_education:
            required_highest = max(required_highest, education_rank.get(level, 0))
        
        # Calculate level match score
        if required_highest == 0:
            level_score = 1.0  # No specific level requirement
        elif seeker_highest >= required_highest:
            level_score = 1.0  # Meets or exceeds requirements
        elif seeker_highest > 0:
            level_score = seeker_highest / required_highest  # Partial match
        else:
            level_score = 0.0  # No match
        
        # Check field match if required
        field_score = 1.0
        if required_fields:
            has_field_match = False
            for field in seeker_fields:
                for req_field in required_fields:
                    if req_field in field:
                        has_field_match = True
                        break
                if has_field_match:
                    break
            
            field_score = 1.0 if has_field_match else 0.0  # Stricter field matching
        
        # Combine scores (field is now equally important)
        return level_score * 0.5 + field_score * 0.5
    
    # New structured education matching
    # For each job education requirement, find if the seeker has a matching education
    requirement_scores = []
    
    for job_edu in education_requirements:
        job_level = job_edu.get('level', '').lower()
        job_field = job_edu.get('field', '').lower()
        
        # Skip if no level or field specified
        if not job_level or not job_field:
            continue
            
        # Get the required education rank
        required_rank = 0
        for key, rank in education_rank.items():
            if key in job_level:
                required_rank = rank
                break
        
        # Check each of seeker's education entries
        best_match_score = 0.0
        
        for seeker_edu in seeker_education:
            seeker_level = seeker_edu.get('level', '').lower()
            seeker_field = seeker_edu.get('field', '').lower()
            
            # Skip if no level or field specified
            if not seeker_level or not seeker_field:
                continue
                
            # Get seeker education rank
            seeker_rank = 0
            for key, rank in education_rank.items():
                if key in seeker_level:
                    seeker_rank = rank
                    break
            
            # Calculate level match
            if seeker_rank >= required_rank:
                level_score = 1.0  # Meets or exceeds requirements
            elif seeker_rank > 0 and required_rank > 0:
                level_score = seeker_rank / required_rank  # Partial match
            else:
                level_score = 0.0  # No match
            
            # Calculate field match - exact match required
            # Normalize fields by removing spaces and converting to lowercase
            norm_seeker_field = seeker_field.replace(' ', '').lower()
            norm_job_field = job_field.replace(' ', '').lower()
            
            # Check for exact match or if one contains the other
            if norm_seeker_field == norm_job_field:
                field_score = 1.0  # Exact match
            elif norm_seeker_field in norm_job_field or norm_job_field in norm_seeker_field:
                field_score = 0.8  # Partial match
            else:
                field_score = 0.0  # No match
            
            # Calculate combined score for this education entry
            # Field matching is now MORE important (60%) than level (40%)
            match_score = level_score * 0.4 + field_score * 0.6
            
            # Keep track of best match
            best_match_score = max(best_match_score, match_score)
        
        requirement_scores.append(best_match_score)
    
    # If no valid requirements were processed, return neutral score
    if not requirement_scores:
        return 0.5
    
    # Return average score across all requirements
    # This ensures ALL education requirements must be satisfied for a high score
    return sum(requirement_scores) / len(requirement_scores)

def job_type_match(seeker_preferences: List[str], job_type: str) -> float:
    """
    Calculate job type match score, handling empty preferences
    
    Args:
        seeker_preferences: List of job type preferences from seeker profile
        job_type: Job type string from job posting
        
    Returns:
        Job type match score between 0.0 and 1.0
    """
    if not job_type:
        return 0.0
        
    # If seeker has no preferences, consider all job types acceptable
    if not seeker_preferences:
        return 1.0
    
    # Normalize job types
    job_type = job_type.upper()
    seeker_preferences = [pref.upper() for pref in seeker_preferences]
    
    # Check for direct match
    if job_type in seeker_preferences:
        return 1.0
        
    # Handle related job types with partial scores
    related_types = {
        'FULL_TIME': {'PART_TIME': 0.5, 'CONTRACT': 0.3},
        'PART_TIME': {'FULL_TIME': 0.5, 'TEMPORARY': 0.7},
        'CONTRACT': {'FULL_TIME': 0.3, 'TEMPORARY': 0.5},
        'INTERNSHIP': {'PART_TIME': 0.5, 'TEMPORARY': 0.3},
        'TEMPORARY': {'PART_TIME': 0.7, 'CONTRACT': 0.5}
    }
    
    # Check for related job types
    max_score = 0.0
    for pref in seeker_preferences:
        if pref in related_types and job_type in related_types[pref]:
            max_score = max(max_score, related_types[pref][job_type])
    
    return max_score

def enhanced_location_match(seeker_location: str, job_location: str, willing_to_relocate: bool) -> float:
    """
    Enhanced location matching with relocation consideration
    
    Args:
        seeker_location: Location string from seeker profile
        job_location: Location string from job posting
        willing_to_relocate: Whether seeker is willing to relocate
        
    Returns:
        Location match score between 0.0 and 1.0
    """
    if not seeker_location or not job_location:
        return 0.5  # Neutral score for missing data
        
    # Normalize locations
    seeker_location = seeker_location.lower().strip()
    job_location = job_location.lower().strip()
    
    # Direct location match
    if seeker_location == job_location:
        return 1.0
    
    # Check for partial matches (e.g., "Dar es Salaam" vs "Dar")
    if seeker_location in job_location or job_location in seeker_location:
        return 0.9
    
    # Willing to relocate
    if willing_to_relocate:
        return 0.7  # High but not perfect score
    
    # No match and not willing to relocate
    return 0.0

def get_matching_skills(seeker_skills: List[str], job_skills: List[str]) -> Tuple[Set[str], float]:
    """
    Get matching skills and calculate skill overlap score
    
    Args:
        seeker_skills: List of skills from seeker profile
        job_skills: List of skills from job posting
        
    Returns:
        Tuple of (matching skills set, skill overlap score)
    """
    if not seeker_skills or not job_skills:
        return set(), 0.0
        
    # Normalize skills
    norm_seeker_skills = normalize_skills(seeker_skills)
    norm_job_skills = normalize_skills(job_skills)
    
    # Find matching skills
    matching_skills = set(norm_seeker_skills) & set(norm_job_skills)
    
    # Calculate Jaccard similarity
    if not matching_skills:
        return set(), 0.0
        
    union_size = len(set(norm_seeker_skills) | set(norm_job_skills))
    jaccard = len(matching_skills) / union_size if union_size > 0 else 0
    
    # Calculate percentage of job skills matched
    job_skills_matched = len(matching_skills) / len(norm_job_skills) if norm_job_skills else 0
    
    # Combine scores (emphasize matching job requirements)
    skill_score = jaccard * 0.4 + job_skills_matched * 0.6
    
    return matching_skills, skill_score
