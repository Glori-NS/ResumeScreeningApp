import sqlite3

connection = sqlite3.connect('resume.db')
cursor = connection.cursor()

# Create table
cursor.execute('''CREATE TABLE IF NOT EXISTS jobs
               (id INTEGER PRIMARY KEY, description TEXT)''')

# Insert a job description (example)
cursor.execute('''INSERT INTO jobs (description)
                  VALUES ('Data Scientist with experience in Python and SQL')''')

connection.commit()
connection.close()
