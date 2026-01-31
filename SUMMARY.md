# Socratic Parent - Complete Project Summary

> **Use this document to onboard an LLM with full context about the Socratic Parent project.**

---

## 1. PROJECT IDENTITY

**Name:** Socratic Parent (also marketed as "Step-by-Step Learning")  
**Tagline:** "Transform Homework Into Learning"  
**Theme:** The "Anti-Homework-Solver" for the AI-Saturated Era  
**Live URL:** https://socratesparent-production.up.railway.app/

---

## 2. THE PROBLEM WE SOLVE

### Context (2026 Reality)
In 2026, AI "solver" apps are everywhere. Students can point a camera at any problem and get the answer in 0.5 seconds. This has created a crisis of **"Knowledge Decay"**—students are getting answers without understanding.

### The Parent Pain Point
- Parents want to help with homework but are disconnected from modern curricula
- They lack pedagogical training to guide children without just giving answers
- Homework time often becomes a source of family conflict
- Existing tools are either "answer-givers" (cheating) or too complex

### The Student Problem
- Instant answers destroy the learning process
- No understanding = no retention = struggling on tests
- Loss of critical thinking skills
- Dependence on AI tools

---

## 3. THE SOLUTION: A PEDAGOGICAL FIREWALL

Socratic Parent is **NOT** a homework solver. It's a **coaching tool for parents**.

### How It Works
1. **Parent uploads** a photo of the child's homework
2. **AI analyzes** the problem, grade level, and where the student appears stuck
3. **Parent receives** a structured "Coaching Script" with guided questions
4. **Parent guides** the child through discovery—never giving the answer
5. **Child learns** through the Socratic method (questioning → insight)

### The Magic Transformation
- A potential 10-minute "cheating session" becomes a **20-minute meaningful learning moment**
- Homework shifts from source of conflict → source of **connection**

---

## 4. TARGET AUDIENCE

### Primary: Parents
- **Demographics:** Parents of K-12 students (ages 5-18)
- **Pain Points:**
  - Feel disconnected from modern math/science curricula
  - Want to help but don't want to just give answers
  - Frustrated by nightly homework battles
  - Worried about AI making their kids intellectually lazy
- **Psychographics:**
  - Value education and critical thinking
  - Tech-comfortable but not necessarily tech-savvy
  - Willing to invest time in their child's learning
  - Concerned about screen time and AI dependency

### Secondary: Tutors & Educators
- Private tutors wanting a structured approach
- Homeschool parents
- Teachers looking for parent communication tools

---

## 5. VALUE PROPOSITION

### Core Promise
**"We don't give answers. We give mastery."**

