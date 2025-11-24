"""会话管理器"""
from typing import List, Optional
from ..models import Session, SessionCreate, Message
from ..dao.memory_dao import MemoryDAO


class SessionService:
    """会话管理器"""
    
    def __init__(self, dao: MemoryDAO):
        self.dao = dao
    
    async def add_session(self, session_create: SessionCreate) -> Session:
        """添加新会话"""
        session = Session(
            task=session_create.task,
            messages=session_create.messages,
            outcome=session_create.outcome,
            metadata=session_create.metadata
        )
        
        await self.dao.save_session(session)
        return session
    
    async def get_session(self, session_id: str) -> Optional[Session]:
        """获取会话"""
        return await self.dao.get_session(session_id)
    
    async def list_sessions(
        self, 
        outcome: Optional[str] = None,
        limit: int = 100
    ) -> List[Session]:
        """列出会话"""
        return await self.dao.list_sessions(outcome=outcome, limit=limit)
