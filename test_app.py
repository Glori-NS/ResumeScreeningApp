import unittest
from app import app
from io import BytesIO

class TestResumeScreeningApp(unittest.TestCase):
    # Set up the app for testing
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    # Test 1: Test the home page for correct HTTP response 
    def test_home_page(self):
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Welcome to <em>JustScreen</em>: Resume Review', response.data)

    # Test 2: Test file upload without a file
    def test_upload_page_without_file(self):
        response = self.app.post('/upload', data={}, follow_redirects=True)
        self.assertEqual(response.status_code, 400)  # Expecting bad request status
        self.assertIn(b'No selected file', response.data)


    # Test 3: Test file upload with an empty job description
    def test_upload_page_with_empty_job_description(self):
        data = {
            'job_description': '',
            'resume': (BytesIO(b'Sample resume content'), 'resume.txt')
        }
        response = self.app.post('/upload', data=data, follow_redirects=True)
        self.assertIn(b'Job description is required', response.data)


    # Test 4: Test uploading a valid file with job description
    def test_upload_valid_file(self):
        data = {
            'job_description': 'Software Developer with experience in Python',
            'resume': (BytesIO(b'Experienced Python Developer'), 'resume.txt')
        }
        response = self.app.post('/upload', data=data, content_type='multipart/form-data', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Analysis Summary', response.data)
        self.assertIn(b'Skills Matching Job Description:', response.data)
        self.assertIn(b'Overall Matching Score:', response.data)

    # Test 5: Test file upload with an invalid file type
    def test_invalid_file_type(self):
        data = {
            'job_description': 'Software Developer with experience in Python',
            'resume': (BytesIO(b'<?xml version="1.0" encoding="UTF-8"?>'), 'resume.xml')
        }
        response = self.app.post('/upload', data=data, content_type='multipart/form-data', follow_redirects=True)
        self.assertIn(b'Invalid file type', response.data)

    # Test 6: Test uploading a large file
    def test_large_file_upload(self):
        large_content = b'a' * (1024 * 1024 * 10)  # 10 MB of data
        data = {
            'job_description': 'Software Developer',
            'resume': (BytesIO(large_content), 'large_resume.txt')
        }
        response = self.app.post('/upload', data=data, content_type='multipart/form-data', follow_redirects=True)
        self.assertIn(b'File too large', response.data)


if __name__ == '__main__':
    unittest.main()
