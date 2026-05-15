from dataclasses import dataclass

from app.pipeline.chain import ApprovalChain
from app.pipeline.orchestrator import _extract_verdict
from app.pipeline.router import route_task


class TestRouteTask:
    def test_route_task_full(self):
        groups = route_task("full")
        assert len(groups) == 5
        assert groups[0] == ["PM"]
        assert len(groups[1]) == 3
        assert "BackendDev" in groups[1]
        assert "FrontendDev" in groups[1]
        assert "DevOps" in groups[1]
        assert groups[2] == ["QA", "Safety"]
        assert groups[3] == ["SeniorLead"]
        assert groups[4] == ["CTO"]

    def test_route_task_unknown_falls_back(self):
        assert route_task("xyz") == route_task("full")

    def test_route_task_frontend(self):
        groups = route_task("frontend")
        assert len(groups) == 5
        assert groups[1] == ["FrontendDev"]

    def test_route_task_backend(self):
        groups = route_task("backend")
        assert len(groups) == 5
        assert groups[1] == ["BackendDev"]

    def test_route_task_devops(self):
        groups = route_task("devops")
        assert len(groups) == 5
        assert groups[1] == ["DevOps"]

    def test_route_task_data(self):
        groups = route_task("data")
        assert len(groups) == 5
        assert groups[1] == ["DataEngineer"]


class TestApprovalChain:
    def test_chain_approve_path(self):
        chain = ApprovalChain(steps=[["PM"], ["QA"], ["CTO"]])
        chain.start()
        assert chain.state == "RUNNING"

        chain.record_group_verdict("approved", [{"role": "PM", "verdict": "approved"}])
        assert chain.state == "RUNNING"
        assert chain.current_group_index == 1

        chain.record_group_verdict("approved", [{"role": "QA", "verdict": "approved"}])
        assert chain.state == "RUNNING"
        assert chain.current_group_index == 2

        chain.record_group_verdict("approved", [{"role": "CTO", "verdict": "approved"}])
        assert chain.state == "APPROVED"
        assert chain.is_terminal()

    def test_chain_reject_terminal(self):
        chain = ApprovalChain(steps=[["PM"], ["QA"], ["CTO"]])
        chain.start()
        chain.record_group_verdict("approved", [{"role": "PM", "verdict": "approved"}])
        chain.record_group_verdict("rejected", [{"role": "QA", "verdict": "rejected"}])
        assert chain.state == "REJECTED"
        assert chain.is_terminal()

    def test_chain_current_group_none_when_done(self):
        chain = ApprovalChain(steps=[["PM"]])
        chain.start()
        chain.record_group_verdict("approved", [{"role": "PM", "verdict": "approved"}])
        assert chain.current_group() is None

    def test_chain_verdicts_recorded(self):
        chain = ApprovalChain(steps=[["PM"], ["CTO"]])
        chain.start()
        chain.record_group_verdict("approved", [{"role": "PM", "verdict": "approved"}])
        chain.record_group_verdict("approved", [{"role": "CTO", "verdict": "approved"}])
        assert len(chain.verdicts) == 2

    def test_chain_revised_is_terminal(self):
        chain = ApprovalChain(steps=[["PM"], ["CTO"]])
        chain.start()
        chain.record_group_verdict("revised", [{"role": "PM", "verdict": "revised"}])
        assert chain.state == "REJECTED"
        assert chain.is_terminal()


class TestExtractVerdict:
    def test_extract_verdict_cto_approve(self):
        @dataclass
        class R:
            verdict: str
        assert _extract_verdict("CTO", R(verdict="APPROVE")) == "approved"

    def test_extract_verdict_cto_revise(self):
        @dataclass
        class R:
            verdict: str
        assert _extract_verdict("CTO", R(verdict="REVISE")) == "revised"

    def test_extract_verdict_cto_reject(self):
        @dataclass
        class R:
            verdict: str
        assert _extract_verdict("CTO", R(verdict="REJECT")) == "rejected"

    def test_extract_verdict_qa_pass(self):
        @dataclass
        class R:
            passed: bool
        assert _extract_verdict("QA", R(passed=True)) == "approved"

    def test_extract_verdict_qa_fail(self):
        @dataclass
        class R:
            passed: bool
        assert _extract_verdict("QA", R(passed=False)) == "rejected"

    def test_extract_verdict_safety_approved(self):
        @dataclass
        class R:
            approved: bool
        assert _extract_verdict("Safety", R(approved=True)) == "approved"

    def test_extract_verdict_safety_rejected(self):
        @dataclass
        class R:
            approved: bool
        assert _extract_verdict("Safety", R(approved=False)) == "rejected"

    def test_extract_verdict_pm_always_approved(self):
        @dataclass
        class R:
            milestones: list
        assert _extract_verdict("PM", R(milestones=[])) == "approved"

    def test_extract_verdict_backend_always_approved(self):
        @dataclass
        class R:
            endpoints: list
        assert _extract_verdict("BackendDev", R(endpoints=[])) == "approved"

    def test_extract_verdict_senior_lead_always_approved(self):
        @dataclass
        class R:
            feedback: str
        assert _extract_verdict("SeniorLead", R(feedback="ok")) == "approved"
