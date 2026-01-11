"""
Post-mortem API endpoints for negotiation analysis.

Provides REST endpoints to:
1. Store completed session data
2. Trigger post-mortem analysis
3. Retrieve analysis results
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import logging
import sys
import os

# Add agents to path
sys.path.append(os.path.join(os.path.dirname(__file__), "../../../.."))

from agents.post_mortem.mortem import PostMortemAgent

logger = logging.getLogger(__name__)

postmortem_router = APIRouter()

# In-memory store for session data and analysis results
# Analysis is also persisted to Supabase when available
_session_store: Dict[str, Dict] = {}
_analysis_store: Dict[str, Dict] = {}


def get_supabase_client():
    """Initialize Supabase client for post-mortem storage."""
    from app.core.config import settings
    if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
        return None
    try:
        from supabase import create_client
        return create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
    except Exception as e:
        logger.warning(f"Supabase client unavailable: {e}")
        return None


def persist_postmortem_to_db(session_id: str, analysis_data: Dict, video_url: Optional[str] = None) -> bool:
    """
    Persist post-mortem analysis to Supabase recordings table.

    Args:
        session_id: The negotiation session ID
        analysis_data: The frontend-formatted analysis result
        video_url: Optional presigned URL for the video

    Returns:
        True if persistence succeeded, False otherwise
    """
    supabase = get_supabase_client()
    if not supabase:
        logger.warning("Supabase not configured, skipping DB persistence")
        return False

    try:
        # Check if record exists
        existing = supabase.table("recordings").select("*").eq("id", session_id).execute()

        record_data = {
            "analysis": analysis_data,
        }
        if video_url:
            record_data["link"] = video_url

        if existing.data and len(existing.data) > 0:
            # Update existing record
            supabase.table("recordings").update(record_data).eq("id", session_id).execute()
            logger.info(f"Updated post-mortem in DB for session {session_id}")
        else:
            # Insert new record
            record_data["id"] = session_id
            supabase.table("recordings").insert(record_data).execute()
            logger.info(f"Inserted post-mortem in DB for session {session_id}")

        return True
    except Exception as e:
        logger.error(f"Failed to persist post-mortem to DB: {e}")
        return False


class SessionData(BaseModel):
    """Data required to run post-mortem analysis."""
    transcript: List[Dict[str, Any]]
    opponent_config: Dict[str, Any]
    coach_config: Dict[str, Any]
    user_briefing: Optional[Dict[str, Any]] = None
    hidden_state: Optional[Dict[str, Any]] = None
    final_advice: Optional[str] = None
    video_url: Optional[str] = None


class PostMortemRequest(BaseModel):
    """Request to trigger post-mortem analysis."""
    session_id: str


class PostMortemMetric(BaseModel):
    """A single performance metric."""
    label: str
    score: int
    change: int


class PostMortemMoment(BaseModel):
    """A key moment in the negotiation."""
    time: str
    desc: str
    type: str  # "positive" or "negative"


class PostMortemResult(BaseModel):
    """Frontend-compatible post-mortem result format."""
    overallScore: int
    strengths: List[str]
    improvements: List[str]
    metrics: List[PostMortemMetric]
    keyMoments: List[PostMortemMoment]


def store_session_data(session_id: str, data: Dict) -> None:
    """Store session data for later analysis."""
    _session_store[session_id] = data
    logger.info(f"Stored session data for {session_id}")


def get_session_data(session_id: str) -> Optional[Dict]:
    """Retrieve stored session data."""
    return _session_store.get(session_id)


def transform_to_frontend_format(analysis: Dict, final_advice: Optional[str] = None) -> Dict:
    """
    Transform PostMortemAgent output to frontend-compatible format.

    Maps the rich agent analysis to the simpler frontend structure.
    """
    # Handle parse errors gracefully
    if analysis.get("parse_error"):
        return {
            "overallScore": 50,
            "strengths": ["Analysis could not be parsed. Please try again."],
            "improvements": [analysis.get("raw_response", "Unknown error")[:200]],
            "metrics": [
                {"label": "Communication", "score": 50, "change": 0},
                {"label": "Strategy", "score": 50, "change": 0},
                {"label": "Persuasion", "score": 50, "change": 0},
                {"label": "Listening", "score": 50, "change": 0},
                {"label": "Confidence", "score": 50, "change": 0},
                {"label": "Adaptability", "score": 50, "change": 0},
            ],
            "keyMoments": [],
        }

    # Extract summary data
    summary = analysis.get("summary", {})
    outcome = analysis.get("outcome_assessment", {})

    # Map grade to score
    grade_to_score = {
        "A": 95, "A-": 90,
        "B+": 87, "B": 83, "B-": 80,
        "C+": 77, "C": 73, "C-": 70,
        "D+": 67, "D": 63, "D-": 60,
        "F": 45
    }
    grade = summary.get("grade", "C")
    overall_score = grade_to_score.get(grade, 70)

    # Build strengths from various sources
    strengths = []

    # Add biggest win
    if summary.get("biggest_win"):
        strengths.append(f"Strong move: {summary['biggest_win']}")

    # Add effective tactics
    for tactic in analysis.get("tactics_used", []):
        if tactic.get("speaker") == "user" and tactic.get("effectiveness") == "effective":
            strengths.append(f"Effective use of {tactic.get('tactic_name', 'tactic')}: {tactic.get('analysis', '')}")

    # Add positive lessons
    for lesson in analysis.get("key_lessons", [])[:2]:
        if "well" in lesson.get("lesson", "").lower() or "good" in lesson.get("lesson", "").lower():
            strengths.append(lesson.get("lesson", ""))

    # Add outcome positives
    if outcome.get("primary_objective_achieved"):
        strengths.append(f"Primary objective achieved: {outcome.get('primary_objective_details', '')}")

    if outcome.get("compared_to_batna") == "better":
        strengths.append(f"Outcome better than BATNA: {outcome.get('batna_comparison_details', '')}")

    # Ensure at least one strength
    if not strengths:
        strengths.append("Completed the negotiation session")

    # Build improvements from various sources
    improvements = []

    # Add biggest miss
    if summary.get("biggest_miss"):
        improvements.append(f"Opportunity missed: {summary['biggest_miss']}")

    # Add missed opportunities
    for missed in analysis.get("missed_opportunities", [])[:2]:
        improvements.append(f"At turn {missed.get('turn', '?')}: {missed.get('opportunity', 'Missed opportunity')}")

    # Add improvement lessons
    for lesson in analysis.get("key_lessons", []):
        lesson_text = lesson.get("lesson", "")
        if any(word in lesson_text.lower() for word in ["could", "should", "avoid", "improve", "next time"]):
            tip = lesson.get("practice_tip", "")
            improvements.append(f"{lesson_text}. {tip}" if tip else lesson_text)

    # Add ineffective tactics
    for tactic in analysis.get("tactics_used", []):
        if tactic.get("speaker") == "user" and tactic.get("effectiveness") in ["ineffective", "backfired"]:
            improvements.append(f"Reconsider {tactic.get('tactic_name', 'approach')}: {tactic.get('analysis', '')}")

    # Ensure at least one improvement
    if not improvements:
        improvements.append("Continue practicing to refine your negotiation skills")

    # Build metrics based on analysis
    # These are inferred from the analysis content
    metrics = []

    # Communication score - based on information reveals and tactics
    info_reveals = analysis.get("information_reveals", [])
    intentional_reveals = sum(1 for r in info_reveals if r.get("speaker") == "user" and r.get("was_intentional"))
    unintentional_reveals = sum(1 for r in info_reveals if r.get("speaker") == "user" and not r.get("was_intentional"))
    comm_score = max(50, min(95, 80 + intentional_reveals * 5 - unintentional_reveals * 10))
    metrics.append({"label": "Communication", "score": comm_score, "change": 0})

    # Strategy score - based on outcome and objective achievement
    strategy_score = overall_score
    if outcome.get("primary_objective_achieved"):
        strategy_score = min(95, strategy_score + 10)
    if outcome.get("compared_to_batna") == "worse":
        strategy_score = max(40, strategy_score - 15)
    metrics.append({"label": "Strategy", "score": strategy_score, "change": 0})

    # Persuasion score - based on effective tactics
    effective_tactics = sum(1 for t in analysis.get("tactics_used", [])
                           if t.get("speaker") == "user" and t.get("effectiveness") == "effective")
    ineffective_tactics = sum(1 for t in analysis.get("tactics_used", [])
                             if t.get("speaker") == "user" and t.get("effectiveness") in ["ineffective", "backfired"])
    persuasion_score = max(45, min(95, 70 + effective_tactics * 8 - ineffective_tactics * 10))
    metrics.append({"label": "Persuasion", "score": persuasion_score, "change": 0})

    # Listening score - based on missed opportunities (fewer = better listening)
    missed_count = len(analysis.get("missed_opportunities", []))
    listening_score = max(50, min(95, 90 - missed_count * 10))
    metrics.append({"label": "Listening", "score": listening_score, "change": 0})

    # Confidence score - based on overall rating and tactics
    rating_to_confidence = {"excellent": 92, "good": 82, "fair": 68, "poor": 52}
    confidence_score = rating_to_confidence.get(outcome.get("overall_rating", "fair"), 70)
    metrics.append({"label": "Confidence", "score": confidence_score, "change": 0})

    # Adaptability score - based on turning points handled
    turning_points = analysis.get("turning_points", [])
    adaptability_score = max(55, min(95, 75 + len(turning_points) * 5))
    metrics.append({"label": "Adaptability", "score": adaptability_score, "change": 0})

    # Build key moments from tactics, turning points, and missed opportunities
    key_moments = []

    # Add turning points as key moments
    for tp in analysis.get("turning_points", [])[:2]:
        moment_type = "positive" if "better" not in tp.get("better_alternative", "").lower() else "negative"
        key_moments.append({
            "time": tp.get("timestamp", "0:00"),
            "desc": tp.get("description", "Key moment"),
            "type": moment_type
        })

    # Add effective tactics as positive moments
    for tactic in analysis.get("tactics_used", [])[:2]:
        if tactic.get("speaker") == "user" and tactic.get("effectiveness") == "effective":
            key_moments.append({
                "time": tactic.get("timestamp", "0:00"),
                "desc": f"{tactic.get('tactic_name', 'Tactic')}: {tactic.get('analysis', '')}",
                "type": "positive"
            })

    # Add missed opportunities as negative moments
    for missed in analysis.get("missed_opportunities", [])[:2]:
        key_moments.append({
            "time": missed.get("timestamp", "0:00"),
            "desc": missed.get("opportunity", "Missed opportunity"),
            "type": "negative"
        })

    # Ensure we have at least some moments
    if not key_moments:
        key_moments.append({
            "time": "0:00",
            "desc": summary.get("one_sentence", "Negotiation completed"),
            "type": "positive" if overall_score >= 70 else "negative"
        })

    # Sort by time and limit to 4-5 moments
    key_moments = key_moments[:5]

    return {
        "overallScore": overall_score,
        "strengths": strengths[:3],  # Limit to 3
        "improvements": improvements[:3],  # Limit to 3
        "metrics": metrics,
        "keyMoments": key_moments,
    }


@postmortem_router.post("/post_mortem")
async def request_post_mortem(request: PostMortemRequest):
    """
    Trigger post-mortem analysis for a completed session.

    The session data must have been stored via store_session_data()
    when the negotiation ended.
    """
    session_id = request.session_id
    logger.info(f"Post-mortem requested for session {session_id}")

    # Check if analysis already exists
    if session_id in _analysis_store:
        logger.info(f"Returning cached analysis for {session_id}")
        return {"status": "complete", "session_id": session_id}

    # Get session data
    session_data = get_session_data(session_id)
    if not session_data:
        logger.warning(f"No session data found for {session_id}")
        raise HTTPException(
            status_code=404,
            detail=f"Session {session_id} not found. The session may have expired."
        )

    try:
        # Extract required data
        transcript = session_data.get("transcript", [])
        opponent_config = session_data.get("opponent_config", {})
        coach_config = session_data.get("coach_config", {})
        hidden_state = session_data.get("hidden_state", {})

        # Build user briefing from coach config
        user_briefing = {
            "objectives": coach_config.get("user_objectives", {}),
            "batna": coach_config.get("user_batna", {}),
            "success_criteria": coach_config.get("success_criteria", {}),
            "negotiables": coach_config.get("negotiables", []),
        }

        # Create PostMortemAgent
        agent = PostMortemAgent(
            user_briefing=user_briefing,
            opponent_hidden_state=hidden_state or opponent_config,
            coach_config=coach_config
        )

        # Run analysis
        logger.info(f"Running post-mortem analysis for {session_id} with {len(transcript)} messages")
        analysis = agent.analyze(transcript)

        # Transform to frontend format
        frontend_result = transform_to_frontend_format(
            analysis,
            session_data.get("final_advice")
        )

        # Store the analysis in memory
        _analysis_store[session_id] = {
            "raw_analysis": analysis,
            "frontend_result": frontend_result,
            "summary_text": agent.get_summary(analysis),
            "opponent_reveal": agent.get_opponent_reveal(),
        }

        # Persist to database
        video_url = session_data.get("video_url")
        persist_postmortem_to_db(session_id, frontend_result, video_url)

        logger.info(f"Post-mortem analysis complete for {session_id}")
        return {"status": "complete", "session_id": session_id}

    except Exception as e:
        logger.error(f"Post-mortem analysis failed for {session_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(e)}"
        )


@postmortem_router.get("/post_mortem/{session_id}")
async def get_post_mortem(session_id: str):
    """
    Retrieve post-mortem analysis results.

    Returns the frontend-compatible result format.
    """
    logger.info(f"Fetching post-mortem for session {session_id}")

    # Check if analysis exists
    if session_id not in _analysis_store:
        # Try to run analysis if session data exists
        session_data = get_session_data(session_id)
        if session_data:
            # Trigger analysis
            await request_post_mortem(PostMortemRequest(session_id=session_id))
        else:
            raise HTTPException(
                status_code=404,
                detail=f"No analysis found for session {session_id}"
            )

    analysis_data = _analysis_store.get(session_id)
    if not analysis_data:
        raise HTTPException(
            status_code=404,
            detail=f"Analysis not found for session {session_id}"
        )

    return analysis_data["frontend_result"]


@postmortem_router.get("/post_mortem/{session_id}/full")
async def get_full_post_mortem(session_id: str):
    """
    Retrieve the full post-mortem analysis including raw data.

    This includes:
    - raw_analysis: The complete agent analysis
    - frontend_result: The transformed frontend format
    - summary_text: Human-readable summary
    - opponent_reveal: What the opponent was really thinking
    """
    if session_id not in _analysis_store:
        raise HTTPException(
            status_code=404,
            detail=f"No analysis found for session {session_id}"
        )

    return _analysis_store[session_id]


@postmortem_router.post("/post_mortem/{session_id}/store")
async def store_session(session_id: str, data: SessionData):
    """
    Store session data for later analysis.

    This endpoint is called when a negotiation ends to persist
    the session data needed for post-mortem analysis.
    """
    store_session_data(session_id, data.model_dump())
    return {"status": "stored", "session_id": session_id}


class VideoUrlUpdate(BaseModel):
    """Request to update video URL for a session."""
    video_url: str


@postmortem_router.post("/post_mortem/{session_id}/video")
async def update_session_video_url(session_id: str, data: VideoUrlUpdate):
    """
    Associate a video URL with a post-mortem session.

    Called after video upload completes to link the video to the analysis.
    """
    # Update in-memory store
    if session_id in _session_store:
        _session_store[session_id]["video_url"] = data.video_url

    # Update in database if analysis already exists
    if session_id in _analysis_store:
        persist_postmortem_to_db(
            session_id,
            _analysis_store[session_id]["frontend_result"],
            data.video_url
        )

    return {"status": "updated", "session_id": session_id}
