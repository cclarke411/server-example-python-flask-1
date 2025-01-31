##############################################################################
# Extended Pydantic Models + ClickUp Integration Example
##############################################################################

import os
import requests
from pydantic import BaseModel, Field, ValidationError
from typing import List, Optional
from datetime import datetime

# If you use .env files, uncomment these
# from dotenv import load_dotenv
# load_dotenv()

########################################
# 1. Extended Pydantic Models
########################################

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
    subtasks: List[Subtask] = Field(default_factory=list, description="List of subtasks under this task")

class TaskList(BaseModel):
    list_name: str = Field(..., description="Name of the task list")
    tasks: List[Task] = Field(default_factory=list, description="List of tasks in the task list")

class Schedule(BaseModel):
    schedule_name: str = Field(..., description="Name of the schedule")
    lists: List[TaskList] = Field(default_factory=list, description="Task lists within the schedule")


########################################
# 2. ClickUp API Configuration
########################################

API_TOKEN = os.environ.get("CLICKUP_API_KEY", "YOUR_CLICKUP_API_KEY_HERE")
BASE_URL = "https://api.clickup.com/api/v2"

def _make_headers():
    return {
        "Authorization": API_TOKEN,
        "Content-Type": "application/json"
    }


########################################
# 3. ClickUp API Helper Functions
########################################

def get_folders(space_id: str):
    """
    Retrieve all folders for a given space.
    """
    url = f"{BASE_URL}/space/{space_id}/folder"
    response = requests.get(url, headers=_make_headers())
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Error retrieving folders: {response.status_code} - {response.text}")

def create_folder(space_id: str, folder_name: str) -> str:
    """
    Create a new folder within a space and return its ID.
    """
    url = f"{BASE_URL}/space/{space_id}/folder"
    payload = {"name": folder_name}
    response = requests.post(url, json=payload, headers=_make_headers())
    if response.status_code == 200:
        return response.json().get("id")
    else:
        raise Exception(f"Error creating folder '{folder_name}': {response.status_code} - {response.text}")

def create_list(folder_id: str, list_name: str) -> str:
    """
    Create a list within a folder and return its ID.
    """
    url = f"{BASE_URL}/folder/{folder_id}/list"
    payload = {"name": list_name}
    response = requests.post(url, json=payload, headers=_make_headers())
    if response.status_code == 200:
        return response.json().get("id")
    else:
        raise Exception(f"Error creating list '{list_name}': {response.status_code} - {response.text}")

def create_task(
    list_id: str,
    name: str,
    description: Optional[str] = None,
    start_date: Optional[int] = None,
    due_date: Optional[int] = None,
    parent_id: Optional[str] = None,
    priority: Optional[int] = None,
    link: Optional[str] = None
) -> str:
    """
    Create a task or subtask in ClickUp.
    If parent_id is provided, it will create a subtask.
    """
    url = f"{BASE_URL}/list/{list_id}/task"

    # Append link to description if provided
    if link:
        if not description:
            description = f"Reference Link: {link}"
        else:
            description += f"\n\nReference Link: {link}"

    payload = {
        "name": name,
        "description": description or ""
    }

    if start_date is not None:
        payload["start_date"] = str(start_date)
    if due_date is not None:
        payload["due_date"] = str(due_date)
    if parent_id is not None:
        payload["parent"] = parent_id
    if priority is not None:
        payload["priority"] = priority

    # Clean up any None values
    to_remove = [k for k, v in payload.items() if v is None]
    for k in to_remove:
        del payload[k]

    response = requests.post(url, json=payload, headers=_make_headers())
    if response.status_code == 200:
        return response.json().get("id")
    else:
        raise Exception(f"Error creating task '{name}': {response.status_code} - {response.text}")

def set_dependency(task_id: str, depends_on_id: str):
    """
    Make task_id depend on depends_on_id in ClickUp.
    This means task_id cannot be completed unless depends_on_id is finished.
    
    POST /task/{task_id}/dependency
    Payload: {"depends_on": depends_on_id}
    """
    url = f"{BASE_URL}/task/{task_id}/dependency"
    payload = {"depends_on": depends_on_id}
    response = requests.post(url, json=payload, headers=_make_headers())
    if response.status_code != 200:
        raise Exception(
            f"Error setting dependency for task {task_id} on {depends_on_id}: "
            f"{response.status_code} - {response.text}"
        )


########################################
# 4. Transform and Validate LLM Output
########################################

