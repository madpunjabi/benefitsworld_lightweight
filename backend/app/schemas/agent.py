from pydantic import BaseModel


class AgentStatusOut(BaseModel):
    case_status: str
    open_requirements: list[str]
