# AI-Powered Email Assistant

A full-stack web application that helps professionals write, manage,
and send emails using Google Gemini AI.

## Tech Stack
- **Frontend:** React, Bootstrap
- **Backend:** Django, Django REST Framework
- **Database:** MySQL
- **AI:** Google Gemini API
- **Auth:** Google OAuth 2.0 + JWT
- **Email:** Gmail API
- **Deployment:** Railway

## Project Status
- [x] Phase 1: Foundation & Setup
- [ ] Phase 2: Authentication (Google OAuth + JWT)
- [ ] Phase 3: Gmail API + Email CRUD
- [ ] Phase 4: Gemini AI Integration
- [ ] Phase 5: React Frontend + Deployment

## Setup Instructions
1. Clone the repository
2. Create virtual environment: `python -m venv venv`
3. Activate: `venv\Scripts\Activate.ps1`
4. Install dependencies: `pip install -r requirements.txt`
5. Create `.env` file (see `.env.example`)
6. Run migrations: `python manage.py migrate`
7. Start server: `python manage.py runserver`