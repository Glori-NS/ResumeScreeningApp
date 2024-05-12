
import unittest
from app import app

class TestJustScreen(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_home_page(self):
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'JustScreen', response.data)

    def test_upload_file(self):
        data = {
            'job_description': 'Software Engineer with experience in Python and machine learning',
            'resume': (BytesIO(b'Sample resume text'), 'resume.txt')
        }
        response = self.app.post('/upload', data=data, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Resume Analysis', response.data)
        self.assertIn(b'Word Count:', response.data)
        self.assertIn(b'Skills Matched:', response.data)
        self.assertIn(b'Experiences Matched:', response.data)
        self.assertIn(b'Match Score:', response.data)

if __name__ == '__main__':
    unittest.main()
