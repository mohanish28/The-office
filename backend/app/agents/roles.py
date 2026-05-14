import json
from dataclasses import dataclass

from app.agents.base import BaseAgent

@dataclass
class CTOVerdict:
    verdict: str
    reasoning: str
    line_citations: list[str]
    risk_level: str


@dataclass
class SafetyReport:
    safety_score: float
    issues: list[str]
    approved: bool
    recommendation: str


@dataclass
class QAReport:
    passed: bool
    findings: list[str]
    severity: str
    summary: str


@dataclass
class SeniorLeadReview:
    feedback: str
    action_items: list[str]
    priority: str
    confidence: float


@dataclass
class PMPlan:
    milestones: list[str]
    timeline: str
    resources: list[str]
    risks: list[str]


@dataclass
class FrontendCode:
    components: list[str]
    styling_notes: str
    dependencies: list[str]
    notes: str


@dataclass
class BackendCode:
    endpoints: list[str]
    models: list[str]
    services: list[str]
    notes: str


@dataclass
class APIDesign:
    routes: list[str]
    schemas: list[str]
    auth_strategy: str
    version: str


@dataclass
class DevOpsPlan:
    infrastructure: list[str]
    cicd_steps: list[str]
    monitoring: list[str]
    cost_estimate: str


@dataclass
class ExtractionResult:
    entities: list[str]
    relationships: list[str]
    raw_text: str
    confidence: float


@dataclass
class SearchResult:
    sources: list[str]
    relevance_scores: list[float]
    answer: str
    context_chunks: list[str]

MODEL_MAP = {
    "CTO": "nvidia/nemotron-3-super-120b-a12b",
    "SeniorLead": "moonshotai/kimi-k2.6",
    "PM": "minimaxai/minimax-m2.7",
    "FrontendDev": "deepseek-ai/deepseek-v4-flash",
    "BackendDev": "deepseek-ai/deepseek-v4-pro",
    "APIEngineer": "z-ai/glm-5.1",
    "DevOps": "mistralai/mistral-medium-3.5-128b",
    "QA": "mistralai/mistral-small-4-119b-2603",
    "Safety": "nvidia/nemotron-3-content-safety",
    "DataExtractor": "nvidia/nemotron-ocr-v1",
    "RAGSearch": "nvidia/llama-nemotron-rerank-vl",
}


def _safe_json_parse(raw: str) -> dict:
    try:
        return json.loads(raw)
    except Exception:
        return {}


def _as_list(value: object) -> list:
    if isinstance(value, list):
        return value
    return []


def _as_float(value: object, fallback: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return fallback

class CTOAgent(BaseAgent):
    model = MODEL_MAP["CTO"]
    system_prompt = (
        "You are the CTO. Review the provided context and output strict JSON with keys: "
        "verdict (APPROVE/REVISE/REJECT), reasoning (string), line_citations (list of strings), "
        "risk_level (string)."
    )

    async def run(self, context: dict) -> CTOVerdict:
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": json.dumps(context)},
        ]
        raw = await self._call_nim(messages)
        data = _safe_json_parse(raw)
        verdict = data.get("verdict", "UNKNOWN")
        if verdict not in ("APPROVE", "REVISE", "REJECT"):
            verdict = "UNKNOWN"
        return CTOVerdict(
            verdict=verdict,
            reasoning=data.get("reasoning", ""),
            line_citations=_as_list(data.get("line_citations")),
            risk_level=data.get("risk_level", "UNKNOWN"),
        )


class SafetyReviewer(BaseAgent):
    model = MODEL_MAP["Safety"]
    system_prompt = (
        "You are the Safety reviewer. Inspect the context and output strict JSON with keys: "
        "safety_score (float 0.0-1.0), issues (list of strings), approved (boolean), "
        "recommendation (string)."
    )

    async def run(self, context: dict) -> SafetyReport:
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": json.dumps(context)},
        ]
        raw = await self._call_nim(messages)
        data = _safe_json_parse(raw)
        score = _as_float(data.get("safety_score"), 0.0)
        approved = score >= 0.5 and bool(data.get("approved", False))
        return SafetyReport(
            safety_score=score,
            issues=_as_list(data.get("issues")),
            approved=approved,
            recommendation=data.get("recommendation", ""),
        )


class QAReviewer(BaseAgent):
    model = MODEL_MAP["QA"]
    system_prompt = (
        "You are the QA reviewer. Evaluate the context and output strict JSON with keys: "
        "passed (boolean), findings (list of strings), severity (string), summary (string)."
    )

    async def run(self, context: dict) -> QAReport:
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": json.dumps(context)},
        ]
        raw = await self._call_nim(messages)
        data = _safe_json_parse(raw)
        return QAReport(
            passed=bool(data.get("passed", False)),
            findings=_as_list(data.get("findings")),
            severity=data.get("severity", "UNKNOWN"),
            summary=data.get("summary", ""),
        )


class SeniorLead(BaseAgent):
    model = MODEL_MAP["SeniorLead"]
    system_prompt = (
        "You are a Senior Lead engineer. Review the context and output strict JSON with keys: "
        "feedback (string), action_items (list of strings), priority (string), confidence (float)."
    )

    async def run(self, context: dict) -> SeniorLeadReview:
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": json.dumps(context)},
        ]
        raw = await self._call_nim(messages)
        data = _safe_json_parse(raw)
        return SeniorLeadReview(
            feedback=data.get("feedback", ""),
            action_items=_as_list(data.get("action_items")),
            priority=data.get("priority", "UNKNOWN"),
            confidence=_as_float(data.get("confidence"), 0.0),
        )


