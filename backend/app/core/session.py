"""
NegotiationSession - Manages the state and transcript for a negotiation practice session.

This is the central coordinator that:
1. Owns the canonical transcript with accurate timestamps
2. Coordinates between agents (Opponent, Coach, PostMortem)
3. Tracks session metadata (duration, turn count, etc.)
4. Provides data for post-mortem analysis
"""

from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum
import uuid


class SessionStatus(Enum):
    CREATED = "created"
    BRIEFING = "briefing"          # User reading scenario briefing
    IN_PROGRESS = "in_progress"    # Active negotiation
    PAUSED = "paused"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


@dataclass
class TranscriptEntry:
    """A single entry in the negotiation transcript."""
    role: str                      # "user" or "assistant" (opponent)
    content: str                   # The text of the message
    timestamp: str                 # ISO format timestamp
    turn: int                      # Turn number (user message starts new turn)
    audio_duration_ms: Optional[int] = None    # How long the audio was
    latency_ms: Optional[int] = None           # Response latency (for opponent)

    def to_dict(self) -> Dict:
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp,
            "turn": self.turn,
            "audio_duration_ms": self.audio_duration_ms,
            "latency_ms": self.latency_ms
        }


@dataclass
class NegotiationSession:
    """
    Manages a single negotiation practice session.

    Usage:
        session = NegotiationSession(
            scenario_id="salary-negotiation",
            user_briefing={...},
            opponent_config={...},
            coach_config={...}
        )

        # User speaks
        session.add_user_message("I'd like to discuss...", audio_duration_ms=2340)

        # Get opponent response
        response = opponent_agent.get_response(session.get_llm_transcript())
        session.add_opponent_message(response, latency_ms=320)

        # Get coach tip
        tip = coach_agent.analyze_turn(session.get_transcript())

        # End and analyze
        session.end()
        analysis = post_mortem.analyze(session.get_transcript())
    """

    # Required fields
    scenario_id: str
    user_briefing: Dict
    opponent_config: Dict
    coach_config: Dict

    # Auto-generated fields
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    # State tracking
    status: SessionStatus = SessionStatus.CREATED
    current_turn: int = 0

    # Transcript
    transcript: List[TranscriptEntry] = field(default_factory=list)

    # Timing
    started_at: Optional[str] = None
    ended_at: Optional[str] = None

    # Metadata
    scenario_title: Optional[str] = None
    opponent_name: Optional[str] = None

    # Video recording
    video_url: Optional[str] = None

    def __post_init__(self):
        """Extract useful metadata from configs."""
        self.opponent_name = self.opponent_config.get("counterparty_name", "Opponent")

    # =========================================================================
    # Session Lifecycle
    # =========================================================================

    def start(self) -> None:
        """Mark the negotiation as started."""
        self.status = SessionStatus.IN_PROGRESS
        self.started_at = datetime.now().isoformat()

    def pause(self) -> None:
        """Pause the session."""
        self.status = SessionStatus.PAUSED

    def resume(self) -> None:
        """Resume a paused session."""
        if self.status == SessionStatus.PAUSED:
            self.status = SessionStatus.IN_PROGRESS

    def end(self) -> None:
        """End the negotiation session."""
        self.status = SessionStatus.COMPLETED
        self.ended_at = datetime.now().isoformat()

    def abandon(self) -> None:
        """Mark session as abandoned (user quit early)."""
        self.status = SessionStatus.ABANDONED
        self.ended_at = datetime.now().isoformat()

    # =========================================================================
    # Transcript Management
    # =========================================================================

    def add_user_message(
        self,
        content: str,
        audio_duration_ms: Optional[int] = None,
        timestamp: Optional[str] = None
    ) -> TranscriptEntry:
        """
        Add a user message to the transcript.

        Args:
            content: The transcribed text from user's speech
            audio_duration_ms: How long the user spoke (from STT)
            timestamp: When the user finished speaking (defaults to now)

        Returns:
            The created TranscriptEntry
        """
        # User message starts a new turn
        self.current_turn += 1

        entry = TranscriptEntry(
            role="user",
            content=content,
            timestamp=timestamp or datetime.now().isoformat(),
            turn=self.current_turn,
            audio_duration_ms=audio_duration_ms
        )

        self.transcript.append(entry)
        return entry

    def add_opponent_message(
        self,
        content: str,
        latency_ms: Optional[int] = None,
        audio_duration_ms: Optional[int] = None,
        timestamp: Optional[str] = None
    ) -> TranscriptEntry:
        """
        Add an opponent message to the transcript.

        Args:
            content: The opponent's response text
            latency_ms: Time from user finish to opponent start
            audio_duration_ms: How long the TTS audio is
            timestamp: When opponent started speaking (defaults to now)

        Returns:
            The created TranscriptEntry
        """
        entry = TranscriptEntry(
            role="assistant",
            content=content,
            timestamp=timestamp or datetime.now().isoformat(),
            turn=self.current_turn,  # Same turn as user message
            latency_ms=latency_ms,
            audio_duration_ms=audio_duration_ms
        )

        self.transcript.append(entry)
        return entry

    def add_opening_message(
        self,
        content: str,
        audio_duration_ms: Optional[int] = None
    ) -> TranscriptEntry:
        """
        Add the opponent's opening message (before user speaks).
        This is turn 0.
        """
        entry = TranscriptEntry(
            role="assistant",
            content=content,
            timestamp=datetime.now().isoformat(),
            turn=0,
            audio_duration_ms=audio_duration_ms
        )

        self.transcript.append(entry)
        return entry

    # =========================================================================
    # Transcript Access
    # =========================================================================

    def get_transcript(self) -> List[Dict]:
        """
        Get the full transcript as a list of dicts.
        Used by PostMortemAgent.
        """
        return [entry.to_dict() for entry in self.transcript]

    def get_llm_transcript(self) -> List[Dict]:
        """
        Get transcript in format suitable for LLM context.
        Only includes role and content (what LLM needs for conversation history).
        """
        return [
            {"role": entry.role, "content": entry.content}
            for entry in self.transcript
        ]

    def get_recent_transcript(self, n_messages: int = 4) -> List[Dict]:
        """
        Get the last N messages. Used by CoachAgent for analysis.
        """
        recent = self.transcript[-n_messages:] if len(self.transcript) >= n_messages else self.transcript
        return [entry.to_dict() for entry in recent]

    def get_last_user_message(self) -> Optional[str]:
        """Get the most recent user message."""
        for entry in reversed(self.transcript):
            if entry.role == "user":
                return entry.content
        return None

    def get_last_opponent_message(self) -> Optional[str]:
        """Get the most recent opponent message."""
        for entry in reversed(self.transcript):
            if entry.role == "assistant":
                return entry.content
        return None

    # =========================================================================
    # Session Metrics
    # =========================================================================

    def get_duration_seconds(self) -> Optional[float]:
        """Get total session duration in seconds."""
        if not self.started_at:
            return None

        end = self.ended_at or datetime.now().isoformat()

        start_dt = datetime.fromisoformat(self.started_at)
        end_dt = datetime.fromisoformat(end)

        return (end_dt - start_dt).total_seconds()

    def get_turn_count(self) -> int:
        """Get total number of turns (user messages)."""
        return self.current_turn

    def get_message_count(self) -> Dict[str, int]:
        """Get count of messages by role."""
        user_count = sum(1 for e in self.transcript if e.role == "user")
        opponent_count = sum(1 for e in self.transcript if e.role == "assistant")
        return {"user": user_count, "opponent": opponent_count, "total": len(self.transcript)}

    def get_average_response_latency(self) -> Optional[float]:
        """Get average opponent response latency in ms."""
        latencies = [e.latency_ms for e in self.transcript if e.latency_ms is not None]
        if not latencies:
            return None
        return sum(latencies) / len(latencies)

    # =========================================================================
    # Serialization
    # =========================================================================

    def to_dict(self) -> Dict:
        """Serialize session to dictionary (for storage/API response)."""
        return {
            "session_id": self.session_id,
            "scenario_id": self.scenario_id,
            "scenario_title": self.scenario_title,
            "opponent_name": self.opponent_name,
            "status": self.status.value,
            "current_turn": self.current_turn,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "ended_at": self.ended_at,
            "duration_seconds": self.get_duration_seconds(),
            "message_count": self.get_message_count(),
            "transcript": self.get_transcript(),
            "user_briefing": self.user_briefing,
            "opponent_config": self.opponent_config,
            "coach_config": self.coach_config,
            "video_url": self.video_url
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "NegotiationSession":
        """Deserialize session from dictionary."""
        session = cls(
            scenario_id=data["scenario_id"],
            user_briefing=data["user_briefing"],
            opponent_config=data["opponent_config"],
            coach_config=data["coach_config"]
        )

        session.session_id = data.get("session_id", session.session_id)
        session.status = SessionStatus(data.get("status", "created"))
        session.current_turn = data.get("current_turn", 0)
        session.created_at = data.get("created_at", session.created_at)
        session.started_at = data.get("started_at")
        session.ended_at = data.get("ended_at")
        session.scenario_title = data.get("scenario_title")
        session.opponent_name = data.get("opponent_name")
        session.video_url = data.get("video_url")

        # Rebuild transcript
        for entry_data in data.get("transcript", []):
            entry = TranscriptEntry(
                role=entry_data["role"],
                content=entry_data["content"],
                timestamp=entry_data["timestamp"],
                turn=entry_data["turn"],
                audio_duration_ms=entry_data.get("audio_duration_ms"),
                latency_ms=entry_data.get("latency_ms")
            )
            session.transcript.append(entry)

        return session
