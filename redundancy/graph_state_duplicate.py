from pydantic import BaseModel
from typing import List
from langchain_core.messages import BaseMessage

class GraphState(BaseModel):
    messages: List[BaseMessage]