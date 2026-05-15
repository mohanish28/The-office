from dataclasses import dataclass, field


@dataclass
class ApprovalChain:
    steps: list[list[str]]
    state: str = "PENDING"
    current_group_index: int = 0
    verdicts: list[dict] = field(default_factory=list)

    def start(self) -> None:
        self.state = "RUNNING"

    def current_group(self) -> list[str] | None:
        if self.current_group_index >= len(self.steps):
            return None
        return self.steps[self.current_group_index]

    def record_group_verdict(self, group_verdict: str, details: list[dict]) -> None:
        self.verdicts.append({"verdict": group_verdict, "details": details})
        if group_verdict in ("rejected", "revised"):
            self.state = "REJECTED"
            return
        self.current_group_index += 1
        if self.current_group_index >= len(self.steps):
            self.state = "APPROVED"

    def is_terminal(self) -> bool:
        return self.state in ("APPROVED", "REJECTED")
