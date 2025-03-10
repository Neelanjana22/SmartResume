import google.generativeai as genai
import os
import sqlite3
from flask import Flask, render_template, request, flash, redirect, url_for, session, send_file
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from dotenv import load_dotenv
from fpdf import FPDF
import io
import re
from bs4 import BeautifulSoup

# Load environment variables
load_dotenv()

app = Flask(__name__)

app.secret_key = os.getenv('SECRET_KEY')
bcrypt = Bcrypt(app)

# Configure Google Gemini API Key
genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))

# Database Connection
conn = sqlite3.connect('users.db', check_same_thread=False)
cursor = conn.cursor()

# Create users table if not exists
cursor.execute('''CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
)''')
conn.commit()

# Flask-Login Setup
login_manager = LoginManager(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, id, name, email):
        self.id = id
        self.name = name
        self.email = email


@login_manager.user_loader
def load_user(user_id):
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    if user:
        return User(user[0], user[1], user[2])
    return None

# Add custom filter to convert newline to <br> tag
@app.template_filter('nl2br')
def nl2br_filter(s):
    return s.replace('\n', '<br>')

# Home Page
@app.route('/')
def index():
    return render_template('index.html')

# Signup Route
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')

        # Check if user already exists
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        if cursor.fetchone():
            flash('Email already exists. Please login.', 'error')
            return redirect(url_for('login'))

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        cursor.execute("INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
                       (name, email, hashed_password))
        conn.commit()
        flash('Account created successfully! Please login.', 'success')
        return redirect(url_for('login'))

    return render_template('signup.html')

# Login Route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        # Fetch user
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()

        if user and bcrypt.check_password_hash(user[3], password):
            user_obj = User(user[0], user[1], user[2])
            login_user(user_obj)
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials, please try again.', 'error')

    return render_template('login.html')


# Dashboard (Resume Builder)
@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    try:
        if request.method == 'POST':
            name = request.form.get('name')
            phone = request.form.get('phone')
            email = request.form.get('email')
            linkedin = request.form.get('linkedin')
            education = request.form.get('education')
            experience = request.form.get('experience')
            skills = request.form.get('skills')

            if not all([name, phone, email, linkedin, education, experience, skills]):
                flash('Please fill in all fields.', 'error')
                return render_template('dashboard.html', name=current_user.name)

            prompt = f"""
You are a professional AI resume generator. Your task is to generate a clean, professional resume without any empty sections, no repeated headers, and no misplaced content.
Generate a highly compelling and job-tailored resume based on the provided user details.
Ensure that the resume is optimized for ATS (Applicant Tracking System) and uses strong, action-oriented language.
For the skills section, do not simply list the skills provided by the user; instead, expand on them by describing their practical applications or how they contribute to achieving business goals.
Craft a powerful professional summary that aligns with the target job role.
Use a concise, result-driven, and impactful tone throughout the resume.
Avoid any empty sections and ensure consistent, professional formatting.After skills section,if there are any suggestion,give them in dim color(there should be difference for the resume and suggestions)
---

### *Candidate Details:*
- *Name:* {name}
- *Phone:* {phone}
- *Email:* {email}
- *LinkedIn:* {linkedin}
- *Education:* {education}
- *Experience:* {experience}
- *Skills:* {skills}
- *Job Role:* {request.form.get('job_role') if request.form.get('job_role') else 'Data Analyst'}

---

###  *Resume Rules:*  
1.  *NEVER* show empty sections (like Experience or Education).  
2.  *NEVER* repeat the "Professional Summary" header.  
3.  Always show *Skills*, even if there's only one.  
4.  Remove any section where input was blank.  
5.  Format the resume cleanly and professionally.  

---

###  *Generate the Resume as Follows:*  

*{name}*  
*Phone:* {phone} | *Email:* {email} | *LinkedIn:* {linkedin}  

---

### *Professional Summary*  
Highly motivated and detail-oriented aspiring {request.form.get('job_role') if request.form.get('job_role') else 'Data Analyst'}  
with strong knowledge in {skills}. Passionate about extracting meaningful insights from data and contributing to data-driven decision-making.  

---

### *Education*  
{education}

---

### *Experience*  
{experience if experience else "• Actively seeking opportunities to apply and enhance technical skills in a professional environment.\n• Open to internships and entry-level positions to gain hands-on experience."}

---

### *Skills*  
- {skills.replace(',', '\n- ')}

---

 *Rules Followed:*  
-  No empty sections.  
-  No repeated headers.  
-  Always show Skills.  
-  Clean, professional formatting.  

---

###  Example of Clean Output:
 If input was:  
- Name: Abc  
- Phone: 1234567890  
- Email: Abc@gmail.com  
- LinkedIn: vbnnnnn  
- Education: CVR College  
- Experience: No experience  
- Skills: Python  

---

### ✅ *Generated Output Will Be:*
---

*Abc*  
*Phone:* 1234567890 | *Email:* Abc@gmail.com | *LinkedIn:* vbnnnnn  

---

### *Professional Summary*  
Highly motivated and detail-oriented aspiring Data Analyst  
with strong knowledge in Python. Passionate about extracting meaningful insights from data and contributing to data-driven decision-making.  

---

### *Education*  
Studied atCVR College of engineering

---

### *Experience*  
Actively seeking opportunities to apply and enhance technical skills in a professional environment.\n• Open to internships and entry-level positions to gain hands-on experience."

### *Skills*  
- Python  

---

 
"""

            # ✅ Call Gemini API
            model = genai.GenerativeModel('models/gemini-1.5-pro-latest')
            response = model.generate_content(prompt)
            generated_resume = response.text

            # ✅ Strip ALL HTML tags using BeautifulSoup
            soup = BeautifulSoup(generated_resume, "html.parser")
            clean_resume = soup.get_text(separator="\n")  # Converts it to clean text

            # ✅ Store the clean resume in session
            session['generated_resume'] = clean_resume

            # ✅ Redirect to a different page to show clean resume
            return redirect(url_for('generated_resume'))

    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        return render_template('dashboard.html', name=current_user.name)

    return render_template('dashboard.html', name=current_user.name)


