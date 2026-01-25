# 🎓 Step-by-Step Learning

**Transform Homework into Understanding with AI-Powered Step-by-Step Guidance**

An educational platform that breaks down complex problems into clear, manageable steps using AI and research-backed learning principles.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.12-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110-green.svg)

## 🌐 Live Application

**[Try it now at socratesparent-production.up.railway.app →](https://socratesparent-production.up.railway.app/)**

No installation required! Simply:
1. Visit the live application
2. Upload a homework image (math, science, or any subject)
3. Get instant step-by-step learning guidance
4. Navigate through each step at your own pace

> Powered by Google Gemini AI with secure, privacy-first processing.

## 🌟 Philosophy

Built on evidence-based educational psychology principles:
- **Chunking**: Break complex problems into digestible pieces (Miller's Law)
- **Cognitive Load Reduction**: Clean design minimizes mental overhead
- **Progressive Learning**: One step at a time, building understanding
- **Visual Hierarchy**: Clear typography and spacing guide attention
- **Active Learning**: Engage with content through structured steps

## ✨ Features

### 🎯 Core Features
- **📸 Image Upload**: Drag-and-drop or click to upload homework photos
- **🔄 Step-by-Step Navigation**: Progress through solutions at your pace with Previous/Continue buttons
- **📊 Progress Tracking**: Visual progress bar shows completion status
- **🧮 Professional Math Rendering**: KaTeX library with Wolfram Alpha-inspired styling
  - Color-coded components (blue numbers, red exponents, green operators, purple parentheses)
  - Beautiful gradient display boxes for equations
  - Inline and display math modes
- **📱 Fully Responsive**: Optimized for desktop, tablet, and mobile devices
- **🔒 Privacy First**: Images processed securely, never stored permanently
- **✨ Smooth Animations**: Step transitions and progress updates

### 🎨 Design Based on Educational Psychology Research
- **Chunking (Miller's Law)**: Complex problems broken into 7±2 manageable steps
- **Cognitive Load Reduction**: Clean, minimalist interface reduces mental overhead
- **Optimal Reading**: 65-character line width for maximum comprehension
- **Generous Spacing**: 1.75 line height reduces eye strain and improves focus
- **Visual Hierarchy**: Typography scales (2.5em → 0.9em) guide attention naturally
- **Calm Colors**: Blue tones (#3b82f6) promote focus and learning
- **Progress Feedback**: Instant visual confirmation of advancement
- **Chunked Content**: Related information grouped with clear visual boundaries

## 🚀 Quick Start

### Using the Live Application

Visit **[https://socratesparent-production.up.railway.app/](https://socratesparent-production.up.railway.app/)**

1. **Upload**: Click or drag-and-drop a homework image
2. **Analyze**: Click "Start Learning" to process the image
3. **Learn**: Navigate through steps using Previous/Continue buttons
4. **Practice**: Try the suggested practice problem at the end

### Self-Hosting

#### Prerequisites

- Docker and Docker Compose
- Google Gemini API key ([Get one here](https://makersuite.google.com/app/apikey))

#### Installation

1. **Clone the repository**
```bash
git clone https://github.com/davidbobekdev/SocraticParent.git
cd SocraticParent
```

2. **Configure environment**
```bash
echo "GEMINI_API_KEY=your_key_here" > .env
```

3. **Start with Docker**
```bash
docker compose up -d --build
```

4. **Access locally**
Open your browser to: `http://localhost:8000`

## 🏗️ Architecture

### Single-File Application
The entire application is contained in `main.py` (1000+ lines) with embedded HTML/CSS/JavaScript:
- **Backend**: FastAPI 0.110.0 serves HTML and API endpoints
- **Frontend**: Vanilla JavaScript with no frameworks (fast, lightweight)
- **Math Rendering**: KaTeX 0.16.9 with custom Wolfram Alpha-inspired CSS
- **AI Engine**: Google Gemini 2.5 Flash for intelligent content analysis
- **Styling**: Embedded CSS with mobile-first responsive design

### Key Technical Features
- **Step Management**: Dynamic step navigation with state tracking
- **Math Processing**: KaTeX auto-rendering with dollar sign delimiters
- **Responsive CSS**: Mobile optimizations (@media max-width: 768px)
- **Color-Coded Math**: Custom CSS for educational visual hierarchy
- **Error Recovery**: Robust navigation reset and content clearing

### File Structure
```
├── main.py                     # FastAPI backend (1700+ lines)
├── requirements.txt            # Python dependencies
├── start.sh                    # Application startup script
├── users.json                  # User data storage (gitignored)
├── .env.example                # Environment variables template
├── static/                     # Frontend assets
│   ├── index.html              # Main application UI
│   ├── app.js                  # Frontend JavaScript
│   ├── styles.css              # Application styles
│   ├── login.html              # Authentication page
│   └── login.js                # Login logic
├── docs/                       # Documentation
│   ├── PROJECT_OVERVIEW.md     # High-level project info
│   ├── SYSTEM_LOGIC.md         # Architecture details
│   ├── TECHNICAL_SPEC.md       # Technical specifications
│   ├── UI_UX_GUIDELINES.md     # Design guidelines
│   ├── paddle/                 # Payment integration docs
│   │   ├── PADDLE_CONFIG.md
│   │   ├── PADDLE_IMPLEMENTATION.md
│   │   └── PAYMENT_TESTING.md
│   └── deployment/             # Deployment guides
│       ├── DEPLOYMENT.md
│       ├── RAILWAY_VOLUME_SETUP.md
│       └── deploy-railway.sh
├── tests/                      # Test suite (being rewritten)
│   └── README.md               # Test structure documentation
├── .github/                    # GitHub configuration
├── Dockerfile                  # Container configuration
├── docker-compose.yml          # Service orchestration
├── railway.json                # Railway deployment config
└── fly.toml                    # Fly.io configuration
```

## 📋 API Endpoints

### `GET /`
Serves the main application interface
- **Output**: HTML page with embedded CSS and JavaScript

### `POST /upload`
Analyzes homework image and returns step-by-step learning content
- **Input**: Multipart form with `file` (image)
- **Output**: JSON with structured learning steps, problem description, and practice questions

### `GET /health`
Health check endpoint
- **Output**: `{"status": "healthy"}`

### `GET /api/test`
Tests AI model connectivity
- **Output**: Model availability and configuration status

## 🎨 Design Principles

Built on research from Nielsen Norman Group and cognitive psychology:

### Typography
- **Body Text**: 1.125em (18px) for comfortable reading
- **Line Height**: 1.75 for optimal comprehension
- **Line Length**: Max 65 characters (optimal reading width)
- **Font**: Inter system font for native, readable experience

### Colors (Educational Psychology-Based)
- **Primary Blue**: #3b82f6 (promotes focus and calmness)
- **Background**: #f8fafc (soft white reduces eye strain)
- **Text**: #334155 (high contrast for readability)
- **Math Components** (Wolfram Alpha-inspired):
  - Numbers: #1e40af (blue) - primary focus
  - Exponents: #dc2626 (red) - visual distinction
  - Operators: #059669 (green) - action indicators
  - Parentheses: #7c3aed (purple) - grouping
  - Variables: #be123c (rose italic) - unknowns
- **Display Equations**: Blue gradient boxes (#dbeafe → #eff6ff) with borders and shadows

### Spacing (Cognitive Load Optimized)
- **Desktop**: Section margins 32-48px, content padding 24-40px
- **Mobile**: Reduced to 16-20px margins, 16-24px padding
- **Line Spacing**: 1.75 (optimal for comprehension)
- **Step Separation**: 20px between cards

### Layout
- **Max Width**: 720px (optimal for reading and focus)
- **Chunking**: Related content grouped in bordered visual boxes
- **Step Cards**: White background, shadow effects, animated transitions
- **Mobile Optimizations**: Smaller fonts, tighter spacing, optimized touch targets
- **Progressive Disclosure**: One step visible at a time
- **Visual Hierarchy**: Size, weight, and color guide attention

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `GEMINI_API_KEY` | Google Gemini API key | Yes | - |
| `PORT` | Server port | No | 8000 |

### Deployment Configuration

#### Railway (Current Production)
- Automatic deployment on push
- Environment variables set in Railway dashboard
- Health checks enabled
- URL: https://socratesparent-production.up.railway.app/

#### Docker Configuration
- **Port**: 8000 (mapped from container)
- **Health Check**: `/health` endpoint monitored
- **Auto-restart**: Container restarts on failure
- **Image**: Python 3.12-slim for minimal size

## 📝 How to Use

### For Students and Parents

1. **Capture Your Homework**
   - Take a clear photo of the problem
   - Ensure good lighting and legible text
   - Supports all subjects (math, science, etc.)

2. **Upload**
   - Click the upload area or drag-and-drop
   - Preview appears automatically
   - Click "Start Learning" to analyze

3. **Learn Step-by-Step**
   - Read each step carefully
   - Math expressions rendered professionally with KaTeX
   - Use Previous/Continue buttons to navigate
   - Take your time - no rush!

4. **Practice**
   - Try the suggested practice problem
   - Apply what you learned
   - Upload a new problem anytime

### Tips for Best Results
- ✅ Clear, well-lit photos
- ✅ Full problem visible in frame
- ✅ Legible handwriting or printed text
- ✅ One problem at a time
- ❌ Avoid blurry or dark images
- ❌ Don't cut off parts of the problem

## 🧪 Testing

### Health Check
```bash
curl https://socratesparent-production.up.railway.app/health
```

### Test Upload Locally
```bash
curl -X POST http://localhost:8000/upload \
  -F "file=@homework.jpg"
```

## 🛠️ Development

### Local Development

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variable
export GEMINI_API_KEY="your_key_here"

# Run server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Visit `http://localhost:8000` to test locally.

### Key Technologies

- **AI Model**: Google Gemini 2.5 Flash (latest, fastest model)
- **Backend**: FastAPI 0.110.0 with async support
- **Math Rendering**: KaTeX 0.16.9 for LaTeX expressions
- **Image Processing**: Pillow (PIL) for image handling
- **Deployment**: Docker + Railway for production
- **Frontend**: Vanilla JavaScript (no frameworks for simplicity)

## 🚀 Deployment to Railway

The application is currently deployed at: **https://socratesparent-production.up.railway.app/**

### Deploy Your Own Instance

1. **Install Railway CLI**
```bash
npm i -g @railway/cli
```

2. **Login and Deploy**
```bash
railway login
railway init
railway up
```

3. **Set Environment Variable**
```bash
railway variables set GEMINI_API_KEY=your_key_here
```

Or use the included script:
```bash
./deploy-railway.sh
```

### Other Deployment Options

#### Render
```bash
# Push to GitHub, then:
# 1. Go to render.com
# 2. New Web Service → Connect Repository
# 3. Render auto-detects configuration
# 4. Set GEMINI_API_KEY in dashboard
```

#### Fly.io
```bash
flyctl auth login
flyctl launch
flyctl secrets set GEMINI_API_KEY=your_key
flyctl deploy
```

#### Docker (Any Platform)
```bash
docker build -t step-by-step-learning .
docker run -e GEMINI_API_KEY=key -p 8000:8000 step-by-step-learning
```

## 📚 Educational Research Foundation

This application implements principles from:

### Cognitive Load Theory (Sweller, 1988)
- Chunking information into manageable pieces
- Progressive disclosure to prevent overwhelm
- Visual hierarchy guides attention naturally

### Nielsen Norman Group UX Research
- Optimal line length (50-75 characters)
- Generous white space (1.75-2.0 line height)
- Clear visual grouping (Gestalt principles)

### Miller's Law (1956)
- Information presented in digestible chunks
- 5-7 steps per lesson for optimal retention
- Clear separation between concepts

### Color Psychology for Learning
- Blue tones promote focus and reduce anxiety
- High contrast (4.5:1) for accessibility
- Soft backgrounds reduce eye strain

## 🤝 Contributing

Contributions welcome! Areas of interest:
- Additional subject support
- Multi-language interface
- Accessibility improvements
- Mobile app development
- Alternative AI model integrations

## 📄 License

MIT License - Free to use, modify, and distribute

## 🙏 Acknowledgments

- **Google Gemini AI**: Powers the intelligent content analysis
- **KaTeX**: Beautiful math rendering library
- **FastAPI**: Modern, fast Python web framework
- **Railway**: Seamless deployment platform
- **Nielsen Norman Group**: UX research and guidelines
- **Cognitive Psychology Research**: Educational design principles

## 📚 Additional Resources

- [Google Gemini API Documentation](https://ai.google.dev/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [KaTeX Documentation](https://katex.org/)
- [Nielsen Norman Group: Chunking](https://www.nngroup.com/articles/chunking/)
- [Cognitive Load Theory](https://www.instructionaldesign.org/theories/cognitive-load/)

## 🐛 Known Issues & Limitations

- **Image Size**: Very large images (>5MB) may timeout
- **API Quota**: Rate limits apply to free Gemini API tier
- **Math Notation**: Complex LaTeX may need manual formatting
- **Language**: Currently English only (multi-language planned)

## 🚧 Roadmap

- [ ] User accounts and progress tracking
- [ ] Multi-language support (Spanish, French, etc.)
- [ ] Voice narration for steps
- [ ] Offline mode with cached responses
- [ ] Mobile native apps (iOS/Android)
- [ ] Teacher dashboard and analytics
- [ ] Integration with learning management systems

## 💬 Support & Contact

- **Issues**: [GitHub Issues](https://github.com/davidbobekdev/SocraticParent/issues)
- **Live App**: [socratesparent-production.up.railway.app](https://socratesparent-production.up.railway.app/)
- **Documentation**: See `/docs` folder

---

**Built with ❤️ to make learning accessible and effective**

© 2026 Step-by-Step Learning Platform
