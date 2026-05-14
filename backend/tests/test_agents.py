import json

import httpx
import openai
import pytest
import respx
from httpx import Response

from app.agents.roles import (
    APIEngineer,
    APIDesign,
    BackendCode,
    BackendDev,
    CTOAgent,
    CTOVerdict,
    DataExtractor,
    DevOps,
    DevOpsPlan,
    ExtractionResult,
    FrontendCode,
    FrontendDev,
    MODEL_MAP,
    PMPlan,
    PMAgent,
    QAReport,
    QAReviewer,
    RAGSearch,
    SafetyReport,
    SafetyReviewer,
    SearchResult,
    SeniorLead,
    SeniorLeadReview,
)

NIM_BASE = "https://integrate.api.nvidia.com/v1"


def _router() -> respx.Router:
    return respx.Router(assert_all_called=False)


def _bind_agent(agent, router: respx.Router):
    agent.client = openai.AsyncOpenAI(
        base_url=NIM_BASE,
        api_key="nvapi-test",
        max_retries=0,
        http_client=httpx.AsyncClient(transport=httpx.MockTransport(router.handler)),
    )
    return agent


def _nim_response(payload: dict, status: int = 200) -> Response:
    body = {
        "id": "chatcmpl-test",
        "object": "chat.completion",
        "created": 1,
        "model": "test-model",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": json.dumps(payload),
                },
                "finish_reason": "stop",
            }
        ],
    }
    return Response(status, json=body)


@pytest.mark.asyncio
async def test_cto_agent_returns_cto_verdict():
    router = _router()
    route = router.post(f"{NIM_BASE}/chat/completions").mock(
        return_value=_nim_response(
            {"verdict": "APPROVE", "reasoning": "ok", "line_citations": ["L1"], "risk_level": "LOW"}
        )
    )
    agent = _bind_agent(CTOAgent(), router)
    result = await agent.run({"task": "review"})
    assert isinstance(result, CTOVerdict)
    assert result.verdict == "APPROVE"
    assert route.call_count == 1


@pytest.mark.asyncio
async def test_safety_reviewer_returns_safety_report():
    router = _router()
    route = router.post(f"{NIM_BASE}/chat/completions").mock(
        return_value=_nim_response(
            {"safety_score": 0.9, "issues": [], "approved": True, "recommendation": " proceed"}
        )
    )
    agent = _bind_agent(SafetyReviewer(), router)
    result = await agent.run({"task": "scan"})
    assert isinstance(result, SafetyReport)
    assert result.approved is True
    assert route.call_count == 1


@pytest.mark.asyncio
async def test_qa_reviewer_returns_qa_report():
    router = _router()
    route = router.post(f"{NIM_BASE}/chat/completions").mock(
        return_value=_nim_response(
            {"passed": True, "findings": [], "severity": "NONE", "summary": "all good"}
        )
    )
    agent = _bind_agent(QAReviewer(), router)
    result = await agent.run({"task": "test"})
    assert isinstance(result, QAReport)
    assert result.passed is True
    assert route.call_count == 1


@pytest.mark.asyncio
async def test_senior_lead_returns_review():
    router = _router()
    route = router.post(f"{NIM_BASE}/chat/completions").mock(
        return_value=_nim_response(
            {"feedback": "nice", "action_items": ["a"], "priority": "LOW", "confidence": 0.95}
        )
    )
    agent = _bind_agent(SeniorLead(), router)
    result = await agent.run({"task": "lead"})
    assert isinstance(result, SeniorLeadReview)
    assert result.confidence == 0.95
    assert route.call_count == 1


@pytest.mark.asyncio
async def test_pm_agent_returns_plan():
    router = _router()
    route = router.post(f"{NIM_BASE}/chat/completions").mock(
        return_value=_nim_response(
            {"milestones": ["M1"], "timeline": "2w", "resources": ["R1"], "risks": []}
        )
    )
    agent = _bind_agent(PMAgent(), router)
    result = await agent.run({"task": "plan"})
    assert isinstance(result, PMPlan)
    assert result.milestones == ["M1"]
    assert route.call_count == 1


@pytest.mark.asyncio
async def test_frontend_dev_returns_code():
    router = _router()
    route = router.post(f"{NIM_BASE}/chat/completions").mock(
        return_value=_nim_response(
            {"components": ["C1"], "styling_notes": "css", "dependencies": ["d1"], "notes": "n"}
        )
    )
    agent = _bind_agent(FrontendDev(), router)
    result = await agent.run({"task": "ui"})
    assert isinstance(result, FrontendCode)
    assert result.components == ["C1"]
    assert route.call_count == 1


@pytest.mark.asyncio
async def test_backend_dev_returns_code():
    router = _router()
    route = router.post(f"{NIM_BASE}/chat/completions").mock(
        return_value=_nim_response(
            {"endpoints": ["E1"], "models": ["M1"], "services": ["S1"], "notes": "n"}
        )
    )
    agent = _bind_agent(BackendDev(), router)
    result = await agent.run({"task": "api"})
    assert isinstance(result, BackendCode)
    assert result.endpoints == ["E1"]
    assert route.call_count == 1


