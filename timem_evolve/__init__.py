"""TiMEM-Evolve: Build Agents that EVOLVE Over Time"""

__version__ = "0.1.0"

from .dao.memory_dao import MemoryDAO
from .services.session_service import SessionService
from .services.analyzer_service import AnalyzerService
from .services.learner_service import LearnerService
from .services.coach_service import CoachAgent

from .models import (
    Session, SessionCreate, Message, Skill, Rule, Feedback, FeedbackCreate,
    CoachTask, CoachTaskCreate, CoachState
)

__all__ = [
    "MemoryDAO",
    "SessionService",
    "AnalyzerService",
    "LearnerService",
    "CoachAgent",
    "Session",
    "SessionCreate",
    "Message",
    "Skill",
    "Rule",
    "Feedback",
    "FeedbackCreate",
    "CoachTask",
    "CoachTaskCreate",
    "CoachState",
]
