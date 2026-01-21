#!/usr/bin/env python3
"""
Unit tests for Socratic Parent API
Run with: python3 test_api_unit.py
"""

import unittest
import requests
import json
import os
import sys
from pathlib import Path

BASE_URL = "http://localhost:8000"
TEST_IMAGE_PATH = "test_homework.jpg"

class TestSocraticParentAPI(unittest.TestCase):
    """Test suite for Socratic Parent API endpoints"""
    
    @classmethod
    def setUpClass(cls):
        """Check if API is accessible before running tests"""
        try:
            response = requests.get(f"{BASE_URL}/health", timeout=5)
            if response.status_code != 200:
                print("❌ API is not accessible. Please ensure the application is running.")
                sys.exit(1)
        except requests.exceptions.RequestException:
            print("❌ Cannot connect to API. Please ensure Docker container is running.")
            sys.exit(1)
            
        # Ensure test image exists
        if not Path(TEST_IMAGE_PATH).exists():
            print("⚠️  Test image not found. Creating one...")
            cls.create_test_image()
    
    @staticmethod
    def create_test_image():
        """Create a simple test image"""
        try:
            from PIL import Image, ImageDraw
            img = Image.new('RGB', (400, 200), color='white')
            draw = ImageDraw.Draw(img)
            draw.text((20, 20), 'Test: 2 + 2 = ?', fill='black')
            img.save(TEST_IMAGE_PATH, 'JPEG')
            print(f"✅ Created {TEST_IMAGE_PATH}")
        except Exception as e:
            print(f"❌ Could not create test image: {e}")
            sys.exit(1)
    
    def test_health_endpoint(self):
        """Test /health endpoint returns correct structure"""
        response = requests.get(f"{BASE_URL}/health")
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIn('status', data)
        self.assertIn('message', data)
        self.assertIn('ai_configured', data)
        self.assertEqual(data['status'], 'healthy')
        self.assertTrue(data['ai_configured'])
    
    def test_root_endpoint(self):
        """Test / returns HTML"""
        response = requests.get(BASE_URL)
        self.assertEqual(response.status_code, 200)
        self.assertIn('text/html', response.headers.get('content-type', ''))
        self.assertIn('Socratic Parent', response.text)
    
    def test_analyze_endpoint_structure(self):
        """Test /analyze endpoint returns correct JSON structure"""
        with open(TEST_IMAGE_PATH, 'rb') as f:
            files = {'file': f}
            data = {'grade': '6-8'}
            response = requests.post(f"{BASE_URL}/analyze", files=files, data=data)
        
        self.assertEqual(response.status_code, 200)
        result = response.json()
        
        # Check required fields
        self.assertIn('subject', result)
        self.assertIn('questions', result)
        self.assertIn('behavioral_tip', result)
        
        # Check questions structure
        questions = result['questions']
        self.assertIn('foundation', questions)
        self.assertIn('bridge', questions)
        self.assertIn('mastery', questions)
        
        # Check all questions are non-empty strings
        self.assertIsInstance(questions['foundation'], str)
        self.assertGreater(len(questions['foundation']), 10)
        self.assertIsInstance(questions['bridge'], str)
        self.assertGreater(len(questions['bridge']), 10)
        self.assertIsInstance(questions['mastery'], str)
        self.assertGreater(len(questions['mastery']), 10)
    
    def test_analyze_endpoint_optional_fields(self):
        """Test optional fields in /analyze response"""
        with open(TEST_IMAGE_PATH, 'rb') as f:
            files = {'file': f}
            response = requests.post(f"{BASE_URL}/analyze", files=files)
        
        result = response.json()
        
        # Check optional fields if present
        if 'solution_steps' in result:
            self.assertIsInstance(result['solution_steps'], list)
            if len(result['solution_steps']) > 0:
                self.assertIsInstance(result['solution_steps'][0], str)
        
        if 'example_approach' in result:
            self.assertIsInstance(result['example_approach'], str)
    
    def test_analyze_without_file(self):
        """Test /analyze without file returns error"""
        response = requests.post(f"{BASE_URL}/analyze")
        self.assertEqual(response.status_code, 422)  # Unprocessable Entity
    
    def test_analyze_with_grade(self):
        """Test /analyze with grade parameter"""
        with open(TEST_IMAGE_PATH, 'rb') as f:
            files = {'file': f}
            data = {'grade': '9-12'}
            response = requests.post(f"{BASE_URL}/analyze", files=files, data=data)
        
        self.assertEqual(response.status_code, 200)
    
    def test_static_files(self):
        """Test static files are accessible"""
        endpoints = ['/static/app.js', '/static/styles.css', '/static/index.html']
        
        for endpoint in endpoints:
            response = requests.get(f"{BASE_URL}{endpoint}")
            self.assertEqual(response.status_code, 200, f"Failed to access {endpoint}")
    
    def test_solution_steps_contain_calculations(self):
        """Test that solution steps contain actual numbers/calculations"""
        with open(TEST_IMAGE_PATH, 'rb') as f:
            files = {'file': f}
            response = requests.post(f"{BASE_URL}/analyze", files=files)
        
        result = response.json()
        
        if 'solution_steps' in result and len(result['solution_steps']) > 0:
            # Join all steps and check for numbers
            all_steps = ' '.join(result['solution_steps'])
            has_numbers = any(char.isdigit() for char in all_steps)
            self.assertTrue(has_numbers, "Solution steps should contain numbers/calculations")

class TestErrorHandling(unittest.TestCase):
    """Test error handling and edge cases"""
    
    def test_invalid_file_type(self):
        """Test uploading non-image file"""
        # Create a text file
        with open('test_text.txt', 'w') as f:
            f.write('This is not an image')
        
        try:
            with open('test_text.txt', 'rb') as f:
                files = {'file': f}
                response = requests.post(f"{BASE_URL}/analyze", files=files)
            
            # Should either reject or handle gracefully
            self.assertIn(response.status_code, [400, 422, 500])
        finally:
            os.remove('test_text.txt')
    
    def test_very_large_grade_parameter(self):
        """Test with unusual grade parameter"""
        with open(TEST_IMAGE_PATH, 'rb') as f:
            files = {'file': f}
            data = {'grade': 'invalid-grade'}
            response = requests.post(f"{BASE_URL}/analyze", files=files, data=data)
        
        # Should still process (grade is optional validation)
        self.assertEqual(response.status_code, 200)

def run_tests():
    """Run all tests and return results"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    suite.addTests(loader.loadTestsFromTestCase(TestSocraticParentAPI))
    suite.addTests(loader.loadTestsFromTestCase(TestErrorHandling))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "="*60)
    print("📊 Test Summary")
    print("="*60)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.wasSuccessful():
        print("\n✅ All tests passed!")
        return 0
    else:
        print("\n❌ Some tests failed")
        return 1

if __name__ == '__main__':
    sys.exit(run_tests())
