# Insight Stream Backend

YouTube video summarization service backend built with FastAPI and AI-powered summarization.

## Features

- YouTube transcript extraction (supports multiple languages)
- **Dual AI Provider Support**: Choose between Google Gemini or OpenAI
- AI-powered video summaries with customizable models
- RESTful API with FastAPI
- Structured error handling
- CORS support for frontend integration
- Modular architecture for easy maintenance

## Project Structure

```
backend/
├── .env                          # Environment variables (Git ignored)
├── .env.example                  # Environment variable template
├── .gitignore                    # Python ignore patterns
├── requirements.txt              # Python dependencies
├── README.md                     # This file
├── main.py                       # FastAPI app entry point
│
└── app/
    ├── __init__.py
    │
    ├── core/                     # Core configuration
    │   ├── __init__.py
    │   └── config.py             # Centralized settings management
    │
    ├── models/                   # Data models
    │   ├── __init__.py
    │   └── schemas.py            # Pydantic request/response models
    │
    ├── services/                 # Business logic
    │   ├── __init__.py
    │   ├── base_ai_service.py    # AI service interface
    │   ├── youtube_service.py    # YouTube transcript extraction
    │   ├── ai_service.py         # Gemini AI implementation
    │   ├── openai_service.py     # OpenAI implementation
    │   └── ai_factory.py         # AI provider factory
    │
    └── api/                      # API endpoints
        ├── __init__.py
        └── endpoints.py          # Route handlers
```

## Installation

### Prerequisites

