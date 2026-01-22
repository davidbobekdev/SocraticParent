# 🎓 Socratic Parent

**The Anti-Homework-Solver for the 2026 AI-Saturated Era**

Transform homework battles into meaningful learning moments using AI-powered Socratic questioning.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.12-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104-green.svg)

## 🌐 Try It Now!

**[Use Socratic Parent Online →](https://yourusername.github.io/SocraticParent/)**

No installation required! Just:
1. Visit the link above
2. Get a free [Google Gemini API key](https://makersuite.google.com/app/apikey)
3. Upload your child's homework
4. Get instant Socratic coaching guidance

> Your API key is stored locally in your browser and never sent anywhere except Google's API.

## 🌟 Philosophy

In an age where AI can instantly solve any homework problem, we take a different approach:
- **Friction over Speed**: We deliberately slow down to create learning moments
- **Questions over Answers**: Guide children to discover solutions themselves
- **Connection over Conflict**: Turn homework time into quality parent-child interaction

## ✨ Features

- **📸 Image Upload**: Upload homework photos via drag-and-drop or camera
- **🤔 Socratic Questions**: Three-tier questioning system (Spark, Climb, Summit)
- **🎯 Smart Analysis**: Google Gemini AI analyzes homework and generates coaching scripts
- **📝 Progressive Solution Reveal**: Step-by-step solutions with actual calculations (last resort)
- **🔒 Privacy First**: Images processed securely, never stored
- **👨‍👩‍👧 Parent Mode**: Example approaches that help parents understand concepts

## 🚀 Quick Start

### Option 1: Use Online (Easiest!)

Visit **[https://yourusername.github.io/SocraticParent/](https://yourusername.github.io/SocraticParent/)**

No installation needed! Just get a free [Gemini API key](https://makersuite.google.com/app/apikey) and start using it immediately.

### Option 2: Self-Host with Docker

#### Prerequisites

- Docker and Docker Compose
- Google Gemini API key ([Get one here](https://makersuite.google.com/app/apikey))

#### Installation

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/SocraticParent.git
cd SocraticParent
```

2. **Configure environment**
```bash
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY
```

3. **Start the application**
```bash
./start.sh
# Or manually:
docker compose up -d --build
```

4. **Access the application**
Open your browser to: `http://localhost:8000`

## 🏗️ Architecture

```
├── main.py              # FastAPI backend
├── static/              # Frontend assets
│   ├── index.html      # Main UI
│   ├── app.js          # JavaScript logic
│   └── styles.css      # Design system
├── Dockerfile           # Container configuration
├── docker-compose.yml   # Service orchestration
├── requirements.txt     # Python dependencies
└── docs/               # Project documentation
    ├── PROJECT_OVERVIEW.md
    ├── SYSTEM_LOGIC.md
    ├── TECHNICAL_SPEC.md
    └── UI_UX_GUIDELINES.md
```

## 📋 API Endpoints

### `POST /analyze`
Analyzes homework image and returns Socratic coaching script
- **Input**: Multipart form with `file` (image) and optional `grade` (K-2, 3-5, 6-8, 9-12)
- **Output**: JSON with questions, tips, example approach, and solution steps

### `GET /health`
Health check endpoint
- **Output**: System status and AI configuration state

## 🎨 Design System

- **Colors**: Indigo primary (#4F46E5), emerald secondary (#10B981)
- **Typography**: System fonts for native feel
- **Spacing**: Consistent 8px grid system
- **Animations**: Smooth transitions for better UX

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GEMINI_API_KEY` | Google Gemini API key | Yes |

### Docker Configuration

- **Port**: 8000 (configurable in docker-compose.yml)
- **Health Check**: Automatic monitoring
- **Auto-restart**: Container restarts on failure

## 📝 Usage Example

1. Upload a homework image (math problem, science question, etc.)
2. Select grade level (optional but recommended)
3. Receive three Socratic questions to guide your child
4. Use "Example Approach" if you need concept clarification
5. Progressive reveal solution steps only as last resort

## 🧪 Testing

Test the API with the included script:
```bash
./test_api_detailed.sh test_homework.jpg
```

Or test with curl:
```bash
curl -X POST http://localhost:8000/analyze \
  -F "file=@homework.jpg" \
  -F "grade=6-8"
```

### Health Check
```bash
curl http://localhost:8000/health
```

## 🛠️ Development

### Local Development (without Docker)

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Project Structure Explained

- **Backend** (`main.py`): FastAPI server with Google Gemini AI (gemini-2.5-flash)
- **Frontend** (`static/`): Vanilla JS for simplicity and performance
- **Containerization**: Docker for easy deployment and consistency
- **Documentation**: Comprehensive guides in `/docs` folder
- **Tests**: Automated test script for API validation

### Key Technologies

- **AI Model**: Google Gemini 2.5 Flash (latest as of 2026)
- **Backend**: FastAPI, Pydantic, google-genai SDK
- **Frontend**: HTML5, CSS3 with gradients/animations, Vanilla JavaScript
- **Image Processing**: Pillow (PIL) for compression
- **Deployment**: Docker + Docker Compose

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) (coming soon).

## 📄 License

MIT License - see LICENSE file for details

## 🙏 Acknowledgments

- Powered by Google Gemini AI
- Built with FastAPI and vanilla JavaScript
- Inspired by Socratic teaching methods

## 📚 Documentation

Detailed documentation available in the `/docs` folder:
- [Project Overview](docs/PROJECT_OVERVIEW.md)
- [System Logic](docs/SYSTEM_LOGIC.md)
- [Technical Specification](docs/TECHNICAL_SPEC.md)
- [UI/UX Guidelines](docs/UI_UX_GUIDELINES.md)

## 🐛 Known Issues

- API may fall back to generic responses if Gemini quota is exceeded (retry logic helps)
- Camera feature requires HTTPS in production (works for local development)
- Very large images (>5MB) may take longer to process

## 🚧 Roadmap

- [ ] User accounts and homework history
- [ ] Multi-language support
- [ ] Additional AI model options (OpenAI, Anthropic)
- [ ] Mobile app (iOS/Android)
- [ ] Teacher dashboard
- [ ] Analytics for learning progress

## 💬 Support

For issues and questions:
- Open an issue on GitHub
- Email: support@socraticparent.com (coming soon)

---

**Built with ❤️ for better parent-child learning experiences**

© 2026 Socratic Parent
