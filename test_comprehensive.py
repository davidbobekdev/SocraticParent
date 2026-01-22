#!/usr/bin/env python3
"""
Comprehensive End-to-End Test Script for Socratic Parent
Tests both the backend API and simulates frontend functionality
"""

import sys
import time
import requests
import json
from pathlib import Path
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont

# Color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

# Configuration
BASE_URL = "http://localhost:8000"
TEST_IMAGES_DIR = Path("test_images")
RESULTS_FILE = "test_results.json"

class TestResult:
    def __init__(self):
        self.total = 0
        self.passed = 0
        self.failed = 0
        self.skipped = 0
        self.details = []
    
    def add(self, name, status, message="", data=None):
        self.total += 1
        if status == "PASS":
            self.passed += 1
            print(f"{Colors.OKGREEN}✓ PASS{Colors.ENDC} - {name}")
        elif status == "FAIL":
            self.failed += 1
            print(f"{Colors.FAIL}✗ FAIL{Colors.ENDC} - {name}")
            if message:
                print(f"  {Colors.FAIL}└─ {message}{Colors.ENDC}")
        elif status == "SKIP":
            self.skipped += 1
            print(f"{Colors.WARNING}⊘ SKIP{Colors.ENDC} - {name}")
            if message:
                print(f"  {Colors.WARNING}└─ {message}{Colors.ENDC}")
        
        self.details.append({
            "name": name,
            "status": status,
            "message": message,
            "data": data
        })
    
    def summary(self):
        print(f"\n{Colors.BOLD}{'='*70}{Colors.ENDC}")
        print(f"{Colors.BOLD}TEST SUMMARY{Colors.ENDC}")
        print(f"{Colors.BOLD}{'='*70}{Colors.ENDC}")
        print(f"Total Tests:  {self.total}")
        print(f"{Colors.OKGREEN}Passed:       {self.passed}{Colors.ENDC}")
        print(f"{Colors.FAIL}Failed:       {self.failed}{Colors.ENDC}")
        print(f"{Colors.WARNING}Skipped:      {self.skipped}{Colors.ENDC}")
        
        if self.failed == 0:
            print(f"\n{Colors.OKGREEN}{Colors.BOLD}🎉 ALL TESTS PASSED!{Colors.ENDC}")
        else:
            print(f"\n{Colors.FAIL}{Colors.BOLD}⚠️  SOME TESTS FAILED{Colors.ENDC}")
        
        # Save results to file
        with open(RESULTS_FILE, 'w') as f:
            json.dump({
                "summary": {
                    "total": self.total,
                    "passed": self.passed,
                    "failed": self.failed,
                    "skipped": self.skipped
                },
                "details": self.details
            }, f, indent=2)
        print(f"\n{Colors.OKCYAN}Results saved to: {RESULTS_FILE}{Colors.ENDC}")

def create_test_images():
    """Create realistic test homework images"""
    TEST_IMAGES_DIR.mkdir(exist_ok=True)
    
    print(f"\n{Colors.BOLD}Creating test images...{Colors.ENDC}")
    
    test_cases = [
        {
            "name": "math_addition.jpg",
            "text": ["Math Problem:", "", "15 + 27 = ?", "", "Show your work"]
        },
        {
            "name": "math_multiplication.jpg",
            "text": ["Multiplication:", "", "8 × 7 = ?"]
        },
        {
            "name": "math_fractions.jpg",
            "text": ["Fractions:", "", "1/2 + 1/4 = ?", "", "Simplify your answer"]
        },
        {
            "name": "word_problem.jpg",
            "text": ["Word Problem:", "", "Sarah has 15 apples.", "She gives 6 to her friend.", "How many apples does", "Sarah have left?"]
        },
        {
            "name": "algebra.jpg",
            "text": ["Algebra:", "", "Solve for x:", "2x + 5 = 13"]
        }
    ]
    
    for case in test_cases:
        img_path = TEST_IMAGES_DIR / case["name"]
        img = Image.new('RGB', (600, 400), color='white')
        draw = ImageDraw.Draw(img)
        
        # Try to use a nicer font, fall back to default
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
            font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 32)
        except:
            font = ImageFont.load_default()
            font_title = font
        
        y_position = 50
        for i, line in enumerate(case["text"]):
            current_font = font_title if i == 0 else font
            draw.text((50, y_position), line, fill='black', font=current_font)
            y_position += 50 if i == 0 else 40
        
        img.save(img_path, 'JPEG', quality=95)
        print(f"  Created: {img_path}")

