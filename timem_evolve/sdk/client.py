"""TiMEM-Evolve SDK 客户端"""
import requests
from typing import List, Optional, Dict, Any
import os

from ..models import (
    Session, SessionCreate, 
    Skill, Rule, 
    Feedback, FeedbackCreate,
    CoachTask, CoachState, CoachTaskCreate
)


class EvolveClient:
    """
    TiMEM-Evolve 后端服务的 Python SDK 客户端。
    用于简化对 FastAPI 接口的调用。
    """
    
    def __init__(self, base_url: Optional[str] = None):
        self.base_url = base_url or os.environ.get("EVOLVE_API_URL", "http://127.0.0.1:8000")
        if not self.base_url.endswith("/"):
            self.base_url += "/"
            
    def _request(self, method: str, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Any:
        """通用请求方法"""
        url = f"{self.base_url}{endpoint}"
        try:
            if method == "GET":
                response = requests.get(url, params=data)
            elif method == "POST":
                response = requests.post(url, json=data)
            else:
                raise ValueError(f"Unsupported method: {method}")
                
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            print(f"HTTP Error for {url}: {e.response.status_code} - {e.response.text}")
            raise
        except requests.exceptions.RequestException as e:
            print(f"Request Error for {url}: {e}")
            raise
            
    # ==================== Sessions ====================
    
    def add_session(self, session_create: SessionCreate) -> Session:
        """添加新会话"""
        data = self._request("POST", "sessions", session_create.model_dump())
        return Session(**data)

    def get_session(self, session_id: str) -> Optional[Session]:
        """获取会话"""
        try:
            data = self._request("GET", f"sessions/{session_id}")
            return Session(**data)
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                return None
            raise

    def list_sessions(self, outcome: Optional[str] = None, limit: int = 100) -> List[Session]:
        """列出会话"""
        params = {"limit": limit}
        if outcome:
            params["outcome"] = outcome
        data = self._request("GET", "sessions", params)
        return [Session(**item) for item in data]

    # ==================== Feedbacks ====================

    def add_feedback(self, feedback_create: FeedbackCreate) -> Feedback:
        """添加反馈并触发学习"""
        data = self._request("POST", "feedbacks", feedback_create.model_dump())
        return Feedback(**data)

    def list_feedbacks(self, session_id: Optional[str] = None, learned: Optional[bool] = None, limit: int = 100) -> List[Feedback]:
        """列出反馈"""
        params = {"limit": limit}
        if session_id:
            params["session_id"] = session_id
        if learned is not None:
            params["learned"] = learned
        data = self._request("GET", "feedbacks", params)
        return [Feedback(**item) for item in data]

    # ==================== Skills ====================

    def list_skills(self, limit: int = 100) -> List[Skill]:
        """列出技能"""
        data = self._request("GET", "skills", {"limit": limit})
        return [Skill(**item) for item in data]

    def search_skills(self, query: str, top_k: int = 5) -> List[Skill]:
        """搜索技能"""
        data = self._request("GET", "skills/search", {"query": query, "top_k": top_k})
        return [Skill(**item) for item in data]

    # ==================== Rules ====================

    def list_rules(self, limit: int = 100) -> List[Rule]:
        """列出规则"""
        data = self._request("GET", "rules", {"limit": limit})
        return [Rule(**item) for item in data]

    def search_rules(self, query: str, top_k: int = 5) -> List[Rule]:
        """搜索规则"""
        data = self._request("GET", "rules/search", {"query": query, "top_k": top_k})
        return [Rule(**item) for item in data]

    # ==================== Learning ====================

    def learn_from_session(self, session_id: str) -> Optional[str]:
        """从完整的会话中学习（成功->技能，失败->规则）"""
        data = self._request("POST", f"learn/session/{session_id}")
        return data

    # ==================== Coach ====================

    def get_coach_state(self) -> CoachState:
        """获取 Coach 模块的统计状态"""
        data = self._request("GET", "coach/state")
        return CoachState(**data)

    def generate_coach_task(self, task_create: CoachTaskCreate) -> CoachTask:
        """生成一个新的 Coach 任务"""
        data = self._request("POST", "coach/generate_task", task_create.model_dump())
        return CoachTask(**data)

    def run_coach_task(self, task_id: str) -> CoachTask:
        """运行一个 Coach 任务"""
        data = self._request("POST", f"coach/run_task/{task_id}")
        return CoachTask(**data)

    def list_coach_tasks(self, status: Optional[str] = None) -> List[CoachTask]:
        """列出 Coach 任务"""
        params = {}
        if status:
            params["status"] = status
        data = self._request("GET", "coach/tasks", params)
        return [CoachTask(**item) for item in data]
