# Testing Guide

## Automated Test Suite

### Quick Test
```bash
./run_tests.sh
```

This comprehensive test suite checks:
- ✅ Docker environment
- ✅ Container health
- ✅ API endpoints
- ✅ Response structure
- ✅ Configuration files
- ✅ Documentation completeness
- ✅ Container logs for errors

### Unit Tests
```bash
python3 test_api_unit.py
```

Python unit tests that verify:
- API endpoint responses
- JSON structure validation
- Error handling
- Solution steps contain actual calculations
- Edge cases

### Manual API Test
```bash
./test_api_detailed.sh test_homework.jpg
```

Interactive test with detailed output showing:
- Health check
- Full API response
- HTTP status codes
- Error messages if any

## Test Files

1. **run_tests.sh** - Main automated test suite (bash)
2. **test_api_unit.py** - Unit tests (Python)
3. **test_api_detailed.sh** - Manual testing with output
4. **test_homework.jpg** - Sample test image (auto-generated)

## Continuous Integration

To add to CI/CD pipeline:

```yaml
# Example GitHub Actions
- name: Run Tests
  run: |
    docker compose up -d
    sleep 5
    ./run_tests.sh
```

## Expected Test Results

All tests should pass:
```
Tests Passed: 25+
Tests Failed: 0
🎉 All tests passed!
```

## Troubleshooting

If tests fail:
1. Ensure Docker is running
2. Check API is accessible: `curl http://localhost:8000/health`
3. View logs: `docker compose logs --tail=50`
4. Restart: `docker compose restart`
