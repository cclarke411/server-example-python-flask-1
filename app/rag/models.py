from pydantic import BaseModel, Field
from enum import Enum
from typing import Optional, List, Dict

class Category(str, Enum):
    User_Preference = "Preference"
    Topic_Interest = "Interest"
    User_Question = "Question"
    User_Attribute = "Attribute"

class Action(str, Enum):
    Create = "Create"
    Update = "Update"
    Delete = "Delete"
    Retrieve = "Retrieve"

class AddKnowledge(BaseModel):
    user_id: str = Field(..., description="ID of the user")
    key: str = Field(..., description="Key representing the type of knowledge")
    knowledge: str = Field(..., description="Condensed bit of knowledge to be saved for future reference in the format: [user(s) this is relevant to] [fact to store]")
    knowledge_old: Optional[str] = Field(None, description="If updating or deleting a record, the complete, exact phrase that needs to be modified")
    category: Category = Field(..., description="Category that this knowledge belongs to")
    action: Action = Field(..., description="Whether this knowledge is adding a new record, updating a record, or deleting a record")

class UserQueryData(BaseModel):
    user_id: str
    key: str
    value: str
    action: Action
    category: Category

class UserProfile(BaseModel):
    user_id: str
    goals: List[str]
    interactions: List[Dict] = []

class MemoryData(BaseModel):
    context: List[str] = []

class LLMResponse(BaseModel):
    followup: bool
    response: str
    update_db: bool