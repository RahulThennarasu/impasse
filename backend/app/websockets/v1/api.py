from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import logging
from typing import Dict, Optional
import json
from .negotiation import negotiation_router

logger = logging.getLogger(__name__)

api_router = APIRouter()

# Include negotiation router
api_router.include_router(negotiation_router, tags=["negotiation"])

# Store active video call sessions
# Structure: {session_id: {user: websocket, agent_id: agent_data}}
active_sessions: Dict[str, Dict] = {}


class VideoCallManager:
    """Manages WebSocket connections for user-to-agent video calls"""
    
    def __init__(self):
        self.active_sessions: Dict[str, Dict] = {}
    
    async def create_session(self, session_id: str, user_websocket: WebSocket, agent_id: str):
        """Create a new video call session"""
        await user_websocket.accept()
        
        if session_id not in self.active_sessions:
            self.active_sessions[session_id] = {}
        
        self.active_sessions[session_id]["user"] = user_websocket
        self.active_sessions[session_id]["agent_id"] = agent_id
        self.active_sessions[session_id]["transcript"] = []
        
        logger.info(f"Video call session {session_id} created with agent {agent_id}")
    
    def end_session(self, session_id: str):
        """End a video call session"""
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
            logger.info(f"Video call session {session_id} ended")
    
    async def send_to_user(self, session_id: str, message: dict):
        """Send a message to the user"""
        if session_id in self.active_sessions:
            try:
                await self.active_sessions[session_id]["user"].send_json(message)
            except Exception as e:
                logger.error(f"Error sending to user in session {session_id}: {e}")
                self.end_session(session_id)
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        """Get session data"""
        return self.active_sessions.get(session_id)
    
    def add_to_transcript(self, session_id: str, role: str, message: str):
        """Add message to session transcript"""
        if session_id in self.active_sessions:
            self.active_sessions[session_id]["transcript"].append({
                "role": role,
                "message": message
            })
    
    def get_transcript(self, session_id: str) -> list:
        """Get full transcript of session"""
        if session_id in self.active_sessions:
            return self.active_sessions[session_id]["transcript"]
        return []


# Global video call manager
call_manager = VideoCallManager()


@api_router.websocket("/ws/video/call/{session_id}/{agent_id}")
async def websocket_video_call(websocket: WebSocket, session_id: str, agent_id: str):
    """
    WebSocket endpoint for user-to-agent video calls
    
    Message types from user:
    - "video_frame": Video stream data (base64 or RTC data)
    - "audio_data": Audio stream data
    - "message": Text message during call
    - "request_agent_response": Request AI agent response
    
    Message types sent to user:
    - "agent_response": AI agent response/advice
    - "call_status": Connection status updates
    - "agent_message": Direct message from agent
    """
    try:
        await call_manager.create_session(session_id, websocket, agent_id)
        
        # Notify user that connection is established
        await call_manager.send_to_user(session_id, {
            "type": "call_status",
            "status": "connected",
            "session_id": session_id,
            "agent_id": agent_id,
            "message": f"Connected to {agent_id}"
        })
        
        while True:
            data = await websocket.receive_json()
            message_type = data.get("type")
            
            logger.info(f"Session {session_id}: Received {message_type} from user")
            
            if message_type == "message":
                # User sent a text message
                user_message = data.get("message")
                call_manager.add_to_transcript(session_id, "user", user_message)
                
                # Send acknowledgment
                await call_manager.send_to_user(session_id, {
                    "type": "message_received",
                    "message": user_message
                })
            
            elif message_type == "video_frame":
                # User sent video frame data
                # In production, this would be processed for streaming
                logger.debug(f"Received video frame for session {session_id}")
            
            elif message_type == "audio_data":
                # User sent audio data
                # In production, this would be processed for audio streaming
                logger.debug(f"Received audio data for session {session_id}")
            
            elif message_type == "request_agent_response":
                # Request AI agent to respond
                # In production, integrate with actual agent (Coach, Opponent, Scenario)
                await call_manager.send_to_user(session_id, {
                    "type": "agent_response",
                    "agent_id": agent_id,
                    "response": "Processing your request...",
                    "timestamp": data.get("timestamp")
                })
            
            elif message_type == "get_transcript":
                # Request transcript of conversation
                transcript = call_manager.get_transcript(session_id)
                await call_manager.send_to_user(session_id, {
                    "type": "transcript",
                    "transcript": transcript
                })
            
            elif message_type == "end_call":
                # User ended the call
                await call_manager.send_to_user(session_id, {
                    "type": "call_status",
                    "status": "ended",
                    "message": "Call ended by user"
                })
                call_manager.end_session(session_id)
                break
    
    except WebSocketDisconnect:
        logger.info(f"Session {session_id}: User disconnected")
        call_manager.end_session(session_id)
    
    except Exception as e:
        logger.error(f"Session {session_id}: WebSocket error: {e}")
        call_manager.end_session(session_id)


@api_router.get("/video/session/{session_id}")
async def get_session_info(session_id: str):
    """Get information about an active session"""
    session = call_manager.get_session(session_id)
    if not session:
        return {"error": "Session not found", "session_id": session_id}
    
    return {
        "session_id": session_id,
        "agent_id": session.get("agent_id"),
        "transcript_length": len(session.get("transcript", [])),
        "status": "active"
    }


