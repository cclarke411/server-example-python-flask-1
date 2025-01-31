import requests
from pydantic import BaseModel, Field, ValidationError
from typing import List, Optional
import instructor
from datetime import datetime
import os
from dotenv import load_dotenv
from groq import Groq
import instructor 
import asyncio
from openai import OpenAI

load_dotenv()

# Pydantic Models for Schedule
class Subtask(BaseModel):
    name: str = Field(..., description="Name of the subtask")
    description: Optional[str] = Field(None, description="Details about the subtask")
    start_date: Optional[int] = Field(None, description="Start date in UNIX timestamp")
    due_date: Optional[int] = Field(None, description="Due date in UNIX timestamp")
    priority: Optional[int] = Field(None, description="ClickUp priority (0=none, 1=low, 2=normal, 3=high, 4=urgent)")
    link: Optional[str] = Field(None, description="Optional reference link or URL.")
    depends_on: Optional[List[str]] = Field(None, description="List of other tasks/subtasks (by name) this subtask depends on.")

class Task(BaseModel):
    name: str = Field(..., description="Name of the task")
    description: Optional[str] = Field(None, description="Details about the task")
    start_date: Optional[int] = Field(None, description="Start date in UNIX timestamp")
    due_date: Optional[int] = Field(None, description="Due date in UNIX timestamp")
    priority: Optional[int] = Field(None, description="ClickUp priority (0=none, 1=low, 2=normal, 3=high, 4=urgent)")
    link: Optional[str] = Field(None, description="Optional reference link or URL.")
    depends_on: Optional[List[str]] = Field(None, description="List of other tasks (by name) this task depends on.")
    subtasks: List[Subtask] = Field(default_factory=list, description="List of subtasks")

class TaskList(BaseModel):
    list_name: str = Field(..., description="Name of the task list")
    tasks: List[Task] = Field(default_factory=list, description="List of tasks in the task list")

class Schedule(BaseModel):
    schedule_name: str = Field(..., description="Name of the schedule")
    lists: List[TaskList] = Field(default_factory=list, description="Task lists within the schedule")

# OpenAI Client Setup
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
client = instructor.from_openai(client)

# API Functions
API_TOKEN = os.environ.get("CLICKUP_API_KEY")
BASE_URL = "https://api.clickup.com/api/v2"

async def get_folders(space_id):
    url = f"{BASE_URL}/space/{space_id}/folder"
    headers = {"Authorization": API_TOKEN}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Error retrieving folders: {response.status_code} - {response.text}")

async def create_folder(space_id, folder_name):
    url = f"{BASE_URL}/space/{space_id}/folder"
    payload = {"name": folder_name}
    headers = {"Authorization": API_TOKEN, "Content-Type": "application/json"}
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 200:
        return response.json().get("id")
    else:
        raise Exception(f"Error creating folder '{folder_name}': {response.status_code} - {response.text}")

async def create_list(folder_id, list_name):
    url = f"{BASE_URL}/folder/{folder_id}/list"
    payload = {"name": list_name}
    headers = {"Authorization": API_TOKEN, "Content-Type": "application/json"}
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 200:
        return response.json().get("id")
    else:
        raise Exception(f"Error creating list '{list_name}': {response.status_code} - {response.text}")
    
def transform_llm_output(llm_output):
    try:
        # Validate the output against the Schedule model
        schedule = Schedule.model_validate(llm_output)
        return schedule
    except ValidationError as e:
        print(f"Validation error: {e}")
        # Logic to transform the output manually if required
        # For simplicity, reformat data here or raise an exception
        raise ValueError("LLM output does not match the expected format.")
    
async def set_dependency(task_id: str, depends_on_id: str):
    url = f"{BASE_URL}/task/{task_id}/dependency"
    payload = {"depends_on": depends_on_id}
    headers = {"Authorization": API_TOKEN, "Content-Type": "application/json"}
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code != 200:
        raise Exception(f"Error setting dependency: {response.status_code} - {response.text}")

