from pydantic import BaseModel


class CoreStats(BaseModel):
    version: str
    local_enabled: bool = True
    started: bool
    logs_websocket: str
