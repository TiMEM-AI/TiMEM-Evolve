"""核心模块的单元测试"""
import pytest
import os
import shutil
from pathlib import Path
import json
from datetime import datetime

from timem_evolve.dao.memory_dao import MemoryDAO
from timem_evolve.services.session_service import SessionService
from timem_evolve.services.learner_service import LearnerService
from timem_evolve.models import Session, SessionCreate, Message, FeedbackCreate, Skill, Rule

# 模拟 LLM 响应
MOCK_SKILL_RESPONSE = {
    "name": "清晰的代码解释",
    "description": "以清晰、分步的方式解释代码，确保理解。",
    "steps": ["分析代码功能", "分解为小块", "解释每块的作用"],
    "sop": "在解释代码时，先概述其功能，然后将代码分解为逻辑块，逐一解释每个块的作用和输入输出，最后总结。",
    "confidence": 0.9
}

MOCK_RULE_RESPONSE = {
    "name": "避免技术黑话",
    "description": "在非技术用户面前，避免使用过于专业的术语。",
    "constraint": "避免使用如 'Monad', 'Functor', 'Currying' 等高级函数式编程术语。",
    "reason": "这些术语会使用户感到困惑，降低沟通效率。",
    "confidence": 0.8
}


@pytest.fixture(scope="module")
def test_data_dir():
    """为测试创建一个临时数据目录"""
    temp_dir = Path("./test_data")
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    temp_dir.mkdir()
    yield str(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def memory_dao(test_data_dir):
    """MemoryDAO 实例"""
    dao = MemoryDAO(data_dir=test_data_dir)
    # 清理文件
    dao.skills_path.write_text("[]")
    dao.rules_path.write_text("[]")
    dao.feedbacks_path.write_text("[]")
    return dao


@pytest.fixture
async def session_service(memory_dao):
    """SessionService 实例"""
    await memory_dao.init_db()
    return SessionService(memory_dao)


@pytest.fixture
def mock_llm(mocker):
    """模拟 ChatOpenAI 的 ainovke 方法"""
    
    def mock_ainvoke(messages):
        # 简单的模拟，根据提示词判断是提炼技能还是规则
        prompt = messages[-1].content
        
        if "提炼一个可复用的技能" in prompt:
            response_data = MOCK_SKILL_RESPONSE
        elif "提炼一个约束规则" in prompt:
            response_data = MOCK_RULE_RESPONSE
        elif "success" in prompt.lower() or "failure" in prompt.lower():
            # Coach 评估结果
            return mocker.MagicMock(content="success")
        else:
            # Coach 生成任务或 Learner 模拟回复
            return mocker.MagicMock(content="这是一个模拟的回复。")
            
        json_content = json.dumps(response_data, indent=2, ensure_ascii=False)
        mock_response = mocker.MagicMock(content=f"```json\n{json_content}\n```")
        return mock_response

    mock_chat_openai = mocker.patch("timem_evolve.services.learner_service.ChatOpenAI")
    mock_chat_openai.return_value.ainvoke = mocker.AsyncMock(side_effect=mock_ainvoke)
    
    mock_coach_openai = mocker.patch("timem_evolve.services.coach_service.ChatOpenAI")
    mock_coach_openai.return_value.ainvoke = mocker.AsyncMock(side_effect=mock_ainvoke)
    
    return mock_chat_openai


@pytest.fixture
def learner_service(memory_dao, mock_llm):
    """LearnerService 实例"""
    return LearnerService(memory_dao)


@pytest.mark.asyncio
async def test_dao_session_operations(memory_dao):
    """测试 Session 的 DAO 操作"""
    await memory_dao.init_db()
    
    session_data = SessionCreate(
        task="测试任务",
        messages=[
            Message(role="user", content="你好"),
            Message(role="assistant", content="你好，我是AI")
        ],
        outcome="success"
    )
    session = Session(**session_data.model_dump())
    
    await memory_dao.save_session(session)
    
    retrieved_session = await memory_dao.get_session(session.session_id)
    assert retrieved_session is not None
    assert retrieved_session.task == "测试任务"
    assert len(retrieved_session.messages) == 2
    
    sessions = await memory_dao.list_sessions()
    assert len(sessions) == 1
    
    sessions_fail = await memory_dao.list_sessions(outcome="failure")
    assert len(sessions_fail) == 0


def test_dao_skill_operations(memory_dao):
    """测试 Skill 的 DAO 操作"""
    skill = Skill(
        name="测试技能",
        description="描述",
        workflow={"steps": ["a"], "sop": "b"},
        confidence=0.9
    )
    
    memory_dao.save_skill(skill)
    
    retrieved_skill = memory_dao.get_skill(skill.skill_id)
    assert retrieved_skill is not None
    assert retrieved_skill.name == "测试技能"
    
    skills = memory_dao.list_skills()
    assert len(skills) == 1
    
    search_results = memory_dao.search_skills("测试")
    assert len(search_results) == 1


@pytest.mark.asyncio
async def test_session_service_add_and_get(session_service):
    """测试 SessionService 的添加和获取"""
    session_create = SessionCreate(
        task="服务测试任务",
        messages=[Message(role="user", content="hi")],
        outcome="success"
    )
    
    session = await session_service.add_session(session_create)
    assert session.task == "服务测试任务"
    
    retrieved = await session_service.get_session(session.session_id)
    assert retrieved.session_id == session.session_id


@pytest.mark.asyncio
async def test_learner_service_learn_from_positive_feedback(session_service, learner_service, memory_dao):
    """测试 LearnerService 从好评反馈中学习技能"""
    # 1. 创建一个成功的会话
    session_create = SessionCreate(
        task="学习技能任务",
        messages=[
            Message(role="user", content="如何实现快速排序？"),
            Message(role="assistant", content="快速排序的步骤是...")
        ],
        outcome="success"
    )
    session = await session_service.add_session(session_create)
    
    # 2. 创建好评反馈
    feedback_create = FeedbackCreate(
        session_id=session.session_id,
        message_index=1, # AI 回复的索引
        rating="positive",
        comment="解释得非常清楚，步骤很详细。"
    )
    feedback = learner_service.dao.save_feedback(feedback_create)
    
    # 3. 触发学习
    learned_id = await learner_service.learn_from_feedback(feedback)
    assert learned_id is not None
    
    # 4. 验证技能是否被保存
    skills = memory_dao.list_skills()
    assert len(skills) == 1
    assert skills[0].skill_id == learned_id
    assert skills[0].name == MOCK_SKILL_RESPONSE["name"]
    
    # 5. 验证反馈状态是否更新
    updated_feedback = memory_dao.get_feedback(feedback.feedback_id)
    assert updated_feedback.learned is True
    assert updated_feedback.learned_skill_id == learned_id


@pytest.mark.asyncio
async def test_learner_service_learn_from_negative_feedback(session_service, learner_service, memory_dao):
    """测试 LearnerService 从差评反馈中学习规则"""
    # 1. 创建一个失败的会话
    session_create = SessionCreate(
        task="学习规则任务",
        messages=[
            Message(role="user", content="请解释一下 Monad 是什么？"),
            Message(role="assistant", content="Monad 是一个自函子范畴...")
        ],
        outcome="failure"
    )
    session = await session_service.add_session(session_create)
    
    # 2. 创建差评反馈
    feedback_create = FeedbackCreate(
        session_id=session.session_id,
        message_index=1, # AI 回复的索引
        rating="negative",
        comment="解释太学术了，完全听不懂。"
    )
    feedback = learner_service.dao.save_feedback(feedback_create)
    
    # 3. 触发学习
    learned_id = await learner_service.learn_from_feedback(feedback)
    assert learned_id is not None
    
    # 4. 验证规则是否被保存
    rules = memory_dao.list_rules()
    assert len(rules) == 1
    assert rules[0].rule_id == learned_id
    assert rules[0].name == MOCK_RULE_RESPONSE["name"]
    
    # 5. 验证反馈状态是否更新
    updated_feedback = memory_dao.get_feedback(feedback.feedback_id)
    assert updated_feedback.learned is True
    assert updated_feedback.learned_rule_id == learned_id