async def create_task(
    list_id: str,
    name: str,
    description: Optional[str] = None,
    start_date: Optional[int] = None,
    due_date: Optional[int] = None,
    parent_id: Optional[str] = None,
    priority: Optional[int] = None,
    link: Optional[str] = None
) -> str:
    url = f"{BASE_URL}/list/{list_id}/task"

    # Ensure priority is valid
    if priority not in [0, 1, 2, 3, 4, None]:
        priority = None  # Default to no priority if invalid

    payload = {
        "name": name,
        "description": description or "",
        "start_date": str(start_date) if start_date else None,
        "due_date": str(due_date) if due_date else None,
        "parent": parent_id,
        "priority": priority
    }
    payload = {k: v for k, v in payload.items() if v is not None}

    headers = {"Authorization": API_TOKEN, "Content-Type": "application/json"}
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 200:
        return response.json().get("id")
    else:
        raise Exception(f"Error creating task '{name}': {response.status_code} - {response.text}")

async def process_schedule(space_id: str, schedule: Schedule):
    """
    Process a ClickUp schedule under a single folder.
    """
    # Create the main folder once for the entire schedule
    folder_id = await create_folder(space_id, schedule.schedule_name)
    name_to_id_map = {}

    # Iterate over task lists and create tasks within a single folder
    for task_list in schedule.lists:
        list_id = await create_list(folder_id, task_list.list_name)

        # Create tasks and their subtasks within the same list
        for task in task_list.tasks:
            task_id = await create_task(
                list_id=list_id,
                name=task.name,
                description=task.description,
                start_date=task.start_date,
                due_date=task.due_date,
                priority=task.priority,
                link=task.link
            )
            name_to_id_map[task.name] = task_id

            # Ensure subtasks are created directly under the same list
            for sub in task.subtasks:
                sub_id = await create_task(
                    list_id=list_id,
                    name=sub.name,
                    description=sub.description,
                    start_date=sub.start_date,
                    due_date=sub.due_date,
                    priority=sub.priority,
                    link=sub.link,
                    parent_id=task_id  # Fixed to ensure proper parent-child relation
                )
                name_to_id_map[sub.name] = sub_id

    # Second pass: Set dependencies between tasks and subtasks within the same list
    for task_list in schedule.lists:
        for task in task_list.tasks:
            if task.depends_on:
                for dep_name in task.depends_on:
                    if dep_name in name_to_id_map:
                        await set_dependency(name_to_id_map[task.name], name_to_id_map[dep_name])
            # Handle subtask dependencies
            for sub in task.subtasks:
                if sub.depends_on:
                    for dep_name in sub.depends_on:
                        if dep_name in name_to_id_map:
                            await set_dependency(name_to_id_map[sub.name], name_to_id_map[dep_name])


# Generate Schedule with Instructor Ollama
# def generate_schedule(prompt: str) -> Schedule:
#     template = f"""
#     I'm providing you with a Python class definition for a Schedule object. 
#     Your task is to generate a JSON string that accurately represents a valid instance of this Schedule object. 

#     **User Goal:** 
#     {prompt}

#     **Schedule Class:**

#     ```python
#     from pydantic import BaseModel, Field, ValidationError
#     from typing import List, Optional

#     class Subtask(BaseModel):
#         name: str = Field(..., description="Name of the subtask")
#         description: Optional[str] = Field(None, description="Details about the subtask")
#         start_date: Optional[int] = Field(None, description="Start date in UNIX timestamp")
#         due_date: Optional[int] = Field(None, description="Due date in UNIX timestamp")

#     class Task(BaseModel):
#         name: str = Field(..., description="Name of the task")
#         description: Optional[str] = Field(None, description="Details about the task")
#         start_date: Optional[int] = Field(None, description="Start date in UNIX timestamp")
#         due_date: Optional[int] = Field(None, description="Due date in UNIX timestamp")
#         subtasks: List[Subtask] = Field(default_factory=list, description="List of subtasks")