class PMAgent(BaseAgent):
    model = MODEL_MAP["PM"]
    system_prompt = (
        "You are a Product Manager. Analyze the context and output strict JSON with keys: "
        "milestones (list of strings), timeline (string), resources (list of strings), risks (list of strings)."
    )

    async def run(self, context: dict) -> PMPlan:
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": json.dumps(context)},
        ]
        raw = await self._call_nim(messages)
        data = _safe_json_parse(raw)
        return PMPlan(
            milestones=_as_list(data.get("milestones")),
            timeline=data.get("timeline", ""),
            resources=_as_list(data.get("resources")),
            risks=_as_list(data.get("risks")),
        )


class FrontendDev(BaseAgent):
    model = MODEL_MAP["FrontendDev"]
    system_prompt = (
        "You are a Frontend Developer. Review the context and output strict JSON with keys: "
        "components (list of strings), styling_notes (string), dependencies (list of strings), notes (string)."
    )

    async def run(self, context: dict) -> FrontendCode:
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": json.dumps(context)},
        ]
        raw = await self._call_nim(messages)
        data = _safe_json_parse(raw)
        return FrontendCode(
            components=_as_list(data.get("components")),
            styling_notes=data.get("styling_notes", ""),
            dependencies=_as_list(data.get("dependencies")),
            notes=data.get("notes", ""),
        )


class BackendDev(BaseAgent):
    model = MODEL_MAP["BackendDev"]
    system_prompt = (
        "You are a Backend Developer. Review the context and output strict JSON with keys: "
        "endpoints (list of strings), models (list of strings), services (list of strings), notes (string)."
    )

    async def run(self, context: dict) -> BackendCode:
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": json.dumps(context)},
        ]
        raw = await self._call_nim(messages)
        data = _safe_json_parse(raw)
        return BackendCode(
            endpoints=_as_list(data.get("endpoints")),
            models=_as_list(data.get("models")),
            services=_as_list(data.get("services")),
            notes=data.get("notes", ""),
        )


class APIEngineer(BaseAgent):
    model = MODEL_MAP["APIEngineer"]
    system_prompt = (
        "You are an API Engineer. Design based on the context and output strict JSON with keys: "
        "routes (list of strings), schemas (list of strings), auth_strategy (string), version (string)."
    )

    async def run(self, context: dict) -> APIDesign:
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": json.dumps(context)},
        ]
        raw = await self._call_nim(messages)
        data = _safe_json_parse(raw)
        return APIDesign(
            routes=_as_list(data.get("routes")),
            schemas=_as_list(data.get("schemas")),
            auth_strategy=data.get("auth_strategy", ""),
            version=data.get("version", ""),
        )


class DevOps(BaseAgent):
    model = MODEL_MAP["DevOps"]
    system_prompt = (
        "You are a DevOps engineer. Plan based on the context and output strict JSON with keys: "
        "infrastructure (list of strings), cicd_steps (list of strings), monitoring (list of strings), "
        "cost_estimate (string)."
    )

    async def run(self, context: dict) -> DevOpsPlan:
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": json.dumps(context)},
        ]
        raw = await self._call_nim(messages)
        data = _safe_json_parse(raw)
        return DevOpsPlan(
            infrastructure=_as_list(data.get("infrastructure")),
            cicd_steps=_as_list(data.get("cicd_steps")),
            monitoring=_as_list(data.get("monitoring")),
            cost_estimate=data.get("cost_estimate", ""),
        )


class DataExtractor(BaseAgent):
    model = MODEL_MAP["DataExtractor"]
    system_prompt = (
        "You are a Data Extractor. Extract information from the context and output strict JSON with keys: "
        "entities (list of strings), relationships (list of strings), raw_text (string), confidence (float)."
    )

    async def run(self, context: dict) -> ExtractionResult:
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": json.dumps(context)},
        ]
        raw = await self._call_nim(messages)
        data = _safe_json_parse(raw)
        return ExtractionResult(
            entities=_as_list(data.get("entities")),
            relationships=_as_list(data.get("relationships")),
            raw_text=data.get("raw_text", ""),
            confidence=_as_float(data.get("confidence"), 0.0),
        )


class RAGSearch(BaseAgent):
    model = MODEL_MAP["RAGSearch"]
    system_prompt = (
        "You are a RAG Search agent. Retrieve and synthesize from the context and output strict JSON with keys: "
        "sources (list of strings), relevance_scores (list of floats), answer (string), context_chunks (list of strings)."
    )

    async def run(self, context: dict) -> SearchResult:
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": json.dumps(context)},
        ]
        raw = await self._call_nim(messages)
        data = _safe_json_parse(raw)
        return SearchResult(
            sources=_as_list(data.get("sources")),
            relevance_scores=[_as_float(s) for s in _as_list(data.get("relevance_scores"))],
            answer=data.get("answer", ""),
            context_chunks=_as_list(data.get("context_chunks")),
        )
