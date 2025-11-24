"""记忆存储层"""
import json
import aiosqlite
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime

from ..models import Session, Skill, Rule, Feedback


class MemoryDAO:
    """记忆存储管理器"""
    
    def __init__(self, data_dir: str = "./data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.db_path = self.data_dir / "sessions.db"
        self.skills_path = self.data_dir / "skills.json"
        self.rules_path = self.data_dir / "rules.json"
        self.feedbacks_path = self.data_dir / "feedbacks.json"
        
        # 初始化文件
        if not self.skills_path.exists():
            self.skills_path.write_text("[]")
        if not self.rules_path.exists():
            self.rules_path.write_text("[]")
        if not self.feedbacks_path.exists():
            self.feedbacks_path.write_text("[]")
    
    async def init_db(self):
        """初始化数据库"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    task TEXT NOT NULL,
                    messages TEXT NOT NULL,
                    outcome TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    metadata TEXT
                )
            """)
            await db.commit()
    
    # ==================== Sessions ====================
    
    async def save_session(self, session: Session) -> None:
        """保存会话"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT OR REPLACE INTO sessions 
                (session_id, task, messages, outcome, timestamp, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    session.session_id,
                    session.task,
                    json.dumps([msg.model_dump() for msg in session.messages]),
                    session.outcome,
                    session.timestamp.isoformat(),
                    json.dumps(session.metadata)
                )
            )
            await db.commit()
    
    async def get_session(self, session_id: str) -> Optional[Session]:
        """获取会话"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM sessions WHERE session_id = ?",
                (session_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return Session(
                        session_id=row["session_id"],
                        task=row["task"],
                        messages=json.loads(row["messages"]),
                        outcome=row["outcome"],
                        timestamp=datetime.fromisoformat(row["timestamp"]),
                        metadata=json.loads(row["metadata"] or "{}")
                    )
                return None
    
    async def list_sessions(
        self, 
        outcome: Optional[str] = None,
        limit: int = 100
    ) -> List[Session]:
        """列出会话"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            
            if outcome:
                query = "SELECT * FROM sessions WHERE outcome = ? ORDER BY timestamp DESC LIMIT ?"
                params = (outcome, limit)
            else:
                query = "SELECT * FROM sessions ORDER BY timestamp DESC LIMIT ?"
                params = (limit,)
            
            async with db.execute(query, params) as cursor:
                rows = await cursor.fetchall()
                return [
                    Session(
                        session_id=row["session_id"],
                        task=row["task"],
                        messages=json.loads(row["messages"]),
                        outcome=row["outcome"],
                        timestamp=datetime.fromisoformat(row["timestamp"]),
                        metadata=json.loads(row["metadata"] or "{}")
                    )
                    for row in rows
                ]
    
    # ==================== Skills ====================
    
    def _load_skills(self) -> List[Dict[str, Any]]:
        """加载技能"""
        return json.loads(self.skills_path.read_text())
    
    def _save_skills(self, skills: List[Dict[str, Any]]) -> None:
        """保存技能"""
        self.skills_path.write_text(json.dumps(skills, indent=2, ensure_ascii=False))
    
    def save_skill(self, skill: Skill) -> None:
        """保存技能"""
        skills = self._load_skills()
        
        # 检查是否已存在
        for i, s in enumerate(skills):
            if s["skill_id"] == skill.skill_id:
                skills[i] = skill.model_dump(mode='json')
                self._save_skills(skills)
                return
        
        # 新增
        skills.append(skill.model_dump(mode='json'))
        self._save_skills(skills)
    
    def get_skill(self, skill_id: str) -> Optional[Skill]:
        """获取技能"""
        skills = self._load_skills()
        for s in skills:
            if s["skill_id"] == skill_id:
                return Skill(**s)
        return None
    
    def list_skills(self, limit: int = 100) -> List[Skill]:
        """列出技能"""
        skills = self._load_skills()
        # 按创建时间倒序
        skills.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return [Skill(**s) for s in skills[:limit]]
    
    def search_skills(self, query: str, top_k: int = 5) -> List[Skill]:
        """搜索技能（简单的关键词匹配）"""
        skills = self._load_skills()
        results = []
        
        query_lower = query.lower()
        for s in skills:
            # 简单的关键词匹配
            if (query_lower in s.get("name", "").lower() or 
                query_lower in s.get("description", "").lower() or
                query_lower in s.get("workflow", {}).get("sop", "").lower()):
                results.append(Skill(**s))
        
        # 按置信度排序
        results.sort(key=lambda x: x.confidence, reverse=True)
        return results[:top_k]
    
    # ==================== Rules ====================
    
    def _load_rules(self) -> List[Dict[str, Any]]:
        """加载规则"""
        return json.loads(self.rules_path.read_text())
    
    def _save_rules(self, rules: List[Dict[str, Any]]) -> None:
        """保存规则"""
        self.rules_path.write_text(json.dumps(rules, indent=2, ensure_ascii=False))
    
    def save_rule(self, rule: Rule) -> None:
        """保存规则"""
        rules = self._load_rules()
        
        # 检查是否已存在
        for i, r in enumerate(rules):
            if r["rule_id"] == rule.rule_id:
                rules[i] = rule.model_dump(mode='json')
                self._save_rules(rules)
                return
        
        # 新增
        rules.append(rule.model_dump(mode='json'))
        self._save_rules(rules)
    
    def get_rule(self, rule_id: str) -> Optional[Rule]:
        """获取规则"""
        rules = self._load_rules()
        for r in rules:
            if r["rule_id"] == rule_id:
                return Rule(**r)
        return None
    
    def list_rules(self, limit: int = 100) -> List[Rule]:
        """列出规则"""
        rules = self._load_rules()
        # 按创建时间倒序
        rules.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return [Rule(**r) for r in rules[:limit]]
    
    def search_rules(self, query: str, top_k: int = 5) -> List[Rule]:
        """搜索规则（简单的关键词匹配）"""
        rules = self._load_rules()
        results = []
        
        query_lower = query.lower()
        for r in rules:
            # 简单的关键词匹配
            if (query_lower in r.get("name", "").lower() or 
                query_lower in r.get("description", "").lower() or
                query_lower in r.get("constraint", "").lower()):
                results.append(Rule(**r))
        
        # 按置信度排序
        results.sort(key=lambda x: x.confidence, reverse=True)
        return results[:top_k]

    # ==================== Feedbacks ====================
    
    def _load_feedbacks(self) -> List[Dict[str, Any]]:
        """加载反馈"""
        return json.loads(self.feedbacks_path.read_text())
    
    def _save_feedbacks(self, feedbacks: List[Dict[str, Any]]) -> None:
        """保存反馈"""
        self.feedbacks_path.write_text(json.dumps(feedbacks, indent=2, ensure_ascii=False))
    
    def save_feedback(self, feedback: Feedback) -> None:
        """保存反馈"""
        feedbacks = self._load_feedbacks()
        
        # 检查是否已存在
        for i, f in enumerate(feedbacks):
            if f["feedback_id"] == feedback.feedback_id:
                feedbacks[i] = feedback.model_dump(mode='json')
                self._save_feedbacks(feedbacks)
                return
        
        # 新增
        feedbacks.append(feedback.model_dump(mode='json'))
        self._save_feedbacks(feedbacks)
    
    def get_feedback(self, feedback_id: str) -> Optional[Feedback]:
        """获取反馈"""
        feedbacks = self._load_feedbacks()
        for f in feedbacks:
            if f["feedback_id"] == feedback_id:
                return Feedback(**f)
        return None
    
    def list_feedbacks(
        self, 
        session_id: Optional[str] = None,
        learned: Optional[bool] = None,
        limit: int = 100
    ) -> List[Feedback]:
        """列出反馈"""
        feedbacks = self._load_feedbacks()
        
        # 过滤
        if session_id:
            feedbacks = [f for f in feedbacks if f.get("session_id") == session_id]
        if learned is not None:
            feedbacks = [f for f in feedbacks if f.get("learned") == learned]
        
        # 按时间倒序
        feedbacks.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return [Feedback(**f) for f in feedbacks[:limit]]
