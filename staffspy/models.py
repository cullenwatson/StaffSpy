from pydantic import BaseModel

class Staff(BaseModel):
    name: str
    position: str | None = None