# ✅ Separate Page to Display Clean Resume
@app.route('/generated_resume')
@login_required
def generated_resume():
    clean_resume = session.get('generated_resume')
    if not clean_resume:
        flash('No resume found. Please generate one first.', 'error')
        return redirect(url_for('dashboard'))
    
    print("Resume content:", clean_resume)  # For debugging
    return render_template('generated_resume.html', resume=clean_resume)


@app.route('/download_resume')
@login_required
def download_resume():
    try:
        clean_resume = session.get('generated_resume')
        if not clean_resume:
            flash('No resume found. Please generate one first.', 'error')
            return redirect(url_for('dashboard'))

        # Create PDF
        pdf = FPDF()
        pdf.add_page()
        
        # Set font for name (larger and bold)
        pdf.set_font("Arial", 'B', 16)
        
        # Split resume into sections
        sections = clean_resume.split('---')
        
        # Process contact information (first section)
        contact_lines = sections[0].strip().split('\n')
        for i, line in enumerate(contact_lines):
            if i == 0:  # Name
                pdf.cell(0, 10, line.replace('*', '').strip(), ln=True, align='C')
            else:  # Contact details
                pdf.set_font("Arial", '', 12)
                pdf.cell(0, 10, line.replace('*', '').strip(), ln=True, align='C')
        
        pdf.ln(5)
        
        # Process other sections
        for section in sections[1:]:
            if section.strip():
                lines = section.strip().split('\n')
                for i, line in enumerate(lines):
                    if line.strip():
                        if line.startswith('###'):  # Section header
                            pdf.set_font("Arial", 'B', 14)
                            pdf.cell(0, 10, line.replace('###', '').replace('*', '').strip(), ln=True)
                        else:  # Section content
                            pdf.set_font("Arial", '', 12)
                            # Handle bullet points
                            if line.strip().startswith('•'):
                                pdf.cell(10, 10, '•', ln=0)
                                pdf.multi_cell(0, 10, line.strip()[1:].strip())
                            else:
                                pdf.multi_cell(0, 10, line.replace('*', '').strip())
                pdf.ln(5)

        # Save PDF to a temporary file
        temp_pdf_path = "temp_resume.pdf"
        pdf.output(temp_pdf_path)

        # Send the file and then remove it
        response = send_file(
            temp_pdf_path,
            mimetype='application/pdf',
            as_attachment=True,
            download_name='resume.pdf'
        )
        
        # Delete the temporary file after sending
        @response.call_on_close
        def cleanup():
            if os.path.exists(temp_pdf_path):
                os.remove(temp_pdf_path)

        return response

    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('dashboard'))

# Logout
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)