#     class TaskList(BaseModel):
#         list_name: str = Field(..., description="Name of the task list")
#         tasks: List[Task] = Field(default_factory=list, description="List of tasks in the task list")

#     class Schedule(BaseModel):
#         schedule_name: str = Field(..., description="Name of the schedule")
#         lists: List[TaskList] = Field(default_factory=list, description="List of task lists within the schedule")
   
#     **Guidelines:**

#     1. **Adhere to the `Schedule`, `TaskList`, `Task`, and `Subtask` class definitions.**
#     2. **Use UNIX timestamps (seconds since the Unix epoch) for dates.**
#     3. **Provide a well-structured and realistic schedule with multiple lists and tasks.**
#     4. **Include at least one task with subtasks.**

#     **Output:**

#     Generate a JSON string that accurately represents a valid instance of the `Schedule` class based on the provided guidelines.
#         """
#     response = client.chat.completions.create(
#         model="llama3-groq-70b-8192-tool-use-preview",
#         messages=[
#             {"role": "user", "content": template}
#         ],
#         response_model=Schedule
#     )
#     return response

async def generate_schedule(prompt: str) -> Schedule:
    template = f"""
    I'm providing you with an extended Python class definition for a Schedule object. 
    Your task is to generate a JSON string that accurately represents a valid instance of this extended Schedule object, 
    which includes optional fields: 'priority', 'link', and 'depends_on'.

    **User Goal:** 
    {prompt}

    **Schedule Class:**
    (Same code as above, with priority/link/depends_on)

    **Guidelines:**

    1. Use UNIX timestamps (seconds) for any date fields.
    2. Provide a well-structured and realistic schedule with multiple lists, tasks, subtasks. 
    3. Make sure to include detailed descriptions for tasks and subtasks
    4. Demonstrate usage of 'priority', 'link', and 'depends_on' in at least one task or subtask.

    **Output:**
    Generate a JSON string that accurately represents a valid instance of the extended `Schedule` class.
    # Pydantic Models for Schedule
    class Subtask(BaseModel):
        name: str = Field(..., description="Name of the subtask")
        description: Optional[str] = Field(None, description="Details about the subtask")
        start_date: Optional[int] = Field(None, description="Start date in UNIX timestamp")
        due_date: Optional[int] = Field(None, description="Due date in UNIX timestamp")
        priority: Optional[int] = Field(
            None, 
            description="ClickUp priority (0=none, 1=low, 2=normal, 3=high, 4=urgent)"
        )
        link: Optional[str] = Field(
            None, 
            description="Optional reference link or URL."
        )
        depends_on: Optional[List[str]] = Field(
            None, 
            description="List of other tasks/subtasks (by name) this subtask depends on."
        )

    class Task(BaseModel):
        name: str = Field(..., description="Name of the task")
        description: Optional[str] = Field(None, description="Details about the task")
        start_date: Optional[int] = Field(None, description="Start date in UNIX timestamp")
        due_date: Optional[int] = Field(None, description="Due date in UNIX timestamp")
        priority: Optional[int] = Field(
            None, 
            description="ClickUp priority (0=none, 1=low, 2=normal, 3=high, 4=urgent)"
        )
        link: Optional[str] = Field(
            None, 
            description="Optional reference link or URL."
        )
        depends_on: Optional[List[str]] = Field(
            None, 
            description="List of other tasks (by name) this task depends on."
        )
        subtasks: List[Subtask] = Field(default_factory=list, description="List of subtasks")

    class TaskList(BaseModel):
        list_name: str = Field(..., description="Name of the task list")
        tasks: List[Task] = Field(default_factory=list, description="List of tasks in the task list")

    class Schedule(BaseModel):
        schedule_name: str = Field(..., description="Name of the schedule")
        lists: List[TaskList] = Field(default_factory=list, description="Task lists within the schedule")
    """

    response = client.chat.completions.create(
        model= "gpt-4o", #"llama3-groq-70b-8192-tool-use-preview",
        messages=[{"role": "user", "content": template}],
        response_model=Schedule
    )
    print(response)
    return response