### Unique Selling Points
1. **Anti-Cheating by Design** — Impossible to use for shortcuts; it's a parenting tool
2. **Research-Backed Pedagogy** — Built on Socratic method, chunking (Miller's Law), cognitive load theory
3. **Parent-Child Connection** — Transforms homework from conflict to bonding
4. **COPPA-Ready Privacy** — Images processed securely, never stored permanently
5. **No Installation Required** — Web-based, works on any device

### Competitive Moat
| Other EdTech | Socratic Parent |
|--------------|-----------------|
| Sells "Answers" | Sells "Mastery" |
| Enables cheating | Prevents cheating |
| Student-focused | Parent-focused |
| Dependency-creating | Independence-building |

---

## 6. HOW THE PRODUCT WORKS (DETAILED)

### User Flow
```
1. Landing Page → User sees value prop, signs up/logs in
2. Dashboard → Upload area (drag-and-drop or click)
3. Image Upload → Preview shown, "Start Learning" button
4. AI Analysis → Loading state (2-5 seconds)
5. Lesson Display → Problem summary + Steps 1-6
6. Step Navigation → Previous/Continue buttons, progress bar
7. Completion → "Try Another Problem" option
```

### The AI's "Coaching Card" Output Structure
```
SUBJECT: [Subject Name - e.g., "Math - Fractions"]

THE PROBLEM: [What the homework is asking]

Step 1: Understanding
- What the problem is really asking
- Context for the parent

Step 2: Identify the Rules
- Key concepts/formulas needed
- What the child should already know

Step 3: Activate Prior Knowledge
- Questions to ask: "Remember when we learned..."
- Connecting to what they already know

Step 4: The Roadblock
- Where the child appears stuck (from analyzing the work)
- Specific hints for guiding past this point

Step 5: Work It Out
- Step-by-step process (with numbers from problem)
- Questions to ask at each stage

Step 6: Verify & Reflect
- How to check the answer
- Questions for retention: "How would you do a similar problem?"
```

### AI Persona: "The Silent Coach"
- **Tone:** Encouraging, patient, precise
- **Language:** Parent-friendly, no jargon
- **Rules:**
  - NEVER solve the problem
  - NEVER give the final answer
  - Identify WHERE the child is stuck
  - Provide questions, not answers

---

## 7. BUSINESS MODEL

### Freemium with Paddle Billing

**Free Tier:**
- 3 homework analyses per day
- Daily limit resets after 24 hours
- Usage counter displayed in UI
- Paywall triggers on 4th scan attempt

**Premium Tier ($9.99/month):**
- Unlimited homework analyses
- Priority processing
- "∞ Unlimited" badge in header

### Payment Integration
- **Provider:** Paddle Billing v2
- **Checkout:** Overlay checkout within app
- **Webhooks:** Handle subscription lifecycle (created, updated, canceled, expired)
- **Security:** HMAC SHA256 signature verification

---

## 8. TECHNICAL ARCHITECTURE

### Stack Overview
```
Backend:  Python 3.12 + FastAPI 0.110.0
AI:       Google Gemini 2.5 Flash (via google-genai SDK)
Frontend: Vanilla JavaScript (no frameworks)
Math:     KaTeX 0.16.9 (Wolfram Alpha-inspired styling)
Auth:     JWT tokens + bcrypt password hashing
Payments: Paddle Billing v2
Hosting:  Railway.app (PaaS)
```

### Key Files
```
main.py              - Complete backend (2100+ lines)
                       Serves API + static files
static/
  ├── index.html     - Main app interface
  ├── landing.html   - Marketing landing page
  ├── app.js         - Frontend JavaScript
  ├── styles.css     - Shared styles
  ├── login.html     - Auth pages
  └── settings.html  - Account settings
```

### API Endpoints
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Serves landing page |
| `/login.html` | GET | Login page |
| `/upload` | POST | Analyze homework image |
| `/health` | GET | Health check |
| `/api/test` | GET | AI connectivity test |
| `/api/user/status` | GET | Get user premium/usage status |
| `/webhooks/paddle` | POST | Paddle webhook handler |
| `/auth/register` | POST | User registration |
| `/auth/login` | POST | User login |
| `/auth/me` | GET | Get current user |

### API Key Rotation System
- Supports multiple Gemini API keys (GEMINI_API_KEY_1, GEMINI_API_KEY_2, etc.)
- 18 requests/day limit per key (conservative buffer)
- Automatic rotation when key exhausted
- 24-hour recovery period for exhausted keys
- Persistent tracking via JSON file

---

## 9. DESIGN PHILOSOPHY

### Educational Psychology Foundations
1. **Chunking (Miller's Law):** 7±2 steps maximum per lesson
2. **Cognitive Load Theory:** Clean, minimal UI reduces mental overhead
3. **Progressive Disclosure:** One step at a time
4. **Spaced Practice:** Suggested practice problems at end
5. **Visual Hierarchy:** Typography scale guides attention

### Design Tokens
```css
Primary Blue:     #3b82f6 (promotes focus, trust)
Background:       #f8fafc (soft white, easy on eyes)
Text:             #334155 (WCAG AAA contrast)
Math Numbers:     #1e40af (blue)
Math Exponents:   #dc2626 (red)
Math Operators:   #059669 (green)
Math Variables:   #be123c (rose, italic)
```

### Typography
- **Body:** 18px (1.125em) for comfortable reading
- **Line Height:** 1.75 for optimal comprehension
- **Max Width:** 65 characters (ideal reading width)
- **Font:** System fonts (-apple-system, Segoe UI, etc.)

---

## 10. KEY FEATURES LIST

### Core Features
- ✅ Drag-and-drop image upload
- ✅ Step-by-step lesson navigation
- ✅ Progress bar with percentage
- ✅ KaTeX math rendering (color-coded)
- ✅ Mobile-first responsive design
- ✅ JWT authentication
- ✅ User accounts & settings
- ✅ Paddle payment integration
- ✅ Free tier (3/day) + Premium tier
- ✅ Dark mode support
- ✅ Practice problem suggestions

### Technical Features
- ✅ API key rotation with recovery
- ✅ Webhook signature verification
- ✅ Usage tracking persistence
- ✅ Docker containerization
- ✅ Railway auto-deployment
- ✅ Health check endpoints
- ✅ Error recovery & retry logic

---

## 11. FUTURE ROADMAP (Inferred)

1. **Multi-language support** — Spanish, French, Chinese versions
2. **Subject-specific modes** — Math, Science, History, Language Arts
3. **Progress tracking** — History of scans, improvement metrics
4. **Child profiles** — Track multiple children per account
5. **Teacher dashboard** — For classroom use
6. **Mobile apps** — iOS/Android native apps
7. **Offline mode** — Pre-downloaded common concepts
8. **Voice guidance** — Audio coaching for accessibility

---

## 12. PROJECT HISTORY & CONTEXT

**Created:** January 2026  
**Stack Evolution:** Started as single-file app (main.py with embedded frontend) → Modularized to separate static files  
**Deployment:** Railway.app with Docker  
**Current Version:** Production-ready with payment integration

---

## 13. CONVERSATION STARTERS FOR LLM

Use these to ensure the LLM understands the project:

1. "What problem does Socratic Parent solve, and for whom?"
2. "Explain the difference between Socratic Parent and homework solver apps"
3. "How does the freemium business model work?"
4. "Describe the step-by-step learning flow from upload to completion"
5. "What is the AI's persona and what rules does it follow?"
6. "How does the API key rotation system work?"
7. "What educational psychology principles inform the design?"
8. "Explain the Paddle payment integration architecture"

---

## 14. CODEBASE QUICK REFERENCE

### To understand the backend logic:
- Read `main.py` lines 1-200 (setup, API key rotation)
- Read `main.py` lines 240-350 (user management, usage limits)
- Read `main.py` lines 400-550 (upload endpoint, AI call)

### To understand the frontend:
- Read `static/app.js` (main frontend logic)
- Read `static/index.html` (app structure)
- Read `static/landing.html` (marketing page)

### To understand payments:
- Read `docs/paddle/PADDLE_IMPLEMENTATION.md`
- Search `main.py` for "paddle" and "webhook"

### To understand deployment:
- Read `docs/deployment/DEPLOYMENT.md`
- Read `docker-compose.yml` and `Dockerfile`
- Read `railway.json`

---

## 15. SUMMARY IN ONE PARAGRAPH

**Socratic Parent** is a web-based educational tool that transforms homework help from answer-giving into guided learning. Built for parents who want to help their children without cheating, it uses Google Gemini AI to analyze homework images and produce step-by-step "coaching scripts" following the Socratic method. Parents receive questions to ask—never answers to give—turning potential conflict into meaningful connection. The platform uses a freemium model (3 free scans/day, $9.99/month unlimited) powered by Paddle payments. Built with Python/FastAPI backend and vanilla JavaScript frontend, it's designed around cognitive psychology research (chunking, cognitive load theory) with beautiful KaTeX math rendering. Privacy-first: images are processed and never stored.

---

*Document Version: January 2026*  
*Last Updated: Comprehensive summary for LLM context*