@pytest.mark.asyncio
async def test_api_engineer_returns_design():
    router = _router()
    route = router.post(f"{NIM_BASE}/chat/completions").mock(
        return_value=_nim_response(
            {"routes": ["/v1"], "schemas": ["User"], "auth_strategy": "JWT", "version": "1.0"}
        )
    )
    agent = _bind_agent(APIEngineer(), router)
    result = await agent.run({"task": "design"})
    assert isinstance(result, APIDesign)
    assert result.version == "1.0"
    assert route.call_count == 1


@pytest.mark.asyncio
async def test_devops_returns_plan():
    router = _router()
    route = router.post(f"{NIM_BASE}/chat/completions").mock(
        return_value=_nim_response(
            {
                "infrastructure": ["k8s"],
                "cicd_steps": ["build"],
                "monitoring": ["prometheus"],
                "cost_estimate": "$100",
            }
        )
    )
    agent = _bind_agent(DevOps(), router)
    result = await agent.run({"task": "deploy"})
    assert isinstance(result, DevOpsPlan)
    assert result.cost_estimate == "$100"
    assert route.call_count == 1


@pytest.mark.asyncio
async def test_data_extractor_returns_result():
    router = _router()
    route = router.post(f"{NIM_BASE}/chat/completions").mock(
        return_value=_nim_response(
            {"entities": ["E1"], "relationships": ["R1"], "raw_text": "txt", "confidence": 0.88}
        )
    )
    agent = _bind_agent(DataExtractor(), router)
    result = await agent.run({"task": "extract"})
    assert isinstance(result, ExtractionResult)
    assert result.confidence == 0.88
    assert route.call_count == 1


@pytest.mark.asyncio
async def test_rag_search_returns_result():
    router = _router()
    route = router.post(f"{NIM_BASE}/chat/completions").mock(
        return_value=_nim_response(
            {
                "sources": ["S1"],
                "relevance_scores": [0.99],
                "answer": "ans",
                "context_chunks": ["c1"],
            }
        )
    )
    agent = _bind_agent(RAGSearch(), router)
    result = await agent.run({"task": "search"})
    assert isinstance(result, SearchResult)
    assert result.answer == "ans"
    assert route.call_count == 1


@pytest.mark.asyncio
async def test_retry_on_failure():
    async with respx.mock(assert_all_called=False) as router:
        route = router.post(f"{NIM_BASE}/chat/completions")
        route.side_effect = [
            httpx.ConnectError("simulated connection failure"),
            httpx.ConnectError("simulated connection failure"),
            _nim_response(
                {"verdict": "APPROVE", "reasoning": "ok", "line_citations": ["L1"], "risk_level": "LOW"}
            ),
        ]
        agent = _bind_agent(CTOAgent(), router)
        result = await agent.run({"task": "review"})
    assert isinstance(result, CTOVerdict)
    assert result.verdict == "APPROVE"
    assert route.call_count == 3


@pytest.mark.asyncio
async def test_no_retry_on_4xx():
    async with respx.mock(assert_all_called=False) as router:
        route = router.post(f"{NIM_BASE}/chat/completions").mock(
            return_value=Response(
                401,
                json={"error": {"message": "bad api key", "type": "authentication_error"}},
            )
        )
        agent = _bind_agent(CTOAgent(), router)

        with pytest.raises(openai.APIStatusError):
            await agent.run({"task": "review"})

    assert route.call_count == 1


@pytest.mark.asyncio
async def test_safety_approved_false_when_low_score():
    router = _router()
    route = router.post(f"{NIM_BASE}/chat/completions").mock(
        return_value=_nim_response(
            {"safety_score": 0.3, "issues": ["bad"], "approved": False, "recommendation": "reject"}
        )
    )
    agent = _bind_agent(SafetyReviewer(), router)
    result = await agent.run({"task": "scan"})
    assert result.approved is False
    assert result.safety_score == 0.3
    assert route.call_count == 1


@pytest.mark.asyncio
async def test_cto_verdict_enum_validation():
    router = _router()
    route = router.post(f"{NIM_BASE}/chat/completions").mock(
        return_value=_nim_response(
            {"verdict": "REVISE", "reasoning": "r", "line_citations": [], "risk_level": "MED"}
        )
    )
    agent = _bind_agent(CTOAgent(), router)
    result = await agent.run({"task": "review"})
    assert result.verdict in ("APPROVE", "REVISE", "REJECT")
    assert route.call_count == 1


def test_model_map_has_all_roles():
    expected = {
        "CTO",
        "SeniorLead",
        "PM",
        "FrontendDev",
        "BackendDev",
        "APIEngineer",
        "DevOps",
        "QA",
        "Safety",
        "DataExtractor",
        "RAGSearch",
    }
    assert set(MODEL_MAP.keys()) == expected