def transform_llm_output(llm_output) -> Schedule:
    """
    Validate the output against the extended Schedule model 
    (with priority/link/depends_on).
    """
    try:
        schedule = Schedule.model_validate(llm_output)
        return schedule
    except ValidationError as e:
        print(f"Validation error: {e}")
        raise ValueError("LLM output does not match the expected format.")


########################################
# 5. Process Schedule
########################################

def process_schedule(space_id: str, schedule: Schedule):
    """
    1. Create a Folder + List for each TaskList.
    2. Create all tasks/subtasks (store name->ID).
    3. In second pass, set dependencies using set_dependency.
    """
    # Retrieve existing folders if needed
    _existing_folders = get_folders(space_id)

    # Dictionary to store ClickUp IDs by 'Task or Subtask name'
    name_to_id_map = {}

    # First Pass: Create Folders, Lists, and Tasks
    for task_list in schedule.lists:
        folder_id = create_folder(space_id, task_list.list_name)
        list_id = create_list(folder_id, task_list.list_name)

        for task in task_list.tasks:
            # Create the main task
            task_id = create_task(
                list_id=list_id,
                name=task.name,
                description=task.description,
                start_date=task.start_date,
                due_date=task.due_date,
                priority=task.priority,
                link=task.link
            )
            name_to_id_map[task.name] = task_id

            # Create subtasks
            for sub in task.subtasks:
                sub_id = create_task(
                    list_id=list_id,
                    name=sub.name,
                    description=sub.description,
                    start_date=sub.start_date,
                    due_date=sub.due_date,
                    priority=sub.priority,
                    link=sub.link,
                    parent_id=task_id
                )
                name_to_id_map[sub.name] = sub_id

    # Second Pass: Set Dependencies
    for task_list in schedule.lists:
        for task in task_list.tasks:
            current_task_id = name_to_id_map[task.name]

            # If this task depends on other tasks
            if task.depends_on:
                for dep_name in task.depends_on:
                    dep_id = name_to_id_map.get(dep_name)
                    if dep_id:
                        set_dependency(current_task_id, dep_id)
                    else:
                        print(f"Warning: dependency '{dep_name}' not found in name_to_id_map")

            # Check subtasks for dependencies
            for sub in task.subtasks:
                current_sub_id = name_to_id_map[sub.name]
                if sub.depends_on:
                    for dep_name in sub.depends_on:
                        dep_id = name_to_id_map.get(dep_name)
                        if dep_id:
                            set_dependency(current_sub_id, dep_id)
                        else:
                            print(f"Warning: dependency '{dep_name}' not found in name_to_id_map")


########################################
# 6. Generate Schedule (Example Stub)
########################################

# If you want to integrate with your LLM chain or instructor client:
# from groq import Groq
# import instructor
#
# client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
# client = instructor.from_groq(client)

def generate_schedule(prompt: str) -> Schedule:
    """
    Example stub for instructing an LLM to produce a schedule 
    with fields (priority/link/depends_on).
    """
    # In a real case, you'd craft a template and call the LLM, e.g.:
    # response = client.chat.completions.create(...)
    # llm_output = response  # JSON from the LLM
    # schedule = transform_llm_output(llm_output)
    # return schedule

    # For now, return a hard-coded example
    example_output = {
        "schedule_name": "Extended House Cleaning & Meal Plan",
        "lists": [
            {
                "list_name": "Monday Tasks",
                "tasks": [
                    {
                        "name": "Morning Routine",
                        "description": "Make bed, quick tidy, check emails",
                        "start_date": 1704069600,  # example Unix TS
                        "due_date": 1704073200,
                        "priority": 2,  # normal
                        "link": "https://example.com/morning-routine",
                        "depends_on": None,
                        "subtasks": [
                            {
                                "name": "Make Bed",
                                "description": "Straighten sheets, fluff pillows",
                                "priority": 1,  # low
                                "link": None,
                                "depends_on": None,
                                "start_date": 1704069600,
                                "due_date": 1704071400
                            }
                        ]
                    }
                ]
            }
        ]
    }

    # Validate & return
    schedule = transform_llm_output(example_output)
    return schedule

##############################################################################
# End of Canvas Code
##############################################################################

# To run:
# 1. Set your CLICKUP_API_KEY in environment variables or in the code.
# 2. Call generate_schedule(...) to get a Schedule object.
# 3. Call process_schedule(space_id, schedule) with a real space ID.
#
# Example:
# schedule_obj = generate_schedule("Create a cleaning schedule with priority, links, dependencies.")
# process_schedule("123456", schedule_obj)
