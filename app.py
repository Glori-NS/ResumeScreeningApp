from flask import Flask, request, render_template
import os
import RAKE
import plotly.express as px
import pandas as pd
import re
import spacy
import fitz
import textract
from docx import Document
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

app = Flask(__name__)

# Load Spacy model for Named Entity Recognition
nlp = spacy.load('en_core_web_sm')

# Define a custom stoplist for RAKE
custom_stoplist = [
    'and', 'or', 'but', 'with', 'the', 'a', 'an', 'of', 'to', 'in',
    'for', 'on', 'at', 'by', 'from', 'up', 'down', 'over', 'under', 'again',
]

rake = RAKE.Rake(custom_stoplist)

# Comprehensive skill list (expanded to fit most industries)
common_skills = [
    # General Skills
    'communication', 'teamwork', 'leadership', 'problem-solving', 'time management', 'critical thinking',
    'creativity', 'adaptability', 'work ethic', 'interpersonal skills', 'organization', 'attention to detail',
    'customer service', 'project management', 'strategic planning', 'conflict resolution', 'decision making',
    'multitasking', 'presentation skills', 'negotiation', 'public speaking', 'analytical skills', 'research',

    # Technical Skills
    'python', 'java', 'c++', 'javascript', 'html', 'css', 'sql', 'r', 'matlab', 'machine learning',
    'data analysis', 'data science', 'big data', 'software development', 'web development', 'networking',
    'cloud computing', 'cybersecurity', 'technical support', 'linux', 'windows', 'macos', 'docker', 'kubernetes',
    'aws', 'azure', 'gcp', 'devops', 'ci/cd', 'microservices', 'api development', 'blockchain', 'artificial intelligence',
    'robotics', 'iot', 'mobile development', 'ux/ui design', 'system administration', 'virtualization', 'sql server',
    'nosql', 'tensorflow', 'pytorch', 'hadoop', 'spark', 'etl', 'sas', 'stata', 'tableau', 'power bi', 'excel',

    # Healthcare Skills
    'patient care', 'clinical research', 'medical terminology', 'emr', 'ehr', 'phlebotomy', 'first aid', 'cpr', 'surgical technology',
    'nursing', 'medication administration', 'public health', 'healthcare management', 'disease prevention', 'telemedicine',
    'diagnostic testing', 'radiology', 'medical coding', 'medical billing', 'nutrition', 'physical therapy', 'occupational therapy',
    'pharmacy', 'mental health', 'patient advocacy',

    # Finance Skills
    'accounting', 'financial analysis', 'budgeting', 'forecasting', 'investment', 'risk management', 'auditing', 'taxation',
    'financial modeling', 'payroll', 'banking', 'insurance', 'financial planning', 'compliance', 'treasury', 'credit analysis',
    'asset management', 'cost accounting', 'mergers and acquisitions', 'portfolio management', 'securities', 'wealth management',

    # Marketing Skills
    'digital marketing', 'seo', 'sem', 'content marketing', 'social media marketing', 'email marketing', 'advertising', 'branding',
    'market research', 'copywriting', 'crm', 'marketing automation', 'ppc', 'affiliate marketing', 'event planning', 'public relations',
    'graphic design', 'video production', 'photography', 'web analytics', 'google analytics', 'adobe creative suite', 'salesforce',

    # Education Skills
    'curriculum development', 'lesson planning', 'classroom management', 'educational technology', 'special education', 'teaching',
    'e-learning', 'assessment', 'instructional design', 'training and development', 'student counseling', 'academic advising',
    'tutoring', 'early childhood education', 'adult education', 'lms', 'school administration', 'educational research',

    # Engineering Skills
    'mechanical engineering', 'electrical engineering', 'civil engineering', 'structural engineering', 'chemical engineering',
    'environmental engineering', 'biomedical engineering', 'aerospace engineering', 'manufacturing', 'quality control', 'cad',
    'cam', 'solidworks', 'autocad', 'engineering design', 'sustainability', 'project engineering', 'systems engineering',
    'product development', 'testing', 'technical writing', 'lean manufacturing', 'six sigma', 'automation', 'robotics',

    # Legal Skills
    'legal research', 'litigation', 'contract law', 'intellectual property', 'corporate law', 'compliance', 'legal writing', 'mediation',
    'arbitration', 'legal documentation', 'case management', 'court procedures', 'family law', 'criminal law', 'employment law',
    'real estate law', 'tax law', 'immigration law', 'legal compliance', 'due diligence', 'regulatory affairs',

    # Sales Skills
    'sales strategy', 'lead generation', 'account management', 'customer relationship management', 'negotiation skills', 'b2b sales',
    'b2c sales', 'salesforce', 'sales presentations', 'closing techniques', 'prospecting', 'sales forecasting', 'retail sales',
    'direct sales', 'telemarketing', 'territory management', 'business development', 'cold calling', 'upselling', 'cross-selling',

    # Human Resources Skills
    'recruitment', 'employee relations', 'hr management', 'performance management', 'training and development', 'compensation and benefits',
    'payroll management', 'hr policies', 'talent acquisition', 'employee engagement', 'labor law', 'organizational development',
    'succession planning', 'hr analytics', 'diversity and inclusion', 'hr software', 'conflict resolution', 'benefits administration',

    # Operations Skills
    'supply chain management', 'logistics', 'inventory management', 'operations management', 'procurement', 'vendor management',
    'production planning', 'lean manufacturing', 'six sigma', 'quality assurance', 'warehouse management', 'fleet management',
    'materials management', 'logistics management', 'production management', 'transportation management', 'workflow optimization',

    # Creative Skills
    'graphic design', 'video editing', 'animation', 'photography', 'illustration', 'creative direction', '3d modeling', 'adobe photoshop',
    'adobe illustrator', 'adobe premiere pro', 'adobe after effects', 'final cut pro', 'design thinking', 'creative writing', 'storytelling',
    'branding', 'visual design', 'user experience', 'user interface', 'art direction', 'music production', 'sound design', 'copywriting'
]

@app.route('/')
def home():
    return render_template('index.html')

def extract_keywords_with_rake(text):
    keywords = rake.run(text)
    return [k[0].lower() for k in keywords]

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

@app.route('/upload', methods=['POST'])
def upload_file():
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

    resume_text = resume_content.decode('utf-8', errors='ignore')

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

    return render_template(
        'analysis.html',
        job_description=job_description,
        word_count=len(resume_text.split()),
        skills_matched=", ".join(resume_skills),
        experiences_matched=", ".join(resume_experiences),
        match_score="{:.2f}%".format(final_match_score),
        match_chart=match_chart
    )

if __name__ == '__main__':
    app.run(debug=True)
