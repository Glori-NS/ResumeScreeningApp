from flask import Flask, request, render_template
import os
import plotly.express as px
import pandas as pd
import re
import spacy
import fitz  # PyMuPDF for PDF files
from docx import Document
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from rake_nltk import Rake
import openai

app = Flask(__name__)

# Set OpenAI API Key
openai.api_key = os.getenv('OPENAI_API_KEY', 'sk-proj-Ym7Quz4RnaRTBkij6WdsT3BlbkFJNq1NvAMkBqfFIH2JSNDP')

# Load Spacy model for Named Entity Recognition
nlp = spacy.load('en_core_web_sm')

# Define a custom stoplist for RAKE
custom_stoplist = [
    'and', 'or', 'but', 'with', 'the', 'a', 'an', 'of', 'to', 'in',
    'for', 'on', 'at', 'by', 'from', 'up', 'down', 'over', 'under', 'again',
]

rake = Rake(stopwords=custom_stoplist)

# Comprehensive skill list (expanded to fit most industries)
common_skills = [
    # Technical skills
    'python', 'java', 'c++', 'javascript', 'html', 'css', 'sql', 'ruby', 'php',
    'swift', 'kotlin', 'typescript', 'bash', 'shell scripting', 'docker',
    'kubernetes', 'aws', 'azure', 'gcp', 'linux', 'windows', 'macos', 'git',
    'machine learning', 'deep learning', 'data science', 'big data', 'hadoop',
    'spark', 'tensorflow', 'pytorch', 'scikit-learn', 'nlp', 'computer vision',
    'blockchain', 'cybersecurity', 'networking', 'database management', 'oracle',
    'mysql', 'postgresql', 'mongodb', 'sqlite', 'firebase', 'rest api', 'graphql',
    'agile', 'scrum', 'devops', 'ci/cd', 'unit testing', 'integration testing',
    'qa', 'automation', 'selenium', 'jmeter', 'cloud computing', 'virtualization',
    'microservices', 'react', 'angular', 'vue', 'node.js', 'express', 'django',
    'flask', 'laravel', 'spring', 'hibernate', 'dotnet', 'unity', 'unreal engine',
    
    # Soft skills
    'communication', 'teamwork', 'leadership', 'problem-solving', 'critical thinking',
    'time management', 'adaptability', 'creativity', 'work ethic', 'attention to detail',
    'organization', 'interpersonal skills', 'emotional intelligence', 'negotiation',
    'conflict resolution', 'project management', 'presentation', 'public speaking',
    'customer service', 'sales', 'marketing', 'strategic planning', 'decision making',
    'analytical skills', 'research', 'writing', 'editing', 'proofreading',
    
    # Business skills
    'accounting', 'finance', 'budgeting', 'forecasting', 'financial analysis',
    'business analysis', 'business development', 'product management', 'supply chain',
    'logistics', 'procurement', 'contract management', 'human resources', 'recruitment',
    'talent management', 'performance management', 'training and development',
    'compliance', 'risk management', 'quality assurance', 'lean manufacturing',
    'six sigma', 'process improvement', 'operations management', 'change management',
    
    # Design skills
    'graphic design', 'ui/ux design', 'adobe photoshop', 'adobe illustrator',
    'adobe xd', 'sketch', 'figma', 'invision', 'web design', 'responsive design',
    'prototyping', 'wireframing', 'branding', 'typography', 'video editing',
    'motion graphics', 'animation', '3d modeling', 'autocad', 'blender', 'maya',
    
    # Industry-specific skills
    'healthcare', 'nursing', 'patient care', 'clinical research', 'pharmaceuticals',
    'biotechnology', 'chemical engineering', 'mechanical engineering', 'electrical engineering',
    'civil engineering', 'construction management', 'architecture', 'urban planning',
    'education', 'teaching', 'curriculum development', 'e-learning', 'instructional design',
    'legal', 'litigation', 'contract law', 'intellectual property', 'real estate',
    'property management', 'hospitality', 'event planning', 'food and beverage',
    'culinary arts', 'tourism', 'travel planning', 'automotive', 'manufacturing',
    'production management', 'quality control', 'maintenance', 'repair',
    
    # Other skills
    'foreign languages', 'translation', 'interpretation', 'writing', 'editing',
    'publishing', 'social media', 'content creation', 'influencer marketing',
    'seo', 'sem', 'ppc', 'email marketing', 'market research', 'data analysis',
    'statistics', 'survey design', 'customer relationship management (crm)',
    'salesforce', 'sap', 'erp', 'microsoft office', 'excel', 'powerpoint', 'word'
]

# Function to extract text from PDF
def extract_text_from_pdf(file):
    document = fitz.open(stream=file, filetype="pdf")
    text = ""
    for page_num in range(len(document)):
        page = document.load_page(page_num)
        text += page.get_text()
    return text

# Function to extract text from DOCX
def extract_text_from_docx(file):
    document = Document(file)
    text = "\n".join([paragraph.text for paragraph in document.paragraphs])
    return text

