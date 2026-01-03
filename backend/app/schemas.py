from pydantic import BaseModel, ConfigDict

class TaskCreate(BaseModel):
    title: str
    completed: bool = False

class TaskOut(TaskCreate):
    id: int
    owner_id: int
    model_config = ConfigDict(from_attributes=True)
