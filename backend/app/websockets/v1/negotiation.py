"""
WebSocket endpoint for real-time negotiation with voice streaming.

Flow:
1. User speaks → Audio chunks via WebSocket
2. Deepgram STT → Text transcription
3. Opponent Agent → Response text
4. Cartesia TTS → Audio response
5. Stream audio back to user
"""

import uuid
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
import logging
import json
import asyncio
import os
import base64
import sys
import httpx
import uuid
from datetime import datetime
from typing import Dict, Optional, List

# Add agents to path
sys.path.append(os.path.join(os.path.dirname(__file__), "../../../.."))

from pydantic import BaseModel
from supabase import create_client, Client
from app.core.config import settings
from agents.scenario_agent.scenario import generate_scenario
from deepgram import DeepgramClient, DeepgramClientOptions, LiveOptions, LiveTranscriptionEvents
try:
    from cartesia import Cartesia
except ImportError:
    Cartesia = None

from agents.op_agent.op import OpponentAgent
from agents.coach_agent.coach import CoachAgent
from app.routes.v1.postmortem import store_session_data

logger = logging.getLogger(__name__)

negotiation_router = APIRouter()


def get_supabase_client() -> Client:
    """Initialize and return a Supabase client"""
    supabase_key = settings.SUPABASE_SERVICE_ROLE_KEY or settings.SUPABASE_API_KEY
    if not settings.SUPABASE_URL or not supabase_key:
        raise HTTPException(
            status_code=500,
            detail="Supabase credentials not configured"
        )
    try:
        from supabase import create_client
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Supabase client unavailable: {e}"
        )

    return create_client(settings.SUPABASE_URL, supabase_key)