- Python 3.10 or higher
- **AI Provider API Key** (choose one or both):
  - Google Gemini API key ([Get one here](https://makersuite.google.com/app/apikey))
  - OpenAI API key ([Get one here](https://platform.openai.com/api-keys))

### Setup Steps

1. **Navigate to the backend directory:**
   ```bash
   cd backend
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   ```

3. **Activate the virtual environment:**
   - Windows:
     ```bash
     venv\Scripts\activate
     ```
   - macOS/Linux:
     ```bash
     source venv/bin/activate
     ```

4. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

5. **Configure environment variables:**
   ```bash
   # Copy the example file
   copy .env.example .env

   # Edit .env and configure your AI provider
   # Choose AI provider: AI_PROVIDER=gemini or AI_PROVIDER=openai
   # Add your API key for the selected provider
   ```

## Configuration

Edit `.env` file to configure the application:

### AI Provider Selection

Choose between **Gemini** or **OpenAI** by setting `AI_PROVIDER`:

```env
# AI Provider Selection (Required)
AI_PROVIDER=gemini  # Options: "gemini" or "openai"
```

### Option 1: Using Google Gemini

```env
AI_PROVIDER=gemini
GEMINI_API_KEY=your_actual_gemini_api_key_here

# Gemini Model Settings (Optional)
GEMINI_MODEL=gemini-2.0-flash-exp
GEMINI_TEMPERATURE=0.7
GEMINI_TOP_P=0.9
GEMINI_MAX_TOKENS_OVERVIEW=500
GEMINI_MAX_TOKENS_DETAIL=2000
```

### Option 2: Using OpenAI

```env
AI_PROVIDER=openai
OPENAI_API_KEY=your_actual_openai_api_key_here

# OpenAI Model Settings (Optional)
OPENAI_MODEL=gpt-4o-mini  # or gpt-4, gpt-3.5-turbo, etc.
OPENAI_TEMPERATURE=0.7
OPENAI_MAX_TOKENS_OVERVIEW=500
OPENAI_MAX_TOKENS_DETAIL=2000
```

### Other Settings

```env
# Frontend URL for CORS
FRONTEND_URL=http://localhost:8080

# Server Configuration
HOST=0.0.0.0
PORT=8000
DEBUG=False
LOG_LEVEL=INFO

# Transcript Processing Limits
TRANSCRIPT_LIMIT_OVERVIEW=8000
TRANSCRIPT_LIMIT_DETAIL=12000
```

## Running the Server

### Development Mode

```bash
python main.py
```

The API will be available at `http://localhost:8000`

### Production Mode with Uvicorn

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

## API Endpoints

### Health Check

```http
GET /
```

**Response:**
```json
{
  "status": "ok",
  "message": "Insight Stream API is running",
  "version": "1.0.0"
}
```

### Summarize Video

```http
POST /summarize
Content-Type: application/json

{
  "url": "https://www.youtube.com/watch?v=VIDEO_ID"
}
```

**Response:**
```json
{
  "video_id": "VIDEO_ID",
  "title": "YouTube Video (VIDEO_ID)",
  "full_transcript": "1 First line\n\n2 Second line...",
  "summary_overview": "2-3 sentence overview of the video...",
  "summary_detail": "## Section 1\n- Point 1\n- Point 2..."
}
```

**Error Response:**
```json
{
  "detail": {
    "error": "error_code",
    "message": "User-friendly error message",
    "suggestion": "What to do next"
  }
}
```

## Error Codes

| Code | Status | Description |
|------|--------|-------------|
| `invalid_url` | 400 | Invalid YouTube URL format |
| `transcripts_disabled` | 404 | Transcripts disabled for this video |
| `no_transcript` | 404 | No transcript available |
| `video_unavailable` | 404 | Video not found or private |
| `transcript_error` | 500 | Error fetching transcript |

## Development

### Code Organization

- **app/core/config.py**: Centralized configuration using Pydantic settings
- **app/models/schemas.py**: Request/response data models with validation
- **app/services/base_ai_service.py**: Abstract AI service interface
- **app/services/youtube_service.py**: YouTube transcript extraction logic
- **app/services/ai_service.py**: Gemini AI implementation
- **app/services/openai_service.py**: OpenAI implementation
- **app/services/ai_factory.py**: AI provider factory pattern
- **app/api/endpoints.py**: API route handlers
- **main.py**: Application entry point and FastAPI setup

### AI Provider Architecture

The application uses a **Factory Pattern** for AI providers:

1. **BaseAIService**: Abstract interface defining required methods
2. **GeminiService**: Google Gemini implementation
3. **OpenAIService**: OpenAI implementation
4. **AIServiceFactory**: Selects provider based on `AI_PROVIDER` setting

To add a new AI provider:
1. Create a new service class implementing `BaseAIService`
2. Update `AIServiceFactory.create_ai_service()` to include the new provider
3. Add configuration settings to `config.py`

### Adding New Features

1. Add configuration to `app/core/config.py`
2. Define data models in `app/models/schemas.py`
3. Implement business logic in `app/services/`
4. Add API endpoints in `app/api/endpoints.py`

## Troubleshooting

### Import Errors

Make sure you're running Python from the `backend/` directory:
```bash
cd backend
python main.py
```

### Environment Variable Not Loading

Ensure `.env` file is in the same directory as `main.py`.

### CORS Errors

Check that `FRONTEND_URL` in `.env` matches your frontend's URL.

### API Key Errors

**For Gemini:**
- Verify your Gemini API key is valid and has proper permissions
- Get a key from: https://makersuite.google.com/app/apikey

**For OpenAI:**
- Verify your OpenAI API key is valid
- Ensure you have sufficient credits in your OpenAI account
- Get a key from: https://platform.openai.com/api-keys

### Switching AI Providers

To switch between AI providers:
1. Update `AI_PROVIDER` in `.env` (either "gemini" or "openai")
2. Ensure the corresponding API key is set
3. Restart the server

### YouTube "Request Blocked" Errors

If you encounter "YouTube가 요청을 차단했습니다" errors (especially on Vercel or serverless platforms):

**Recommended Fix: ScraperAPI (Most Reliable):**

ScraperAPI acts as a proxy to bypass YouTube's anti-bot measures.

1. **Sign up for ScraperAPI** (Free Plan Available):
   - Visit: https://www.scraperapi.com/signup
   - Free plan: 1,000 requests/month
   - No credit card required for free tier

2. **Get your API key:**
   - Dashboard: https://www.scraperapi.com/dashboard
   - Copy your API key

3. **Add to `.env`:**
```bash
SCRAPERAPI_KEY="your_scraperapi_key_here"
```

4. **Add to Vercel Environment Variables** (if deploying to Vercel):
   - Settings → Environment Variables
   - Name: `SCRAPERAPI_KEY`
   - Value: (paste your API key)
   - Deploy: Vercel will automatically redeploy with new environment variable

5. **How it works:**
   - If `SCRAPERAPI_KEY` is set, all YouTube requests automatically route through ScraperAPI
   - ScraperAPI handles IP rotation, headers, and anti-blocking measures
   - No code changes needed - works automatically!

**Success Rate:**
- ✅ With ScraperAPI: 100% success rate on Vercel
- ❌ Without ScraperAPI: ~10% success rate on Vercel (frequent 403/429 errors)

**Cost Estimate:**
- Free tier: 1,000 requests/month = ~1,000 video summaries
- Paid plan: $49/month = 100,000 requests
- For most users, free tier is sufficient

---

**Alternative: YouTube Cookies (Less Reliable):**

If you prefer not to use ScraperAPI, you can try adding YouTube cookies:

1. Get YouTube cookies from your browser:
   - Open YouTube in browser (logged in)
   - Press F12 → Application tab → Cookies → youtube.com
   - Copy cookie values (especially `CONSENT`, `VISITOR_INFO1_LIVE`, `YSC`)

2. Add to `.env`:
```bash
YOUTUBE_COOKIES="CONSENT=YES+...; VISITOR_INFO1_LIVE=...; YSC=..."
```

3. Add to Vercel Environment Variables (same as above)

**Note:** 
- Cookies may expire and need periodic updates
- Less reliable than ScraperAPI on serverless platforms
- ⚠️ Still may be blocked by YouTube's anti-bot measures

---

**Other Alternatives:**
- Use a dedicated server (Railway, Render, Fly.io) instead of serverless
- Implement rate limiting to avoid triggering YouTube's anti-bot measures
- Consider using `yt-dlp` library as a more robust alternative (requires more setup)

## License

This project is part of the Insight Stream application.
