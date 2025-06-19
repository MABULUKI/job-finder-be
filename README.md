# Job Portal Backend

A production-ready Django REST backend for a job portal with recruiter and job seeker workflows, AI-powered recommendations, and JWT authentication.

## Features
- Recruiter and job seeker registration & profile management
- Job posting and application workflows
- AI-powered job and candidate recommendations (pluggable)
- JWT authentication (djangorestframework-simplejwt)
- PostgreSQL (production) & SQLite (development) support
- Media upload for resumes and company logos

## Project Structure
```
job_portal_backend/
├── manage.py
├── job_portal_backend/         # Django project settings
├── core/                      # Main app: models, views, serializers, urls
│   ├── models.py
│   ├── serializers.py
│   ├── views.py
│   ├── urls.py
│   └── ai/                    # AI recommendation logic
│       ├── job_recommendation.py
│       └── candidate_recommendation.py
├── authentication/            # Auth app: models, views, urls
├── media/                     # Uploaded files (resumes, logos)
├── requirements.txt
└── README.md
```

## Installation & Setup

### 1. Clone the repository
```bash
git clone <your-repo-url>
cd job_portal_backend
```

### 2. Create and activate a virtual environment
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Set up the database
- By default, uses SQLite (for dev). For PostgreSQL, update `settings.py` accordingly.

### 5. Apply migrations
```bash
python manage.py makemigrations authentication core
python manage.py migrate
```

### 6. Create a superuser (optional, for admin access)
```bash
python manage.py createsuperuser
```

### 7. Run the development server
```bash
python manage.py runserver
```

## API Endpoints
- Auth: `/auth/` (signup, login)
- Recruiter profile: `/api/recruiter/profile/`
- Seeker profile: `/api/seeker/profile/`
- Jobs: `/api/jobs/`, `/api/jobs/list/`
- Applications: `/api/applications/`, `/api/applications/list/`

## AI Integration
- Add your ML logic in `core/ai/job_recommendation.py` and `core/ai/candidate_recommendation.py`.

## Notes
- Uses SQLite by default; set `DJANGO_ENV=production` for PostgreSQL.
- Media uploads go to `/media/` (configure in settings if needed).

---

For more, see code comments and docstrings.
