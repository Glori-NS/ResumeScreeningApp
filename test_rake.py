from rake_nltk import Rake

# Initialize the Rake object
rake = Rake()

# Sample text
text = "This is a simple test text to extract keywords using RAKE."

# Extract keywords
rake.extract_keywords_from_text(text)
keywords = rake.get_ranked_phrases()

# Print the extracted keywords
print(keywords)

