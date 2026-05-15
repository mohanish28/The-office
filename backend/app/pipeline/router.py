FULL = [
    ["PM"],
    ["BackendDev", "FrontendDev", "DevOps"],
    ["QA", "Safety"],
    ["SeniorLead"],
    ["CTO"],
]

FRONTEND = [
    ["PM"],
    ["FrontendDev"],
    ["QA", "Safety"],
    ["SeniorLead"],
    ["CTO"],
]

BACKEND = [
    ["PM"],
    ["BackendDev"],
    ["QA", "Safety"],
    ["SeniorLead"],
    ["CTO"],
]

DEVOPS = [
    ["PM"],
    ["DevOps"],
    ["QA", "Safety"],
    ["SeniorLead"],
    ["CTO"],
]

DATA = [
    ["PM"],
    ["DataEngineer"],
    ["QA", "Safety"],
    ["SeniorLead"],
    ["CTO"],
]

PIPELINES = {
    "full": FULL,
    "frontend": FRONTEND,
    "backend": BACKEND,
    "devops": DEVOPS,
    "data": DATA,
}


def route_task(task_type: str) -> list[list[str]]:
    return PIPELINES.get(task_type, FULL)
