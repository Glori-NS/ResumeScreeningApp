from flask import Flask, request, render_template
import os
import RAKE
import plotly.express as px
import pandas as pd
import numpy as np
import re
from sklearn.feature_extraction.text import TfidfVectorizer
import sqlite3

app = Flask(__name__)

# Define a custom stoplist for RAKE
custom_stoplist = [
    'and', 'or', 'but', 'with', 'the', 'a', 'an', 'of', 'to', 'in',
    'for', 'on', 'at', 'by', 'from', 'up', 'down', 'over', 'under', 'again',
    
]

rake = RAKE.Rake(custom_stoplist)

@app.route('/')
def home():
    # Improved homepage with basic styling
    return render_template('index.html')

def extract_keywords_with_rake(text):
    keywords = rake.run(text)
    return [k[0] for k in keywords]  # Return only keywords, excluding scores

def extract_experiences(text):
    # Improved regex for experience extraction
    experience_pattern = re.compile(r'\b(?:Manager|Engineer|Developer|Specialist|Technician)\b', re.IGNORECASE)
    experiences = experience_pattern.findall(text)
    return list(set(experiences))  # Return unique experiences

def calculate_matching_score(keywords1, keywords2):
    matched_keywords = set(keywords1).intersection(set(keywords2))
    if keywords2:
        return len(matched_keywords) / len(keywords2) * 100
    else:
        return 0

def generate_match_chart(match_score):
    # Generate match chart with improved visualization
    data = {'Type': ['Matched', 'Unmatched'], 'Score': [match_score, 100 - match_score]}
    df = pd.DataFrame(data)
    fig = px.pie(df, names='Type', values='Score', title='Match Score', hole=0.4)
    fig.update_traces(textinfo='percent+label')
    fig.update_layout(showlegend=True)
    return fig.to_html(full_html=False)

@app.route('/upload', methods=['POST'])
def upload_file():
    job_description = request.form['job_description']
    resume_file = request.files['resume']

    if resume_file.filename == '':
        return 'No selected file'
    if resume_file:
        resume_filename = os.path.join('uploads', resume_file.filename)
        resume_file.save(resume_filename)
        
        with open(resume_filename, 'r', encoding='utf-8', errors='ignore') as file:
            resume_text = file.read()

        resume_keywords = extract_keywords_with_rake(resume_text)
        job_description_keywords = extract_keywords_with_rake(job_description)
        resume_experiences = extract_experiences(resume_text)
        job_description_experiences = extract_experiences(job_description)

        skills_match_score = calculate_matching_score(resume_keywords, job_description_keywords)
        experiences_match_score = calculate_matching_score(resume_experiences, job_description_experiences)
        overall_match_score = (skills_match_score + experiences_match_score) / 2

        match_chart = generate_match_chart(overall_match_score)

        return render_template(
            'analysis.html',
            job_description=job_description,
            word_count=len(resume_text.split()),
            skills_matched=", ".join(resume_keywords),
            experiences_matched=", ".join(resume_experiences),
            match_score="{:.2f}%".format(overall_match_score),
            match_chart=match_chart
        )
    else:
        return 'No file part'

if __name__ == '__main__':
    app.run(debug=True)