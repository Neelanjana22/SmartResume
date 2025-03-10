# Resume Builder Application

This is a Flask-based web application that allows users to create personalized, professional resumes using Google Gemini AI. Users can sign up, log in, and generate a resume based on their personal details and job preferences. The application ensures clean formatting, ATS optimization, and provides an option to download the resume as a PDF.

## Features

- User Authentication (Sign Up, Login, Logout)
- Google Gemini API Integration to generate professional resumes
- Clean, ATS-optimized resumes with user input
- Option to download resumes as PDF
- Secure password hashing using Flask-Bcrypt
- Session management for storing generated resumes
- User-friendly web interface with Flask templates

## Technologies Used

- **Flask**: Web framework for Python
- **SQLite**: Lightweight database for storing user information
- **Flask-Bcrypt**: Password hashing and security
- **Flask-Login**: User session management
- **Google Gemini AI API**: Used to generate resumes
- **FPDF**: Library to generate PDF files
- **BeautifulSoup**: Used for cleaning HTML from resume generation output
- **Dotenv**: Manage environment variables securely

## Prerequisites

Before you can run this project locally, you'll need to have the following installed:

- Python 3.7+ 
- Virtual environment (recommended)
- Google API Key for the Gemini API
- SQLite (usually comes pre-installed with Python)

## Installation

1. Clone this repository to your local machine:
   ```bash
   git clone https://github.com/your-username/resume-builder.git
   cd resume-builder
2. Set up a virtual environment (optional but recommended):
    python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
3. Install the required dependencies:
 pip install -r requirements.txt
4. Create a .env file in the root directory and add your Google API key:
GOOGLE_API_KEY=your_google_api_key
SECRET_KEY=your_flask_secret_key
5. Initialize the database (it will be automatically created if it doesn't exist):
python
>>> from app import cursor, conn
>>> cursor.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, email TEXT UNIQUE NOT NULL, password TEXT NOT NULL)''')
>>> conn.commit()

Usage:--

1.Run the application: python app.py

2.Open your browser and navigate to http://127.0.0.1:5000/ to access the app.

3.Create an account and log in. Once logged in, you can start building your resume.

4.After filling out the required information (name, phone, email, LinkedIn, education, experience, skills), the system will generate a professional resume.

5.You can view your resume and download it as a PDF.

Routes:--

/: Home page
/signup: Sign-up page for new users
/login: Login page for existing users
/dashboard: Dashboard where users input details to generate their resume
/generated_resume: Page to view the generated resume
/download_resume: Endpoint to download the generated resume as a PDF
/logout: Log out the current user

Security Considerations:--
Passwords are hashed using Flask-Bcrypt before being stored in the database.
Sensitive information like Google API keys and Flask secret keys are stored in environment variables (.env).

