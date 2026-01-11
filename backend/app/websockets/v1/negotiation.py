"""
WebSocket endpoint for real-time negotiation with voice streaming.

Flow:
1. User speaks → Audio chunks via WebSocket
2. Deepgram STT → Text transcription
3. Opponent Agent → Response text
4. Cartesia TTS → Audio response
5. Stream audio back to user
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
import logging
import json
import asyncio
import os
import base64
import sys
from typing import Dict, Optional

# Add agents to path
sys.path.append(os.path.join(os.path.dirname(__file__), "../../../.."))

from pydantic import BaseModel
from agents.scenario_agent.scenario import generate_scenario
from deepgram import DeepgramClient
from deepgram.core.events import EventType
from deepgram.listen.v1.socket_client import AsyncV1SocketClient
from deepgram.listen.v1.types.listen_v1results import ListenV1Results
try:
    from cartesia import Cartesia
except ImportError:
    Cartesia = None

# Add agents to path
sys.path.append(os.path.join(os.path.dirname(__file__), "../../../.."))
from agents.op_agent.op import OpponentAgent
from agents.coach_agent.coach import CoachAgent
from agents.scenario_agent.scenario import generate_scenario

logger = logging.getLogger(__name__)

negotiation_router = APIRouter()


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
            self.deepgram = DeepgramClient(api_key=os.getenv("DEEPGRAM_API_KEY"))
            self.dg_connection: Optional[AsyncV1SocketClient] = None
            self.dg_connection_ctx = None
            self.dg_task: Optional[asyncio.Task] = None
            self.dg_connected = False
        except Exception as e:
            logger.error(f"Failed to initialize Deepgram: {e}")
            self.deepgram = None
            self.dg_connection = None
            self.dg_connection_ctx = None
            self.dg_task = None
            self.dg_connected = False

        # Cartesia client for TTS
        try:
            if Cartesia:
                self.cartesia_client = Cartesia(api_key=os.getenv("CARTESIA_API_KEY"))
            else:
                self.cartesia_client = None
                logger.warning("Cartesia not installed - TTS will be disabled")
        except Exception as e:
            logger.error(f"Failed to initialize Cartesia: {e}")
            self.cartesia_client = None
            logger.warning("Cartesia TTS will be disabled")

        # Session state
        self.is_listening = False
        self.current_transcription = ""
        self.scenario_data = scenario_data
        self.received_audio = False
        self.pending_transcript = ""
        self.flush_task = None
        self.transcript_pause_seconds = float(os.getenv("TRANSCRIPT_PAUSE_SECONDS", "3"))
        self.user_turns = 0
        self.coach_every_n_turns = int(os.getenv("COACH_EVERY_N_TURNS", "3"))
        self.coach_max_chars = int(os.getenv("COACH_MAX_CHARS", "220"))
        self.coach_early_turns = int(os.getenv("COACH_EARLY_TURNS", "4"))
        self.coach_early_every_n_turns = int(os.getenv("COACH_EARLY_EVERY_N_TURNS", "2"))
        self.acceptance_phrases = [
            p.strip().lower() for p in os.getenv(
                "NEGOTIATION_ACCEPT_PHRASES",
                "i accept,i'll take,i will take,sounds good,that works,deal,i agree,"
                "i'll go with,i would take,i can take"
            ).split(",") if p.strip()
        ]

        logger.info(f"Created negotiation session {session_id}")

    async def connect_deepgram(self):
        """Establish connection to Deepgram for live transcription"""
        try:
            if not self.deepgram:
                return False
            logger.info(f"Session {self.session_id}: Starting Deepgram connection...")
            self.dg_connection_ctx = self.deepgram.listen.v1.connect(
                model="nova-2",
                language="en-US",
                encoding="linear16",
                sample_rate="16000",
                channels="1",
                interim_results="true",
                endpointing="5000",
            )
            self.dg_connection = await self.dg_connection_ctx.__aenter__()

            # Set up event handlers
            self.dg_connection.on(EventType.OPEN, self.on_deepgram_open)
            self.dg_connection.on(EventType.MESSAGE, self.on_deepgram_message)
            self.dg_connection.on(EventType.ERROR, self.on_deepgram_error)
            self.dg_connection.on(EventType.CLOSE, self.on_deepgram_close)

            self.dg_task = asyncio.create_task(self.dg_connection.start_listening())
            self.dg_connected = True
            logger.info(f"Session {self.session_id}: Deepgram connection established")
            return True

        except Exception as e:
            logger.error(f"Session {self.session_id}: Deepgram connection error: {e}")
            return False

    def on_deepgram_message(self, result: object):
        """Handle transcription messages from Deepgram"""
        try:
            if not isinstance(result, ListenV1Results):
                return

            alternatives = result.channel.alternatives
            if not alternatives:
                return

            transcript = alternatives[0].transcript
            is_final = bool(result.is_final)

            if transcript:
                logger.info(
                    f"Session {self.session_id}: Transcription: '{transcript}' (final={is_final})"
                )

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

    async def process_user_message(self, user_text: str):
        """Process user's message through opponent and coach agents"""
        try:
            if self._is_acceptance(user_text):
                self.opponent.transcript.append({"role": "user", "content": user_text})
                final_advice = self.coach.get_final_advice(self.opponent.transcript)
                hidden_state = self.opponent.get_hidden_state()
                await self.websocket.send_json({
                    "type": "negotiation_complete",
                    "final_advice": final_advice,
                    "hidden_state": hidden_state,
                    "transcript": self.opponent.transcript,
                    "auto_ended": True
                })
                await self.websocket.close()
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

            # Get coach analysis on a reduced cadence; only forward short actionable tips
            self.user_turns += 1
            cadence = self.coach_early_every_n_turns if self.user_turns <= self.coach_early_turns else self.coach_every_n_turns
            if cadence > 0 and self.user_turns % cadence == 0:
                coach_tip = self.coach.analyze_turn(self.opponent.transcript)
                if coach_tip and coach_tip.startswith("💡") and len(coach_tip) <= self.coach_max_chars:
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
            if not self.cartesia_client:
                logger.warning(f"Session {self.session_id}: TTS disabled - skipping audio generation")
                return

            # Notify frontend that audio is coming
            await self.websocket.send_json({
                "type": "audio_start"
            })

            # Cartesia voice ID - professional male voice
            voice_id = os.getenv("CARTESIA_VOICE_ID", "a0e99841-438c-4a64-b679-ae501e7d6091")

            # Output format for raw PCM audio (16-bit signed, little-endian)
            output_format = {
                "container": "raw",
                "encoding": "pcm_s16le",
                "sample_rate": 44100,
            }

            # Stream audio chunks using SSE
            # Cartesia SDK returns dict with 'audio' key containing bytes
            for chunk in self.cartesia_client.tts.sse(
                model_id="sonic-3",
                transcript=text,
                voice_id=voice_id,
                output_format=output_format,
            ):
                audio_bytes = chunk.get("audio") if isinstance(chunk, dict) else chunk
                if audio_bytes:
                    audio_base64 = base64.b64encode(audio_bytes).decode()
                    await self.websocket.send_json({
                        "type": "audio_chunk",
                        "data": audio_base64,
                        "sample_rate": 44100,
                        "encoding": "pcm_s16le"
                    })

            # Notify frontend that audio is complete
            await self.websocket.send_json({
                "type": "audio_end"
            })

            logger.info(f"Session {self.session_id}: TTS audio stream completed")

        except Exception as e:
            logger.error(f"Session {self.session_id}: TTS error: {e}", exc_info=True)
            await self.websocket.send_json({
                "type": "error",
                "message": "Failed to generate audio response"
            })

    async def send_audio_to_deepgram(self, audio_data: bytes):
        """Send audio chunk to Deepgram for transcription"""
        if not self.dg_connection and self.deepgram:
            await self.connect_deepgram()
        if self.dg_connection:
            if not self.received_audio:
                logger.info(f"Session {self.session_id}: Received audio bytes ({len(audio_data)})")
                self.received_audio = True
            await self.dg_connection.send_media(audio_data)

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

    async def cleanup(self):
        """Clean up session resources"""
        if self.dg_task:
            self.dg_task.cancel()
            self.dg_task = None
        if self.dg_connection_ctx:
            await self.dg_connection_ctx.__aexit__(None, None, None)
            self.dg_connection_ctx = None
        self.dg_connection = None
        self.dg_connected = False
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
