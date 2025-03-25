from flask import Flask, render_template, request, jsonify, send_file
import os
from werkzeug.utils import secure_filename
import PyPDF2
from docx import Document
import nltk
from collections import Counter
import re
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
import io
import base64

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Download required NLTK data
nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')
nltk.download('maxent_ne_chunker')
nltk.download('words')

ALLOWED_EXTENSIONS = {'pdf', 'docx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text_from_pdf(file_path):
    text = ""
    with open(file_path, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        for page in pdf_reader.pages:
            text += page.extract_text()
    return text

def extract_text_from_docx(file_path):
    doc = Document(file_path)
    text = ""
    for paragraph in doc.paragraphs:
        text += paragraph.text + "\n"
    return text

def generate_wordcloud(skills):
    # Create word cloud
    wordcloud = WordCloud(width=800, height=400, background_color='white').generate(' '.join(skills))
    
    # Save to base64 string
    img = io.BytesIO()
    plt.figure(figsize=(10, 5))
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis('off')
    plt.savefig(img, format='png', bbox_inches='tight', pad_inches=0)
    img.seek(0)
    return base64.b64encode(img.getvalue()).decode()

def calculate_resume_score(entities):
    score = 0
    max_score = 100
    
    # Contact information (20 points)
    if entities['emails']:
        score += 10
    if entities['phones']:
        score += 10
    
    # Skills (30 points)
    skills_count = len(entities['skills'])
    score += min(skills_count * 2, 30)  # 2 points per skill, max 30
    
    # Education (25 points)
    education_count = len(entities['education'])
    score += min(education_count * 5, 25)  # 5 points per education entry, max 25
    
    # Experience (25 points)
    experience_count = len(entities['experience'])
    score += min(experience_count * 5, 25)  # 5 points per experience entry, max 25
    
    return {
        'score': score,
        'max_score': max_score,
        'percentage': round((score / max_score) * 100, 1)
    }

def generate_summary(entities):
    summary = []
    
    # Contact summary
    if entities['emails'] or entities['phones']:
        summary.append("Contact Information: Complete")
    else:
        summary.append("Contact Information: Missing")
    
    # Skills summary
    skills_count = len(entities['skills'])
    if skills_count > 10:
        summary.append(f"Strong technical skills profile with {skills_count} identified skills")
    elif skills_count > 5:
        summary.append(f"Moderate technical skills profile with {skills_count} identified skills")
    else:
        summary.append("Limited technical skills identified")
    
    # Education summary
    education_count = len(entities['education'])
    if education_count > 0:
        summary.append(f"Education background identified with {education_count} entries")
    else:
        summary.append("Education information not clearly identified")
    
    # Experience summary
    experience_count = len(entities['experience'])
    if experience_count > 5:
        summary.append(f"Extensive work experience with {experience_count} entries")
    elif experience_count > 0:
        summary.append(f"Work experience identified with {experience_count} entries")
    else:
        summary.append("Work experience not clearly identified")
    
    return summary

def generate_pdf_report(entities, score, summary):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30
    )
    elements.append(Paragraph("Resume Analysis Report", title_style))
    
    # Score
    score_style = ParagraphStyle(
        'Score',
        parent=styles['Heading2'],
        fontSize=18,
        textColor=colors.blue
    )
    elements.append(Paragraph(f"Resume Score: {score['score']}/{score['max_score']} ({score['percentage']}%)", score_style))
    elements.append(Spacer(1, 20))
    
    # Summary
    elements.append(Paragraph("Summary", styles['Heading2']))
    for point in summary:
        elements.append(Paragraph(f"• {point}", styles['Normal']))
    elements.append(Spacer(1, 20))
    
    # Contact Information
    elements.append(Paragraph("Contact Information", styles['Heading2']))
    if entities['emails']:
        elements.append(Paragraph(f"Email: {', '.join(entities['emails'])}", styles['Normal']))
    if entities['phones']:
        elements.append(Paragraph(f"Phone: {', '.join(entities['phones'])}", styles['Normal']))
    elements.append(Spacer(1, 20))
    
    # Skills
    elements.append(Paragraph("Skills", styles['Heading2']))
    for skill in entities['skills']:
        elements.append(Paragraph(f"• {skill}", styles['Normal']))
    elements.append(Spacer(1, 20))
    
    # Education
    elements.append(Paragraph("Education", styles['Heading2']))
    for edu in entities['education']:
        elements.append(Paragraph(f"• {edu}", styles['Normal']))
    elements.append(Spacer(1, 20))
    
    # Experience
    elements.append(Paragraph("Experience", styles['Heading2']))
    for exp in entities['experience']:
        elements.append(Paragraph(f"• {exp}", styles['Normal']))
    
    doc.build(elements)
    buffer.seek(0)
    return buffer

def analyze_resume(text):
    # Extract entities
    entities = {
        'names': [],
        'emails': [],
        'phones': [],
        'skills': [],
        'education': [],
        'experience': []
    }
    
    # Extract emails
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = re.findall(email_pattern, text)
    entities['emails'] = emails
    
    # Extract phone numbers
    phone_pattern = r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'
    phones = re.findall(phone_pattern, text)
    entities['phones'] = phones
    
    # Extract skills (common technical skills)
    skills_keywords = ['python', 'java', 'javascript', 'sql', 'html', 'css', 'react', 'node.js', 
                      'machine learning', 'data analysis', 'project management', 'agile', 'scrum',
                      'aws', 'docker', 'kubernetes', 'git', 'linux', 'unix', 'rest api',
                      'mongodb', 'mysql', 'postgresql', 'redis', 'elasticsearch', 'kafka',
                      'spring', 'django', 'flask', 'fastapi', 'tensorflow', 'pytorch',
                      'scikit-learn', 'pandas', 'numpy', 'matplotlib', 'seaborn']
    found_skills = []
    for skill in skills_keywords:
        if skill.lower() in text.lower():
            found_skills.append(skill)
    entities['skills'] = found_skills
    
    # Extract education
    education_keywords = ['bachelor', 'master', 'phd', 'degree', 'diploma', 'certification',
                         'university', 'college', 'school', 'graduation', 'post-graduation']
    sentences = nltk.sent_tokenize(text)
    for sentence in sentences:
        if any(keyword in sentence.lower() for keyword in education_keywords):
            entities['education'].append(sentence.strip())
    
    # Extract experience
    experience_keywords = ['experience', 'worked', 'job', 'position', 'role', 'responsibility',
                          'project', 'team', 'lead', 'manager', 'developer', 'engineer',
                          'architect', 'consultant', 'analyst', 'specialist']
    for sentence in sentences:
        if any(keyword in sentence.lower() for keyword in experience_keywords):
            entities['experience'].append(sentence.strip())
    
    return entities

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    if 'resume' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['resume']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        try:
            # Extract text based on file type
            if filename.endswith('.pdf'):
                text = extract_text_from_pdf(file_path)
            else:
                text = extract_text_from_docx(file_path)
            
            # Analyze the resume
            entities = analyze_resume(text)
            
            # Generate additional features
            wordcloud = generate_wordcloud(entities['skills'])
            score = calculate_resume_score(entities)
            summary = generate_summary(entities)
            
            # Generate PDF report
            pdf_buffer = generate_pdf_report(entities, score, summary)
            pdf_base64 = base64.b64encode(pdf_buffer.getvalue()).decode()
            
            # Clean up the uploaded file
            os.remove(file_path)
            
            return jsonify({
                'entities': entities,
                'wordcloud': wordcloud,
                'score': score,
                'summary': summary,
                'pdf_report': pdf_base64
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    return jsonify({'error': 'Invalid file type'}), 400

if __name__ == '__main__':
    app.run(debug=True) 