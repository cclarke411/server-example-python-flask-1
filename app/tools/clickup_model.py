import pprint
import json
from pydantic import BaseModel, Field,ValidationError
from typing import List, Optional
import instructor
from datetime import datetime
import os
from dotenv import load_dotenv
from groq import Groq
import instructor 

load_dotenv()

# Pydantic Models for Schedule
class Subtask(BaseModel):
    name: str = Field(..., description="Name of the subtask")
    description: Optional[str] = Field(None, description="Details about the subtask")
    start_date: Optional[int] = Field(None, description="Start date in UNIX timestamp")
    due_date: Optional[int] = Field(None, description="Due date in UNIX timestamp")

class Task(BaseModel):
    name: str = Field(..., description="Name of the task")
    description: Optional[str] = Field(None, description="Details about the task")
    start_date: Optional[int] = Field(None, description="Start date in UNIX timestamp")
    due_date: Optional[int] = Field(None, description="Due date in UNIX timestamp")
    subtasks: List[Subtask] = Field(default_factory=list, description="List of subtasks")

class TaskList(BaseModel):
    list_name: str = Field(..., description="Name of the task list")
    tasks: List[Task] = Field(default_factory=list, description="List of tasks in the task list")

class Schedule(BaseModel):
    schedule_name: str = Field(..., description="Name of the schedule")
    lists: List[TaskList] = Field(default_factory=list, description="Task lists within the schedule")


pprint.pprint(json.dumps(Schedule.model_json_schema()))