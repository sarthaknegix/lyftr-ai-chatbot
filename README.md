# Lyftr AI Chatbot

A full-stack AI chatbot built using React, Python FastAPI, SQLite, and LiteLLM. It supports multi-turn conversations, automatic API key failover, response caching, and per-message token usage tracking.

## Features

- Multi-turn AI conversations with session-based history.
- Automatic fallback between multiple LLM API keys.
- LiteLLM response caching.
- SQLite database for persistent chat history.
- Per-message metadata:
  - Resolution source (`LLM_CACHE` or `LIVE_INFERENCE`)
  - Model name
  - Latency in milliseconds
  - Input and output token counts
- Custom system prompts and response styles.
- Chat history and session management.
- Failure simulation for testing provider failover.

## Technology Stack

- Frontend: React, Vite, CSS
- Backend: Python, FastAPI
- LLM Integration: LiteLLM, Gemini
- Database: SQLite, SQLAlchemy
- Testing: Pytest, HTTPX
- Containerization: Docker, Docker Compose

## Project Structure

```text
lyftr-ai-chatbot/
├── backend/
│   ├── app/
│   ├── tests/
│   └── Dockerfile
├── frontend/
│   ├── src/
│   └── Dockerfile
├── docker-compose.yml
├── Makefile
├── .env.example
├── .gitignore
└── README.md
```

## Live URLs

- **Frontend Application:** https://lyftr-ai-frontend-jopy.onrender.com
- **Backend API:** https://lyftr-ai-chatbot-1-ezfa.onrender.com
- **API Documentation (Swagger):** https://lyftr-ai-chatbot-1-ezfa.onrender.com/docs
- **Health Check:** https://lyftr-ai-chatbot-1-ezfa.onrender.com/health

## Run Locally: Without Docker

### Prerequisites

- Python 3.11 or newer
- Node.js and npm
- Two Gemini API keys

### 1. Clone the repository

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
cd lyftr-ai-chatbot
```

### 2. Configure environment variables

Copy `.env.example` to `.env` and add your actual API keys.

```env
LLM_API_KEYS=YOUR_GEMINI_API_KEY_1,YOUR_GEMINI_API_KEY_2
LLM_MODEL=gemini/gemini-3.5-flash-lite
DATABASE_URL=sqlite:///./lyftr.db
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173
ENABLE_FAILURE_SIMULATION=true
```

Never commit your actual `.env` file.

### 3. Start the backend

```bash
cd backend
python -m venv venv
```

Windows PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
pip install fastapi "uvicorn[standard]" litellm sqlalchemy python-dotenv pydantic pytest httpx aiosqlite
uvicorn app.main:app --reload
```

Backend: `http://127.0.0.1:8000`

API documentation: `http://127.0.0.1:8000/docs`

### 4. Start the frontend

Open another terminal:

```bash
cd frontend
npm install
npm run dev
```

Frontend: `http://localhost:5173`

## Run Locally: With Docker

Docker and Docker Compose are required for the containerized setup.

After configuring `.env` and installing Docker Desktop:

```bash
make up
```

Stop the containers:

```bash
make down
```

The backend database should persist using a Docker volume mounted at `/data`.

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Backend health and configuration status |
| POST | `/chat` | Send a message and receive an AI response |
| GET | `/sessions` | Retrieve chat sessions |
| GET | `/sessions/{session_id}/messages` | Retrieve conversation history |

### Example Chat Request

```json
{
  "session_id": "demo-session",
  "message": "Hello, how are you?",
  "system_prompt": "You are a helpful assistant."
}
```

### Response Metadata

Each assistant response includes:

- `resolution_source`
- `model`
- `latency_ms`
- `input_tokens`
- `output_tokens`
- `key_id`
- `fallback_attempts`

## Design Decisions

### Key Fallback

Multiple API keys are configured in the environment. If a provider request fails due to rate limits or server errors, the backend attempts the next configured key.

### Response Caching

LiteLLM local caching avoids repeated live inference for identical model and message inputs. Cache responses are marked as `LLM_CACHE`.

### SQLite Session Storage

Conversation messages and assistant metadata are stored in SQLite. Each conversation is identified by its session ID.

## Verification

### Backend Tests

Run from the backend directory:

```bash
pytest -v
```

### Health Check

Open:

`http://127.0.0.1:8000/health`

### Cache Verification

Send the same first message in two new sessions. The second identical request should return `LLM_CACHE`.

### Failover Verification

Send a request with this header:

```text
X-Simulate-Failure: key_1=429
```

The backend should fall back to the second key.

### Per-Message Token Usage

Check the assistant response metadata in the frontend or `/sessions/{session_id}/messages`.

## Setup Used

- Operating System: Windows 11
- Editor: Visual Studio Code
- Backend: Python and FastAPI
- Frontend: React and Vite
- Database: SQLite

## Bonus Features

- Custom system prompt settings.
- Multiple response styles.
- Chat session history.
- Failure simulation for testing.
- Response metadata display.