# Function to remove personal information
def clean_resume_text(text):
    lines = text.split('\n')
    cleaned_lines = []
    for line in lines:
        # Skip the first few lines that might contain personal information
        if len(cleaned_lines) > 5:
            cleaned_lines.append(line)
        else:
            if not re.match(r"^\s*\d+\s*$", line):  # skip lines with numbers only
                cleaned_lines.append(line)
    return "\n".join(cleaned_lines)

@app.route('/')
def home():
    return render_template('index.html')

def extract_keywords_with_rake(text):
    rake.extract_keywords_from_text(text)
    keywords = rake.get_ranked_phrases()
    return [k.lower() for k in keywords]

def extract_skills(text):
    doc = nlp(text)
    skills = []
    
    # Use predefined common skills to extract skills from the text
    for token in doc:
        if token.text.lower() in common_skills:
            skills.append(token.text.lower())
    
    # Use regex pattern to identify skills in the text
    pattern = re.compile(r'\b(?:{})\b'.format('|'.join(re.escape(skill) for skill in common_skills)), re.IGNORECASE)
    skills.extend(re.findall(pattern, text))

    return list(set(skills))  # Return unique skills

def extract_experiences(text):
    doc = nlp(text)
    experiences = [ent.text for ent in doc.ents if ent.label_ in {'ORG', 'WORK_OF_ART', 'TITLE', 'GPE'}]
    return list(set(experiences))

def calculate_matching_score(keywords1, keywords2):
    matched_keywords = set(keywords1).intersection(set(keywords2))
    if keywords2:
        return len(matched_keywords) / len(keywords2) * 100
    else:
        return 0

def calculate_cosine_similarity(text1, text2):
    vectorizer = TfidfVectorizer().fit_transform([text1, text2])
    vectors = vectorizer.toarray()
    cosine_sim = cosine_similarity(vectors)
    return cosine_sim[0][1] * 100  # Convert to percentage

def generate_match_chart(match_score):
    data = {'Type': ['Matched', 'Unmatched'], 'Score': [match_score, 100 - match_score]}
    df = pd.DataFrame(data)
    fig = px.pie(df, names='Type', values='Score', title='Match Score', hole=0.4)
    fig.update_traces(textinfo='percent+label')
    fig.update_layout(showlegend=True)
    return fig.to_html(full_html=False)

def summarize_text(text):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": f"Summarize the Job Description and identify key requirements and preferred qualifications. :\n\n{text}"}
        ]
    )
    summary = response.choices[0].message["content"].strip()
    return summary

def generate_analysis(resume_text, job_description):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": f"Analyze the following resume in relation to the job description and provide a brief analysis. Ensure the analysis is free of bias and focuses solely on the skills, experiences, and qualifications relevant to the job description. Do not include or consider the applicant's name or any other personal identifiers:\n\nResume:\n{resume_text}\n\nJob Description:\n{job_description}"}
        ]
    )
    analysis = response.choices[0].message["content"].strip()
    return analysis

@app.route('/upload', methods=['POST'])
def upload_file():
    job_title = request.form.get('job_title')
    job_description = request.form.get('job_description')
    resume_file = request.files.get('resume')

    if not job_description:
        return 'Job description is required', 400
    if not resume_file or resume_file.filename == '':
        return 'No selected file', 400

    if resume_file.filename.split('.')[-1] not in ['txt', 'pdf', 'doc', 'docx']:
        return 'Invalid file type', 400

    resume_content = resume_file.read()
    if len(resume_content) > 1024 * 1024 * 5:  # 5 MB limit for example
        return 'File too large', 400

    if resume_file.filename.endswith('.pdf'):
        resume_text = extract_text_from_pdf(resume_content)
    elif resume_file.filename.endswith('.docx'):
        resume_text = extract_text_from_docx(resume_content)
    else:
        resume_text = resume_content.decode('utf-8', errors='ignore')

    # Clean resume text to remove personal information
    resume_text = clean_resume_text(resume_text)

    resume_keywords = extract_keywords_with_rake(resume_text)
    job_description_keywords = extract_keywords_with_rake(job_description)
    resume_skills = extract_skills(resume_text)
    job_description_skills = extract_skills(job_description)
    resume_experiences = extract_experiences(resume_text)
    job_description_experiences = extract_experiences(job_description)

    skills_match_score = calculate_matching_score(resume_skills, job_description_skills)
    experiences_match_score = calculate_matching_score(resume_experiences, job_description_experiences)
    overall_match_score = (skills_match_score + experiences_match_score) / 2

    # Calculate cosine similarity for a more accurate match score
    text_similarity_score = calculate_cosine_similarity(resume_text, job_description)
    final_match_score = (overall_match_score + text_similarity_score) / 2

    match_chart = generate_match_chart(final_match_score)

    # Summarize the job description
    summarized_job_description = summarize_text(job_description)

    # Generate analysis
    analysis = generate_analysis(resume_text, summarized_job_description)

    return render_template(
        'analysis.html',
        job_title=job_title,
        job_description=summarized_job_description,
        word_count=len(resume_text.split()),
        skills_matched=", ".join(resume_skills),
        experiences_matched=", ".join(resume_experiences),
        match_score="{:.2f}%".format(final_match_score),
        match_chart=match_chart,
        analysis=analysis
    )

if __name__ == '__main__':
    app.run(debug=True)
