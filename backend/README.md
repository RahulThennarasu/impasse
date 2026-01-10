# Negotiation Backend

WebSocket-based backend for real-time voice negotiation with AI agents.

## Setup

1. **Install dependencies:**
```bash
cd backend
pip install -r requirements.txt
```

2. **Get API keys:**

- **Deepgram** (STT): https://console.deepgram.com
  - Sign up for free
  - Create an API key
  - Add to `.env`: `DEEPGRAM_API_KEY=your_key`

- **Cartesia** (TTS): https://play.cartesia.ai
  - Sign up for free
  - Get API key
  - Add to `.env`: `CARTESIA_API_KEY=your_key`

3. **Update `.env` file:**
```
GROQ_API_KEY=your_groq_key
DEEPGRAM_API_KEY=your_deepgram_key
CARTESIA_API_KEY=your_cartesia_key
```

## Run the Server

```bash
cd backend
uvicorn main:app --reload --port 8000
```

Server will be available at: `http://localhost:8000`

## Test the WebSocket

Open `test_client.html` in your browser and:

1. Click "Connect" to establish WebSocket connection
2. Wait for opponent's opening message
3. Click "Start Recording" and speak
4. Your speech → Deepgram → Opponent Agent → Cartesia → Audio back
5. Coach gives tips when it spots tactics

## WebSocket Flow

```
User speaks → Audio chunks via WebSocket
    ↓
Deepgram STT → Text transcription
    ↓
Opponent Agent → Response text
    ↓
Cartesia TTS → Audio chunks
    ↓
Stream audio back to user
```

## WebSocket API

### Endpoint
```
ws://localhost:8000/api/v1/ws/negotiation/{session_id}
```

### Messages from Client

**Initialize:**
```json
{
  "type": "initialize",
  "scenario": {
    "opponent": { /* opponent config */ },
    "coach": { /* coach config */ }
  }
}
```

**Audio chunks:** Send raw binary audio data (16-bit PCM, 16kHz)

**End negotiation:**
```json
{
  "type": "end_negotiation"
}
```

### Messages from Server

**Ready:**
```json
{
  "type": "ready",
  "session_id": "..."
}
```

**Opponent opening:**
```json
{
  "type": "opponent_opening",
  "text": "..."
}
```

**Live transcription:**
```json
{
  "type": "transcription",
  "text": "...",
  "is_final": false
}
```

**Opponent response (text):**
```json
{
  "type": "opponent_text",
  "text": "..."
}
```

**Audio chunks:**
```json
{
  "type": "audio_chunk",
  "data": "base64_audio_data"
}
```

**Coach tip:**
```json
{
  "type": "coach_tip",
  "text": "..."
}
```

**Negotiation complete:**
```json
{
  "type": "negotiation_complete",
  "final_advice": "...",
  "hidden_state": { /* opponent's hidden info */ },
  "transcript": [ /* full conversation */ ]
}
```

## Architecture

```
Frontend (React/Next.js)
    ↕ WebSocket
Backend (FastAPI)
    ↕
┌───────────────┬─────────────┬─────────────┐
│  Deepgram STT │ Agent Logic │ Cartesia TTS│
│  (Speech→Text)│ (Groq LLM)  │ (Text→Speech)│
└───────────────┴─────────────┴─────────────┘
```

## Next Steps

1. Get your API keys and add them to `.env`
2. Test with `test_client.html`
3. Build your React frontend that connects to this WebSocket
4. Add video streaming (optional)
5. Build the dashboard/library features