def check_server_running():
    """Check if the server is accessible"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def test_health_endpoint(results):
    """Test the /health endpoint"""
    print(f"\n{Colors.BOLD}Testing Health Endpoint...{Colors.ENDC}")
    
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        data = response.json()
        
        if response.status_code == 200:
            results.add("Health endpoint responds", "PASS")
        else:
            results.add("Health endpoint responds", "FAIL", f"Status code: {response.status_code}")
        
        # Check response structure
        required_fields = ['status', 'message', 'ai_configured']
        if all(field in data for field in required_fields):
            results.add("Health response has required fields", "PASS")
        else:
            missing = [f for f in required_fields if f not in data]
            results.add("Health response has required fields", "FAIL", f"Missing: {missing}")
        
        # Check AI configuration
        if data.get('ai_configured'):
            results.add("AI (Gemini) is configured", "PASS")
        else:
            results.add("AI (Gemini) is configured", "SKIP", "AI not configured - tests will use fallback")
        
    except Exception as e:
        results.add("Health endpoint responds", "FAIL", str(e))

def test_static_files(results):
    """Test that static files are accessible"""
    print(f"\n{Colors.BOLD}Testing Static Files...{Colors.ENDC}")
    
    files_to_test = [
        ("index.html", "/"),
        ("styles.css", "/static/styles.css"),
        ("app.js", "/static/app.js")
    ]
    
    for name, path in files_to_test:
        try:
            response = requests.get(f"{BASE_URL}{path}", timeout=5)
            if response.status_code == 200:
                results.add(f"Static file: {name}", "PASS")
            else:
                results.add(f"Static file: {name}", "FAIL", f"Status: {response.status_code}")
        except Exception as e:
            results.add(f"Static file: {name}", "FAIL", str(e))

def test_analyze_endpoint(results, image_path, grade=None):
    """Test the /analyze endpoint with a specific image"""
    test_name = f"Analyze: {image_path.name}"
    
    try:
        with open(image_path, 'rb') as f:
            files = {'file': ('homework.jpg', f, 'image/jpeg')}
            data = {}
            if grade:
                data['grade'] = grade
            
            response = requests.post(f"{BASE_URL}/analyze", files=files, data=data, timeout=30)
        
        if response.status_code != 200:
            results.add(test_name, "FAIL", f"Status: {response.status_code}")
            return None
        
        result = response.json()
        
        # Check required fields
        required_fields = ['subject', 'questions', 'behavioral_tip']
        if not all(field in result for field in required_fields):
            missing = [f for f in required_fields if f not in result]
            results.add(test_name, "FAIL", f"Missing fields: {missing}")
            return None
        
        # Check questions structure
        questions = result.get('questions', {})
        required_questions = ['foundation', 'bridge', 'mastery']
        if not all(q in questions for q in required_questions):
            missing = [q for q in required_questions if q not in questions]
            results.add(test_name, "FAIL", f"Missing questions: {missing}")
            return None
        
        # Validate question quality
        for q_type, q_text in questions.items():
            if not isinstance(q_text, str) or len(q_text) < 10:
                results.add(test_name, "FAIL", f"Invalid {q_type} question")
                return None
        
        # Check optional fields
        has_solution = 'solution_steps' in result and isinstance(result['solution_steps'], list)
        has_example = 'example_approach' in result
        
        results.add(test_name, "PASS", f"Has solution: {has_solution}, Has example: {has_example}", data=result)
        return result
        
    except Exception as e:
        results.add(test_name, "FAIL", str(e))
        return None

def test_all_homework_types(results):
    """Test analysis with different types of homework"""
    print(f"\n{Colors.BOLD}Testing Homework Analysis...{Colors.ENDC}")
    
    if not TEST_IMAGES_DIR.exists() or not list(TEST_IMAGES_DIR.glob("*.jpg")):
        results.add("Test images available", "SKIP", "No test images found")
        return
    
    results.add("Test images available", "PASS")
    
    # Test each image
    for img_path in sorted(TEST_IMAGES_DIR.glob("*.jpg")):
        # Determine appropriate grade level
        if "algebra" in img_path.name:
            grade = "9-12"
        elif "fractions" in img_path.name:
            grade = "6-8"
        else:
            grade = "3-5"
        
        test_analyze_endpoint(results, img_path, grade)
        time.sleep(1)  # Rate limiting

def test_error_handling(results):
    """Test error handling"""
    print(f"\n{Colors.BOLD}Testing Error Handling...{Colors.ENDC}")
    
    # Test without file
    try:
        response = requests.post(f"{BASE_URL}/analyze", timeout=5)
        if response.status_code == 422:  # FastAPI validation error
            results.add("Error handling: No file", "PASS")
        else:
            results.add("Error handling: No file", "FAIL", f"Expected 422, got {response.status_code}")
    except Exception as e:
        results.add("Error handling: No file", "FAIL", str(e))
    
    # Test with invalid file type
    try:
        files = {'file': ('test.txt', b'Not an image', 'text/plain')}
        response = requests.post(f"{BASE_URL}/analyze", files=files, timeout=5)
        if response.status_code in [400, 422]:
            results.add("Error handling: Invalid file type", "PASS")
        else:
            results.add("Error handling: Invalid file type", "FAIL", f"Status: {response.status_code}")
    except Exception as e:
        results.add("Error handling: Invalid file type", "FAIL", str(e))

def test_response_quality(results):
    """Test the quality of AI responses"""
    print(f"\n{Colors.BOLD}Testing Response Quality...{Colors.ENDC}")
    
    # Create a simple test image
    test_img_path = TEST_IMAGES_DIR / "math_addition.jpg"
    if not test_img_path.exists():
        results.add("Response quality test", "SKIP", "Test image not found")
        return
    
    result = test_analyze_endpoint(results, test_img_path, "3-5")
    if not result:
        results.add("Response quality test", "SKIP", "Analysis failed")
        return
    
    # Check that questions don't give away the answer
    questions = result.get('questions', {})
    contains_answer = False
    for q_text in questions.values():
        if "42" in q_text or "15 + 27" in q_text:
            contains_answer = True
            break
    
    if not contains_answer:
        results.add("Questions don't reveal answer", "PASS")
    else:
        results.add("Questions don't reveal answer", "FAIL", "Questions contain the answer")
    
    # Check solution steps quality
    solution_steps = result.get('solution_steps', [])
    if solution_steps and len(solution_steps) >= 2:
        results.add("Solution has multiple steps", "PASS", f"Found {len(solution_steps)} steps")
        
        # Check if solution contains actual calculations
        has_calculations = any(any(op in step for op in ['+', '-', '×', '÷', '=']) for step in solution_steps)
        if has_calculations:
            results.add("Solution contains calculations", "PASS")
        else:
            results.add("Solution contains calculations", "FAIL", "No calculations found")
    else:
        results.add("Solution has multiple steps", "FAIL", f"Only {len(solution_steps)} steps")

def test_grade_level_adaptation(results):
    """Test that responses adapt to grade level"""
    print(f"\n{Colors.BOLD}Testing Grade Level Adaptation...{Colors.ENDC}")
    
    test_img_path = TEST_IMAGES_DIR / "math_multiplication.jpg"
    if not test_img_path.exists():
        results.add("Grade level adaptation", "SKIP", "Test image not found")
        return
    
    # Test with different grade levels
    grade_levels = ["K-2", "3-5", "6-8", "9-12"]
    responses = {}
    
    for grade in grade_levels:
        result = test_analyze_endpoint(results, test_img_path, grade)
        if result:
            responses[grade] = result
        time.sleep(1)
    
    if len(responses) >= 2:
        # Check that responses differ
        questions_list = [r['questions']['foundation'] for r in responses.values()]
        if len(set(questions_list)) > 1:
            results.add("Responses vary by grade level", "PASS")
        else:
            results.add("Responses vary by grade level", "FAIL", "All responses identical")
    else:
        results.add("Grade level adaptation", "SKIP", "Not enough successful analyses")

def main():
    print(f"{Colors.HEADER}{Colors.BOLD}")
    print("=" * 70)
    print("  SOCRATIC PARENT - COMPREHENSIVE TEST SUITE")
    print("=" * 70)
    print(f"{Colors.ENDC}")
    
    # Initialize results tracker
    results = TestResult()
    
    # Check if server is running
    print(f"\n{Colors.BOLD}Checking Server Status...{Colors.ENDC}")
    if not check_server_running():
        print(f"{Colors.FAIL}✗ Server is not running at {BASE_URL}{Colors.ENDC}")
        print(f"\n{Colors.WARNING}Please start the server first:{Colors.ENDC}")
        print(f"  {Colors.OKCYAN}docker compose up -d{Colors.ENDC}")
        print(f"  or")
        print(f"  {Colors.OKCYAN}python main.py{Colors.ENDC}")
        sys.exit(1)
    else:
        print(f"{Colors.OKGREEN}✓ Server is running{Colors.ENDC}")
        results.add("Server is running", "PASS")
    
    # Create test images
    create_test_images()
    
    # Run test suites
    test_health_endpoint(results)
    test_static_files(results)
    test_all_homework_types(results)
    test_error_handling(results)
    test_response_quality(results)
    test_grade_level_adaptation(results)
    
    # Print summary
    results.summary()
    
    # Exit with appropriate code
    sys.exit(0 if results.failed == 0 else 1)

if __name__ == "__main__":
    main()