class NegotiationSession:
    """Manages a single negotiation session with voice streaming"""

    def __init__(self, session_id: str, scenario_data: dict):
        self.session_id = session_id
        self.websocket: Optional[WebSocket] = None
        self.loop: Optional[asyncio.AbstractEventLoop] = None

        # Initialize agents
        try:
            self.opponent = OpponentAgent(scenario_data["opponent"])
            logger.info(f"Session {session_id}: OpponentAgent initialized")
        except Exception as e:
            logger.error(f"Session {session_id}: Failed to initialize OpponentAgent: {e}")
            raise

        try:
            self.coach = CoachAgent(scenario_data["coach"])
            logger.info(f"Session {session_id}: CoachAgent initialized")
        except Exception as e:
            logger.error(f"Session {session_id}: Failed to initialize CoachAgent: {e}")
            raise

        # Deepgram client for STT
        try:
            config = DeepgramClientOptions(
                api_key=os.getenv("DEEPGRAM_API_KEY"),
                options={"ssl_verify": False}
            )
            self.deepgram = DeepgramClient("", config)
            self.dg_connection = None
            self.dg_connected = False
        except Exception as e:
            logger.error(f"Failed to initialize Deepgram: {e}")
            self.deepgram = None
            self.dg_connection = None
            self.dg_connected = False

        # Cartesia client for TTS
        try:
            cartesia_key = settings.CARTESIA_API_KEY
            logger.info(f"Cartesia key loaded (settings): {bool(cartesia_key)}")
            logger.info(f"Cartesia voice id (settings): {settings.CARTESIA_VOICE_ID}")
            if Cartesia:
                self.cartesia_client = Cartesia(api_key=cartesia_key)
                self.cartesia_available = True
            else:
                self.cartesia_client = None
                self.cartesia_available = False
                if cartesia_key:
                    logger.warning("Cartesia SDK unavailable - falling back to HTTP TTS")
                else:
                    logger.warning("Cartesia API key missing - TTS will be disabled")
        except Exception as e:
            logger.error(f"Failed to initialize Cartesia: {e}")
            self.cartesia_client = None
            self.cartesia_available = False
            logger.warning("Cartesia TTS will be disabled")

        # Session state
        self.is_listening = False
        self.current_transcription = ""
        self.scenario_data = scenario_data
        self.received_audio = False
        self.pending_transcript = ""
        self.flush_task = None
        self.is_tts_cancelled = False
        self.transcript_pause_seconds = float(os.getenv("TRANSCRIPT_PAUSE_SECONDS", "3"))
        self.user_turns = 0
        self.opponent_turns = 0
        self.coach_max_chars = int(os.getenv("COACH_MAX_CHARS", "220"))
        self.acceptance_phrases = [
            p.strip().lower() for p in os.getenv(
                "NEGOTIATION_ACCEPT_PHRASES",
                "i accept,i'll take,i will take,sounds good,that works,deal,i agree,"
                "i'll go with,i would take,i can take"
            ).split(",") if p.strip()
        ]
        self.closed = False

        logger.info(f"Created negotiation session {session_id}")

    async def connect_deepgram(self):
        """Establish connection to Deepgram for live transcription"""
        try:
            if not self.deepgram:
                return False

            options = LiveOptions(
                model="nova-2",
                language="en-US",
                encoding="linear16",
                sample_rate=16000,
                channels=1,
                interim_results=True,
                endpointing=5000,
            )

            logger.info(f"Session {self.session_id}: Starting Deepgram connection...")

            self.dg_connection = self.deepgram.listen.websocket.v("1")

            self.dg_connection.on(LiveTranscriptionEvents.Open, self.on_deepgram_open)
            self.dg_connection.on(LiveTranscriptionEvents.Transcript, self.on_deepgram_message)
            self.dg_connection.on(LiveTranscriptionEvents.UtteranceEnd, self.on_utterance_end)
            self.dg_connection.on(LiveTranscriptionEvents.Error, self.on_deepgram_error)
            self.dg_connection.on(LiveTranscriptionEvents.Close, self.on_deepgram_close)

            result = self.dg_connection.start(options)
            if not result:
                logger.error(f"Session {self.session_id}: Failed to start Deepgram connection")
                return False

            self.dg_connected = True
            logger.info(f"Session {self.session_id}: Deepgram connection established")
            return True

        except Exception as e:
            logger.error(f"Session {self.session_id}: Deepgram connection error: {e}")
            return False

    def on_deepgram_message(self, *args, **kwargs):
        """Handle transcription messages from Deepgram"""
        try:
            result = kwargs.get("result")
            if not result:
                logger.warning(f"Session {self.session_id}: No result in Deepgram callback")
                return

            if hasattr(result, 'channel'):
                alternatives = result.channel.alternatives
                if alternatives and len(alternatives) > 0:
                    transcript = alternatives[0].transcript
                    is_final = result.is_final if hasattr(result, 'is_final') else True

                    if transcript:
                        logger.info(f"Session {self.session_id}: Transcription: '{transcript}' (final={is_final})")

                        if self.websocket and self.loop:
                            asyncio.run_coroutine_threadsafe(
                                self.websocket.send_json({
                                    "type": "transcription",
                                    "text": transcript,
                                    "is_final": is_final
                                }),
                                self.loop
                            )

                        if transcript.strip():
                            self.current_transcription = transcript
                            self.pending_transcript = transcript
                            self._schedule_transcript_flush()
            elif hasattr(result, "transcript"):
                transcript = result.transcript
                if transcript:
                    logger.info(f"Session {self.session_id}: Transcription: '{transcript}' (alt)")
                    if self.websocket and self.loop:
                        asyncio.run_coroutine_threadsafe(
                            self.websocket.send_json({
                                "type": "transcription",
                                "text": transcript,
                                "is_final": True
                            }),
                            self.loop
                        )
                    if transcript.strip():
                        self.current_transcription = transcript
                        self.pending_transcript = transcript
                        self._schedule_transcript_flush()

        except Exception as e:
            logger.error(f"Session {self.session_id}: Error processing transcript: {e}", exc_info=True)

    def on_deepgram_open(self, *args, **kwargs):
        """Handle Deepgram connection open"""
        logger.info(f"Session {self.session_id}: Deepgram WebSocket opened")
        self.dg_connected = True

    def on_utterance_end(self, *args, **kwargs):
        """Handle utterance end event - when user has stopped speaking"""
        logger.info(f"Session {self.session_id}: Utterance ended - user finished speaking")
        # The final transcript should already be in self.current_transcription from on_deepgram_message
        self._schedule_transcript_flush()

    def on_deepgram_close(self, *args, **kwargs):
        """Handle Deepgram connection close"""
        logger.info(f"Session {self.session_id}: Deepgram WebSocket closed")
        self.dg_connected = False
        self.dg_connection = None

    def on_deepgram_metadata(self, *args, **kwargs):
        """Handle Deepgram metadata"""
        metadata = args[0] if args else kwargs.get("metadata")
        logger.info(f"Session {self.session_id}: Deepgram metadata: {metadata}")

    def on_deepgram_error(self, *args, **kwargs):
        """Handle Deepgram errors"""
        error = args[0] if args else kwargs.get("error")
        logger.error(f"Session {self.session_id}: Deepgram error: {error}")
        self.dg_connected = False
        self.dg_connection = None

    def _is_deal_closed(self, opponent_response: str) -> bool:
        """Check if opponent's response indicates deal has been closed."""
        lowered = opponent_response.lower()
        # Phrases indicating opponent is closing the deal
        closing_phrases = [
            "we have a deal",
            "we've got a deal",
            "we got a deal",
            "deal is done",
            "it's a deal",
            "that's a deal",
            "shake on it",
            "i'll get the paperwork",
            "i'll draw up the",
            "i'll send over the",
            "pleasure doing business",
            "look forward to working",
            "welcome aboard",
            "congratulations",
            "let's finalize",
            "we're all set",
        ]
        return any(phrase in lowered for phrase in closing_phrases)

    def _is_walkaway(self, opponent_response: str) -> bool:
        """Check if opponent's response indicates they are walking away from the negotiation."""
        lowered = opponent_response.lower()
        # Phrases indicating opponent is walking away
        walkaway_phrases = [
            "walk away",
            "walking away",
            "have to pass",
            "going to pass",
            "i'll pass",
            "i'm going to have to pass",
            "not going to work",
            "isn't going to work",
            "can't make this work",
            "too far apart",
            "explore other options",
            "other options that work better",
            "pursue other opportunities",
            "look elsewhere",
            "end this conversation",
            "we're done here",
            "i'm done",
            "this conversation is over",
            "not interested anymore",
            "no longer interested",
            "withdrawing my offer",
            "rescind my offer",
            "off the table",
            "taking my business elsewhere",
        ]
        return any(phrase in lowered for phrase in walkaway_phrases)

    def _get_closing_message(self) -> str:
        """Generate a brief closing message from the opponent."""
        closing_messages = [
            "Alright, we have a deal. I'll get the paperwork started.",
            "Great, glad we could work this out. I'll send over the details.",
            "Perfect, we're all set then. Good doing business with you.",
            "Sounds good, we've got a deal. I'll follow up with next steps.",
            "Alright, that works for me. Let's shake on it.",
        ]
        import random
        return random.choice(closing_messages)

    async def process_user_message(self, user_text: str):
        """Process user's message through opponent and coach agents"""
        try:
            if self._is_acceptance(user_text):
                self.opponent.current_turn += 1
                self.opponent.transcript.append({
                    "role": "user",
                    "content": user_text,
                    "timestamp": datetime.now().isoformat(),
                    "turn": self.opponent.current_turn
                })

                # Generate and speak a closing message
                closing_message = self._get_closing_message()
                self.opponent.transcript.append({
                    "role": "assistant",
                    "content": closing_message,
                    "timestamp": datetime.now().isoformat(),
                    "turn": self.opponent.current_turn
                })

                # Send closing text to frontend
                await self.websocket.send_json({
                    "type": "opponent_text",
                    "text": closing_message
                })

                # Generate and stream closing audio
                await self.generate_and_stream_audio(closing_message)

                final_advice = self.coach.get_final_advice(self.opponent.transcript)
                hidden_state = self.opponent.get_hidden_state()

                # Store session data for post-mortem analysis
                store_session_data(self.session_id, {
                    "transcript": self.opponent.transcript,
                    "opponent_config": self.scenario_data.get("opponent", {}),
                    "coach_config": self.scenario_data.get("coach", {}),
                    "hidden_state": hidden_state,
                    "final_advice": final_advice,
                })

                # Send negotiation complete - frontend will auto-navigate after audio ends
                await self.websocket.send_json({
                    "type": "negotiation_complete",
                    "final_advice": final_advice,
                    "hidden_state": hidden_state,
                    "transcript": self.opponent.transcript,
                    "auto_ended": True
                })
                self.closed = True
                return

            # Get opponent response
            opponent_response = self.opponent.get_response(user_text)
            logger.info(f"Session {self.session_id}: Opponent response: {opponent_response}")

            # Send text response to frontend
            await self.websocket.send_json({
                "type": "opponent_text",
                "text": opponent_response
            })

            # Generate audio from opponent response
            await self.generate_and_stream_audio(opponent_response)

            self.opponent_turns += 1

            # Check if opponent closed the deal
            if self._is_deal_closed(opponent_response):
                logger.info(f"Session {self.session_id}: Deal closed by opponent")
                final_advice = self.coach.get_final_advice(self.opponent.transcript)
                hidden_state = self.opponent.get_hidden_state()

                # Store session data for post-mortem analysis
                store_session_data(self.session_id, {
                    "transcript": self.opponent.transcript,
                    "opponent_config": self.scenario_data.get("opponent", {}),
                    "coach_config": self.scenario_data.get("coach", {}),
                    "hidden_state": hidden_state,
                    "final_advice": final_advice,
                })

                # Send negotiation complete - frontend will handle navigation after audio finishes
                await self.websocket.send_json({
                    "type": "negotiation_complete",
                    "final_advice": final_advice,
                    "hidden_state": hidden_state,
                    "transcript": self.opponent.transcript,
                    "auto_ended": True
                })
                self.closed = True
                # Don't close websocket here - let frontend handle cleanup after audio plays
                return

            # Check if opponent walked away from the negotiation
            if self._is_walkaway(opponent_response):
                logger.info(f"Session {self.session_id}: Opponent walked away from negotiation")
                final_advice = self.coach.get_final_advice(self.opponent.transcript)
                hidden_state = self.opponent.get_hidden_state()

                # Store session data for post-mortem analysis
                store_session_data(self.session_id, {
                    "transcript": self.opponent.transcript,
                    "opponent_config": self.scenario_data.get("opponent", {}),
                    "coach_config": self.scenario_data.get("coach", {}),
                    "hidden_state": hidden_state,
                    "final_advice": final_advice,
                })

                # Send negotiation complete with walkaway flag
                await self.websocket.send_json({
                    "type": "negotiation_complete",
                    "final_advice": final_advice,
                    "hidden_state": hidden_state,
                    "transcript": self.opponent.transcript,
                    "auto_ended": True,
                    "walked_away": True
                })
                self.closed = True
                return

            # Coach tips: show after the first opponent reply for the next 3 turns,
            # then only surface critical guidance.
            self.user_turns += 1
            coach_tip = self.coach.analyze_turn(self.opponent.transcript)
            is_early_window = 2 <= self.opponent_turns <= 4
            is_critical = False
            if coach_tip:
                upper_tip = coach_tip.upper()
                is_critical = any(keyword in upper_tip for keyword in [
                    "CRITICAL",
                    "IMPORTANT",
                    "MAJOR",
                    "MISTAKE",
                    "DON'T",
                    "DO NOT",
                ])

            if coach_tip and (is_early_window or is_critical):
                # Ensure tip has the emoji prefix, add if missing
                if not coach_tip.startswith("💡"):
                    coach_tip = f"💡 {coach_tip}"
                # Truncate if too long rather than discarding
                if len(coach_tip) > self.coach_max_chars:
                    coach_tip = coach_tip[:self.coach_max_chars - 3] + "..."
                logger.info(f"Session {self.session_id}: Coach tip: {coach_tip}")
                await self.websocket.send_json({
                    "type": "coach_tip",
                    "text": coach_tip
                })

        except Exception as e:
            logger.error(f"Session {self.session_id}: Error processing message: {e}")
            await self.websocket.send_json({
                "type": "error",
                "message": "Failed to process your message"
            })

    async def generate_and_stream_audio(self, text: str):
        """Generate TTS audio and stream to frontend using Cartesia"""
        try:
            if not os.getenv("CARTESIA_API_KEY"):
                logger.warning(f"Session {self.session_id}: TTS disabled - no API key")
                return

            # Reset cancellation flag at the start of new TTS
            self.is_tts_cancelled = False

            # Notify frontend that audio is coming
            await self.websocket.send_json({
                "type": "audio_start"
            })

            # Cartesia voice ID - professional male voice
            voice_id = os.getenv("CARTESIA_VOICE_ID", "a0e99841-438c-4a64-b679-ae501e7d6091")
            tts_model = os.getenv("CARTESIA_MODEL_ID", "sonic-3")

            # Output format for raw PCM audio (16-bit signed, little-endian)
            output_format = {
                "container": "raw",
                "encoding": "pcm_s16le",
                "sample_rate": 44100,
            }

            # Use SDK if available, otherwise fall back to HTTP
            if self.cartesia_client:
                # Stream audio chunks using Cartesia SDK
                for chunk in self.cartesia_client.tts.sse(
                    model_id="sonic-3",
                    transcript=text,
                    voice_id=voice_id,
                    output_format=output_format,
                ):
                    # Check if barge-in occurred
                    if self.is_tts_cancelled:
                        logger.info(f"Session {self.session_id}: TTS cancelled due to barge-in")
                        break

                    audio_bytes = chunk.get("audio") if isinstance(chunk, dict) else chunk
                    if audio_bytes:
                        audio_base64 = base64.b64encode(audio_bytes).decode()
                        await self.websocket.send_json({
                            "type": "audio_chunk",
                            "data": audio_base64,
                            "sample_rate": 44100,
                            "encoding": "pcm_s16le"
                        })
            else:
                # Fall back to HTTP SSE stream
                async for audio_bytes in self._cartesia_sse_stream(text, tts_model, voice_id, output_format):
                    # Check if barge-in occurred
                    if self.is_tts_cancelled:
                        logger.info(f"Session {self.session_id}: TTS cancelled due to barge-in")
                        break

                    if audio_bytes:
                        audio_base64 = base64.b64encode(audio_bytes).decode()
                        await self.websocket.send_json({
                            "type": "audio_chunk",
                            "data": audio_base64,
                            "sample_rate": 44100,
                            "encoding": "pcm_s16le"
                        })

            # Notify frontend that audio is complete (even if cancelled)
            await self.websocket.send_json({
                "type": "audio_end"
            })

            if self.is_tts_cancelled:
                logger.info(f"Session {self.session_id}: TTS stream cancelled by barge-in")
            else:
                logger.info(f"Session {self.session_id}: TTS audio stream completed")

        except Exception as e:
            logger.error(f"Session {self.session_id}: TTS error: {e}", exc_info=True)
            await self.websocket.send_json({
                "type": "error",
                "message": "Failed to generate audio response"
            })

    async def _cartesia_sse_stream(self, text: str, model_id: str, voice_id: str, output_format: dict):
        api_key = settings.CARTESIA_API_KEY

        if not api_key:
            return
        base_url = os.getenv("CARTESIA_BASE_URL", "https://api.cartesia.ai")
        if not base_url.startswith("http"):
            base_url = f"https://{base_url}"
        version = os.getenv("CARTESIA_VERSION", "2024-06-10")

        headers = {
            "X-API-Key": api_key,
            "Cartesia-Version": version,
            "Content-Type": "application/json",
        }
        request_body = {
            "model_id": model_id,
            "transcript": text,
            "voice": {"mode": "id", "id": voice_id},
            "output_format": {
                "container": output_format["container"],
                "encoding": output_format["encoding"],
                "sample_rate": output_format["sample_rate"],
            },
        }

        buffer = ""
        async with httpx.AsyncClient(timeout=httpx.Timeout(30.0, read=30.0)) as client:
            async with client.stream("POST", f"{base_url}/tts/sse", headers=headers, json=request_body) as response:
                response.raise_for_status()
                async for chunk_bytes in response.aiter_bytes():
                    buffer += chunk_bytes.decode("utf-8")
                    while "{" in buffer and "}" in buffer:
                        start_index = buffer.find("{")
                        end_index = buffer.find("}", start_index)
                        if start_index == -1 or end_index == -1:
                            break
                        try:
                            chunk_json = json.loads(buffer[start_index:end_index + 1])
                        except json.JSONDecodeError:
                            break
                        buffer = buffer[end_index + 1:]
                        if "error" in chunk_json:
                            raise RuntimeError(f"Cartesia error: {chunk_json['error']}")
                        if chunk_json.get("done"):
                            return
                        audio_b64 = chunk_json.get("data")
                        if audio_b64:
                            yield base64.b64decode(audio_b64)

    async def send_audio_to_deepgram(self, audio_data: bytes):
        """Send audio chunk to Deepgram for transcription"""
        if not self.dg_connection and self.deepgram:
            await self.connect_deepgram()
        if self.dg_connection:
            if not self.received_audio:
                logger.info(f"Session {self.session_id}: Received audio bytes ({len(audio_data)})")
                self.received_audio = True
            self.dg_connection.send(audio_data)

    def _is_acceptance(self, text: str) -> bool:
        lowered = text.lower().strip()
        if not lowered:
            return False
        if "accept" in lowered and ("not" in lowered or "don't" in lowered or "do not" in lowered):
            return False
        return any(phrase in lowered for phrase in self.acceptance_phrases)

    def _schedule_transcript_flush(self):
        if not self.loop:
            return
        if self.flush_task and not self.flush_task.done():
            self.flush_task.cancel()
        self.flush_task = asyncio.run_coroutine_threadsafe(
            self._flush_transcript_after_pause(),
            self.loop
        )

    async def _flush_transcript_after_pause(self):
        await asyncio.sleep(self.transcript_pause_seconds)
        transcript = self.pending_transcript.strip()
        if not transcript:
            return
        self.pending_transcript = ""
        await self.process_user_message(transcript)

    async def get_opening_message(self):
        """Get opponent's opening message to start negotiation"""
        try:
            opening = self.opponent.get_opening_message()

            # Send opening text
            await self.websocket.send_json({
                "type": "opponent_opening",
                "text": opening
            })

            # Generate and stream opening audio
            await self.generate_and_stream_audio(opening)

        except Exception as e:
            logger.error(f"Session {self.session_id}: Error getting opening: {e}")

    def handle_barge_in(self):
        """Handle user interruption - cancel TTS and prepare for new input"""
        logger.info(f"Session {self.session_id}: Barge-in detected - cancelling TTS")
        self.is_tts_cancelled = True
        # Clear any pending transcript flush since user is speaking new content
        if self.flush_task and not self.flush_task.done():
            self.flush_task.cancel()
        self.pending_transcript = ""

    async def cleanup(self):
        """Clean up session resources"""
        if self.dg_connection:
            self.dg_connection.finish()
        self.dg_connection = None
        self.dg_connected = False
        self.closed = True
        logger.info(f"Session {self.session_id}: Cleaned up")


