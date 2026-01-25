# Quick Reference Guide

## Project at a Glance

### Key Files
- **[main.py](../main.py)** - Backend API (1700+ lines)
- **[static/index.html](../static/index.html)** - Main UI
- **[static/styles.css](../static/styles.css)** - Responsive mobile-first CSS
- **[requirements.txt](../requirements.txt)** - Python dependencies
- **[start.sh](../start.sh)** - Quick start script

### Documentation
- **[PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md)** - Architecture overview
- **[PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)** - File organization guide
- **[SYSTEM_LOGIC.md](SYSTEM_LOGIC.md)** - Flow and logic
- **[TECHNICAL_SPEC.md](TECHNICAL_SPEC.md)** - Technical details
- **[UI_UX_GUIDELINES.md](UI_UX_GUIDELINES.md)** - Design principles

### Payment Integration
- **[paddle/PADDLE_CONFIG.md](paddle/PADDLE_CONFIG.md)** - Setup guide
- **[paddle/PADDLE_IMPLEMENTATION.md](paddle/PADDLE_IMPLEMENTATION.md)** - Implementation
- **[paddle/PAYMENT_TESTING.md](paddle/PAYMENT_TESTING.md)** - Testing

### Deployment
- **[deployment/DEPLOYMENT.md](deployment/DEPLOYMENT.md)** - General guide
- **[deployment/RAILWAY_VOLUME_SETUP.md](deployment/RAILWAY_VOLUME_SETUP.md)** - Railway setup
- **[deployment/deploy-railway.sh](deployment/deploy-railway.sh)** - Deploy script

### Testing
- **[../tests/README.md](../tests/README.md)** - Test suite structure (being rewritten)

## Common Tasks

### Local Development
```bash
# Quick start (first time)
./start.sh

# Or manually with Docker
docker compose up -d --build

# View logs
docker compose logs -f

# Stop
docker compose down
```

### Environment Setup
```bash
# Copy environment template
cp .env.example .env

# Edit with your API keys
nano .env  # or your preferred editor
```

### Deployment
```bash
# Deploy to Railway
cd docs/deployment
./deploy-railway.sh

# Manual Railway deployment
railway up
```

### File Locations
- **Frontend**: `/static/` directory
- **Tests**: `/tests/` directory
- **Documentation**: `/docs/` directory
  - Payment: `/docs/paddle/`
  - Deployment: `/docs/deployment/`
- **Config**: Root directory (Dockerfile, docker-compose.yml, etc.)

## Key Features

### Current Implementation
- ✅ Step-by-step homework help with AI
- ✅ Image upload with drag-and-drop
- ✅ Mathematical equation rendering (KaTeX)
- ✅ Responsive mobile-first UI
- ✅ User authentication (JWT)
- ✅ Paddle Billing integration
- ✅ Usage limits (3 free scans, then $9.99/month)
- ✅ API key rotation (5 Google Gemini keys)
- ✅ Railway deployment with volume persistence

### Tech Stack
- **Backend**: FastAPI (Python 3.12)
- **Frontend**: Vanilla JavaScript (no frameworks)
- **AI**: Google Gemini 2.5 Flash
- **Payment**: Paddle Billing v2
- **Hosting**: Railway (cloud)
- **Math**: KaTeX 0.16.9
- **Styling**: Custom CSS (mobile-first)

## API Endpoints

### Public
- `GET /` - Main application
- `GET /login` - Authentication page
- `GET /health` - Health check

### Authentication Required
- `POST /upload` - Upload homework image
- `POST /analyze` - Analyze with AI
- `GET /usage` - Check usage limits

### Paddle Webhooks
- `POST /paddle/webhook` - Subscription events

## Environment Variables

### Required
```bash
GEMINI_API_KEY_1=your_key_here  # Primary Google Gemini key
PADDLE_API_KEY=your_key_here    # Paddle Billing key
```

### Optional (with defaults)
```bash
GEMINI_API_KEY_2-5=additional_keys  # For rotation
JWT_SECRET=auto_generated
PADDLE_WEBHOOK_SECRET=from_paddle_dashboard
```

## Project Status

### Completed (December 2024)
- ✅ Mobile UI optimization (uniform buttons, compact layout)
- ✅ Project file reorganization
- ✅ Documentation restructuring
- ✅ Duplicate file cleanup

### In Progress
- 🔄 Test suite rewrite (from scratch)

### Planned
- 📋 Expanded subject support
- 📋 Progress tracking
- 📋 Parent dashboard
- 📋 Multi-language support

## Support

### Live Application
**[socratesparent-production.up.railway.app](https://socratesparent-production.up.railway.app/)**

### Issues & Questions
Check documentation in `/docs/` or deployment logs in `/docs/deployment/deployment.log`

### Recent Changes
See [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) for December 2024 reorganization details.
