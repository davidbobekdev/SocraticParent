# Project Structure

## Overview
This document describes the organized file structure of Socratic Parent after the December 2024 reorganization.

## Directory Layout

### `/` (Root)
- **main.py** - Complete FastAPI backend (1700+ lines)
- **requirements.txt** - Python dependencies
- **start.sh** - Application startup script
- **users.json** - User data storage (gitignored in production)
- **Dockerfile** - Container configuration
- **docker-compose.yml** - Service orchestration
- **railway.json** - Railway deployment configuration
- **fly.toml** - Fly.io deployment configuration

### `/static/` - Frontend Assets
All user-facing UI files:
- **index.html** - Main application interface
- **app.js** - Frontend JavaScript logic
- **styles.css** - Application styles (mobile-first responsive)
- **login.html** - Authentication page
- **login.js** - Login/registration logic
- **landing.html** - Landing page

### `/docs/` - Documentation
Project documentation and guides:
- **PROJECT_OVERVIEW.md** - High-level architecture
- **SYSTEM_LOGIC.md** - System flow and logic
- **TECHNICAL_SPEC.md** - Technical specifications
- **UI_UX_GUIDELINES.md** - Design principles and guidelines
- **PROJECT_STRUCTURE.md** - This file

#### `/docs/paddle/` - Payment Integration
Paddle Billing documentation:
- **PADDLE_CONFIG.md** - Configuration guide
- **PADDLE_CONFIG_PRODUCTION.md** - Production setup
- **PADDLE_IMPLEMENTATION.md** - Implementation details
- **PAYMENT_TESTING.md** - Testing procedures
- **DEPLOY_PADDLE_CHECKLIST.md** - Deployment checklist

#### `/docs/deployment/` - Deployment Guides
Platform-specific deployment documentation:
- **DEPLOYMENT.md** - General deployment guide
- **RAILWAY_VOLUME_SETUP.md** - Railway volume configuration
- **deploy-railway.sh** - Railway deployment script
- **deploy.sh** - Generic deployment script
- **deployment.log** - Deployment history

### `/tests/` - Test Suite
Testing infrastructure (currently being rewritten):
- **README.md** - Test structure and plans
- Test files will be rewritten from scratch with proper organization

### `/.github/` - GitHub Configuration
GitHub Actions workflows and templates

## Recent Changes (December 2024)

### Reorganization Summary
1. **Tests Consolidated**: All test files moved to `/tests/` directory
2. **Documentation Organized**: Created `/docs/paddle/` and `/docs/deployment/` subdirectories
3. **Duplicates Removed**: Deleted duplicate files from root (app.js, index.html, styles.css)
4. **Clean Root**: Root directory now contains only essential project files

### File Moves
- `test_*.py`, `test_*.sh`, `test_*.html`, `test_*.txt` → `/tests/`
- `run_tests.sh` → `/tests/`
- `PADDLE_*.md`, `PAYMENT_TESTING.md` → `/docs/paddle/`
- `DEPLOY*.md`, `RAILWAY*.md`, `deploy*.sh`, `deployment.log` → `/docs/deployment/`
- `API_KEY_ROTATION_SETUP.md`, `TESTING.md`, `TEST_SUITE_README.md` → `/docs/`

### Verified Clean State
- No hardcoded references to moved files in main.py
- All deployment scripts using relative paths
- Frontend assets correctly reference static/ directory

## Best Practices

### Adding New Files
- **Frontend code** → `/static/`
- **Backend code** → Root or create `/src/` if codebase grows
- **Tests** → `/tests/` with appropriate subdirectories
- **Documentation** → `/docs/` with appropriate subdirectories
- **Deployment configs** → `/docs/deployment/`
- **Payment docs** → `/docs/paddle/`

### File Naming Conventions
- Use lowercase with hyphens for documentation: `project-overview.md`
- Use underscores for Python files: `test_backend.py`
- Use descriptive names that indicate purpose

### Directory Organization
- Keep root directory clean (< 20 files)
- Group related files in subdirectories
- Use README.md in each directory to explain structure
- Maintain parallel structure for related content (e.g., all Paddle docs together)

## Future Improvements
- [ ] Consider `/src/` directory if backend code exceeds 2000 lines
- [ ] Add `/migrations/` for database migrations if needed
- [ ] Create `/scripts/` for utility scripts
- [ ] Reorganize tests into unit/, integration/, e2e/ subdirectories
- [ ] Add API documentation in `/docs/api/`