# Store active sessions
active_sessions: Dict[str, NegotiationSession] = {}


@negotiation_router.websocket("/ws/negotiation/{session_id}")
async def websocket_negotiation(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint for real-time negotiation with voice streaming

    Flow:
    1. Client connects and sends scenario data
    2. Server initializes agents and Deepgram connection
    3. Opponent sends opening message
    4. Client streams audio → Deepgram → Text → Agents → TTS → Audio back
    """
    await websocket.accept()

    try:
        # Wait for initialization message with scenario data
        init_data = await websocket.receive_json()

        if init_data.get("type") != "initialize":
            await websocket.send_json({
                "type": "error",
                "message": "Expected initialization message"
            })
            return

        scenario_data = init_data.get("scenario")
        if not scenario_data:
            await websocket.send_json({
                "type": "error",
                "message": "Missing scenario data"
            })
            return

        # Create session
        session = NegotiationSession(session_id, scenario_data)
        session.websocket = websocket
        session.loop = asyncio.get_event_loop()  # Store the event loop for callbacks
        active_sessions[session_id] = session

        # Connect to Deepgram
        if not await session.connect_deepgram():
            await websocket.send_json({
                "type": "error",
                "message": "Failed to initialize voice recognition"
            })
            return

        # Send ready signal
        await websocket.send_json({
            "type": "ready",
            "session_id": session_id
        })

        # Send opponent's opening message
        await session.get_opening_message()

        # Main message loop
        while True:
            data = await websocket.receive()

            if "bytes" in data:
                # Audio chunk from user
                audio_bytes = data["bytes"]
                await session.send_audio_to_deepgram(audio_bytes)

            elif "text" in data:
                # JSON message
                message = json.loads(data["text"])
                msg_type = message.get("type")

                if msg_type == "end_negotiation":
                    # Get final analysis from coach
                    final_advice = session.coach.get_final_advice(session.opponent.transcript)
                    hidden_state = session.opponent.get_hidden_state()

                    # Store session data for post-mortem analysis
                    store_session_data(session_id, {
                        "transcript": session.opponent.transcript,
                        "opponent_config": session.scenario_data.get("opponent", {}),
                        "coach_config": session.scenario_data.get("coach", {}),
                        "hidden_state": hidden_state,
                        "final_advice": final_advice,
                    })

                    await websocket.send_json({
                        "type": "negotiation_complete",
                        "final_advice": final_advice,
                        "hidden_state": hidden_state,
                        "transcript": session.opponent.transcript
                    })
                    break

                elif msg_type == "get_transcript":
                    await websocket.send_json({
                        "type": "transcript",
                        "transcript": session.opponent.transcript
                    })

                elif msg_type == "barge_in":
                    # User started speaking while TTS was playing
                    session.handle_barge_in()

    except WebSocketDisconnect:
        logger.info(f"Session {session_id}: Client disconnected")

    except Exception as e:
        logger.error(f"Session {session_id}: Error: {e}")
        try:
            await websocket.send_json({
                "type": "error",
                "message": str(e)
            })
        except:
            pass

    finally:
        # Cleanup
        if session_id in active_sessions:
            await active_sessions[session_id].cleanup()
            del active_sessions[session_id]


@negotiation_router.get("/negotiation/session/{session_id}")
async def get_negotiation_session(session_id: str):
    """Get information about active negotiation session"""
    if session_id not in active_sessions:
        return {"error": "Session not found"}

    session = active_sessions[session_id]
    return {
        "session_id": session_id,
        "transcript_length": len(session.opponent.transcript),
        "status": "active"
    }


class ScenarioContextRequest(BaseModel):
    keywords: str


@negotiation_router.post("/scenario_context")
async def create_scenario_context(payload: ScenarioContextRequest):
    try:
        scenario = generate_scenario(payload.keywords)
        if not isinstance(scenario, dict):
            raise ValueError("Scenario generation failed")

        title = (scenario.get("title") or scenario.get("scenario_title") or scenario.get("scenario_id") or "Practice scenario")
        role = (scenario.get("role") or "Participant")
        description = scenario.get("description") or scenario.get("user_narrative") or ""

        return {
            "title": title,
            "role": role,
            "description": description,
            "agent_id": "opponent"
        }
    except Exception as e:
        logger.error(f"Scenario generation failed: {e}")
        raise HTTPException(status_code=500, detail="Scenario generation failed")

@negotiation_router.post("/negotation/session/{session_id}/scenario_info")
async def update_negotiation_scenario_info(session_id: str, scenario_info: str):
    """Update scenario information for a video call session"""
    session = get_negotiation_session(session_id)
    if not session:
        return {"error": "Session not found", "session_id": session_id}

    scenario_para = generate_scenario(scenario_info)
    logger.info(f"Session {session_id}: Scenario info updated")

    return {
        "scenario_paragraph": scenario_para
    }


class VideoSessionRequest(BaseModel):
    """Request model for creating a new video session"""
    link: str
    user_id: Optional[str] = None


class VideoSessionResponse(BaseModel):
    """Response model for video session creation"""
    session_id: str
    created_at: str


class VideoLinksResponse(BaseModel):
    """Response model for fetching all video links"""
    videos: List[dict]


class VideoTitleUpdate(BaseModel):
    title: str


@negotiation_router.post("/videos/session", response_model=VideoSessionResponse)
async def create_video_session(request: VideoSessionRequest):
    """
    Register a new video session in the Supabase table.

    Returns the newly created session ID.
    """
    try:
        supabase = get_supabase_client()

        # Build insert data with optional user_id
        insert_data = {"link": request.link}
        if request.user_id:
            insert_data["user_id"] = request.user_id

        logger.info(f"Creating video session with data: {insert_data}")

        # Insert the new video session into the database
        response = supabase.table("recordings").insert({
            # "id": session_id,
            "link": request.link,
            "public": False,
        }).execute()
        # print("Response data", response.data)
        session_id = response.data[0].get("id")

        logger.info(f"Created video session: {session_id} for user: {request.user_id}")

        # Extract created_at from the response
        if response.data and len(response.data) > 0 and response.data[0]:
            created_at = response.data[0].get("created_at", "")
            return VideoSessionResponse(
                session_id=session_id,
                created_at=created_at
            )

        return VideoSessionResponse(
            session_id=session_id,
            created_at=""
        )

    except Exception as e:
        logger.error(f"Failed to create video session: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to create video session"
        )


@negotiation_router.get("/videos/links", response_model=VideoLinksResponse)
async def get_all_video_links(public_only: bool = False):
    """
    Retrieve video links from the Supabase recordings table.

    If user_id is provided, returns only recordings for that user.
    Otherwise, returns all recordings (for backwards compatibility).

    Args:
        user_id: Optional user ID to filter recordings by

    Returns a list of video records with their id, link, and created_at.
    """
    try:
        supabase = get_supabase_client()
        
        # Fetch video records from the database
        query = supabase.table("recordings").select("*")
        if public_only:
            query = query.eq("public", True)
        response = query.execute()
        
        logger.info(f"Retrieved {len(response.data)} video records")

        return VideoLinksResponse(
            videos=response.data
        )

    except Exception as e:
        logger.error(f"Failed to retrieve video links: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve video links"
        )


@negotiation_router.patch("/videos/{session_id}/title")
async def update_video_title(session_id: str, data: VideoTitleUpdate):
    """
    Update the title for a video session.
    """
    try:
        supabase = get_supabase_client()
        update_data = {"title": data.title.strip()}
        supabase.table("recordings").update(update_data).eq("id", session_id).execute()
        return {"status": "updated", "session_id": session_id}
    except Exception as e:
        logger.error(f"Failed to update video title for session {session_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to update video title"
        )


@negotiation_router.get("/videos/{session_id}/analytics")
async def get_video_analytics(session_id: str):
    """
    Retrieve analytics data for a specific video session.
    
    Returns the analytics JSONB data associated with the given session ID.
    """
    try:
        supabase = get_supabase_client()
        
        # Query the videos table for the specific session
        response = supabase.table("recordings").select("analysis").eq("id", session_id).execute()
        
        if not response.data or len(response.data) == 0:
            raise HTTPException(
                status_code=404,
                detail=f"No video session found with ID: {session_id}"
            )
        
        analysis = response.data[0].get("analysis", {})
        logger.info(f"Retrieved analytics for session: {session_id}")

        return {"session_id": session_id, "analysis": analysis}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve analytics for session {session_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve analytics data"
        )
