# AI Email Assistant - Backend

A production-grade full-stack AI Email Assistant built with Django.

## 🚀 Tech Stack
- **Framework:** Django 4.2 + Django REST Framework
- **Database:** MySQL
- **Authentication:** Google OAuth 2.0 + JWT
- **AI:** Google Gemini API (gemini-3.1-flash-lite)
- **Email:** Gmail API
- **Deployment:** Railway

## ✨ Features
- Google OAuth 2.0 login
- JWT authentication
- Gmail integration (read & send emails)
- AI-powered email composition
- AI email improvement
- AI reply generation
- AI subject line suggestions
- AI email summarization
- Multi-user support

## 📦 Installation

### 1. Clone the repository
git clone https://github.com/rajatsharma09302005-source/ai-email-assistant.git
cd ai-email-assistant

### 2. Create virtual environment
python -m venv venv
venv\Scripts\Activate.ps1  # Windows
source venv/bin/activate   # Mac/Linux

### 3. Install dependencies
pip install -r requirements.txt

### 4. Create .env file
DEBUG=True
SECRET_KEY=your-secret-key
DB_NAME=email_assistant
DB_USER=root
DB_PASSWORD=your-password
DB_HOST=localhost
DB_PORT=3306
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
GEMINI_API_KEY=your-gemini-api-key
JWT_SECRET_KEY=your-jwt-secret
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=1440
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

### 5. Run migrations
python manage.py migrate

### 6. Start server
python manage.py runserver

## 🌐 API Endpoints

### Auth
- POST /api/auth/google/ - Google OAuth login
- GET /api/auth/user/ - Get current user
- POST /api/auth/logout/ - Logout
- GET /api/auth/gmail/status/ - Gmail connection status
- GET /api/auth/gmail/init/ - Start Gmail OAuth
- POST /api/auth/gmail/callback/ - Gmail OAuth callback

### Emails
- GET /api/emails/ - List emails
- POST /api/emails/create/ - Create draft
- GET /api/emails/<id>/ - Get email
- POST /api/emails/<id>/send/ - Send email
- POST /api/emails/<id>/reply/ - Reply to email
- DELETE /api/emails/<id>/delete/ - Delete email

### Gmail
- POST /api/gmail/fetch-inbox/ - Sync inbox
- GET /api/gmail/stats/ - Email statistics

### AI
- POST /api/ai/compose/ - Compose email
- POST /api/ai/improve/ - Improve email
- POST /api/ai/reply/ - Generate reply
- POST /api/ai/subject/ - Generate subjects
- POST /api/ai/summarize/ - Summarize email

## 👨‍💻 Developer
Rajat Sharma - B.Tech CSE, Vision Institute of Technology