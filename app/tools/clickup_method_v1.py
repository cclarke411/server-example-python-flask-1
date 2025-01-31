"""
Complete LLM + ClickUp Integration Script

Requirements:
- pip install requests pydantic instructor groq python-dotenv

Steps:
1. Set environment variables:
   - CLICKUP_API_KEY (your personal ClickUp API token)
   - GROQ_API_KEY (for your Groq/instructor LLM usage)
   - Optional: Create a .env file or define in OS environment

2. Update or pass your actual ClickUp 'space_id'.

3. Run this script (e.g., python this_file.py).

This script:
- Defines extended Pydantic models for a Schedule (with priority, link, depends_on).
- Contains a function to call an LLM using Groq + instructor,
  parse the LLM’s JSON output into a Schedule object.
- Provides functions to create folders/lists/tasks in ClickUp,
  and a process_schedule function to build out the entire schedule in ClickUp.
"""

import os
import json
import requests
from pydantic import BaseModel, Field, ValidationError
from typing import List, Optional

# LLM / Instructor imports
# pip install instructor groq
from groq import Groq
import instructor

##############################################################################
# 1. Extended Pydantic Models
##############################################################################

class Subtask(BaseModel):
    """
    A subtask within a task, with optional priority, link, and depends_on.
    """
    name: str = Field(..., description="Name of the subtask")
    description: Optional[str] = Field(None, description="Details about the subtask")
    start_date: Optional[int] = Field(None, description="Start date in UNIX timestamp (seconds)")
    due_date: Optional[int] = Field(None, description="Due date in UNIX timestamp (seconds)")
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
    """
    A task that can contain multiple subtasks, with optional priority, link, and depends_on.
    """
    name: str = Field(..., description="Name of the task")
    description: Optional[str] = Field(None, description="Details about the task")
    start_date: Optional[int] = Field(None, description="Start date in UNIX timestamp (seconds)")
    due_date: Optional[int] = Field(None, description="Due date in UNIX timestamp (seconds)")
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
    subtasks: List[Subtask] = Field(
        default_factory=list,
        description="List of subtasks under this task"
    )

class TaskList(BaseModel):
    """
    A list of tasks (e.g., a daily or weekly grouping).
    """
    list_name: str = Field(..., description="Name of the task list")
    tasks: List[Task] = Field(
        default_factory=list,
        description="List of tasks in this task list"
    )

class Schedule(BaseModel):
    """
    The top-level schedule containing one or more TaskLists.
    """
    schedule_name: str = Field(..., description="Name of the schedule")
    lists: List[TaskList] = Field(
        default_factory=list,
        description="Task lists within the schedule"
    )

##############################################################################
# 2. LLM -> JSON -> Pydantic (Generating a Schedule from a Prompt)
##############################################################################

def generate_schedule_from_prompt(prompt: str) -> Schedule:
    """
    1. Build a 'template' (system message or user message) prompting the LLM
       to produce a valid JSON for our extended Schedule model.
    2. Call the LLM using Groq + instructor.
    3. Parse the JSON string from the LLM, validate it into a Schedule object.
    4. Return the validated Schedule.
    """
    template = f"""
You are a helpful assistant that generates a JSON representation of a 'Schedule' object.
The 'Schedule' object includes:

- schedule_name (str)
- lists (list of 'TaskList')

Each 'TaskList' has:
- list_name (str)
- tasks (list of 'Task')

Each 'Task' includes:
- name (str)
- description (optional str)
- start_date (optional int, UNIX timestamp in seconds)
- due_date (optional int, UNIX timestamp in seconds)
- priority (optional int: 0=none,1=low,2=normal,3=high,4=urgent)
- link (optional str)
- depends_on (optional list of strings referencing other tasks by name)
- subtasks (list of 'Subtask')

Each 'Subtask' includes the same date/priority/link/depends_on fields, just with 'name' and 'description'.

User's Prompt: {prompt}

Output: A *valid JSON* that can be parsed into a 'Schedule' object using Pydantic.
    """

    # Prepare the LLM client
    llm_api_key = os.environ.get("GROQ_API_KEY")
    if not llm_api_key:
        raise EnvironmentError("Missing GROQ_API_KEY environment variable.")
    groq_client = Groq(api_key=llm_api_key)
    llm_client = instructor.from_groq(groq_client)

    # 1. Make request to LLM
    response = llm_client.chat.completions.create(
        model="llama3-groq-70b-8192-tool-use-preview",
        messages=[{"role": "user", "content": template}],
        response_model=Schedule
        # Not using response_model=Schedule here; we'll parse the raw JSON ourselves.
    )
    # response = response.model_json_schema(mode="json")
    print(response.model_dump())
    print(type(response.model_json_schema()))
    # 2. Extract the raw JSON string from LLM response
    llm_output_str = response.model_dump_json()

    # 3. Parse the string as JSON
    try:
        llm_output_dict = json.loads(llm_output_str)
    except json.JSONDecodeError as e:
        raise ValueError(f"LLM did not return valid JSON. Error: {e}")

    # 4. Validate the dictionary against the Pydantic model
    try:
        schedule = Schedule.model_validate(llm_output_dict)
    except ValidationError as e:
        raise ValueError(f"Generated JSON does not conform to the Schedule model. Error: {e}")

    return schedule

##############################################################################
# 3. ClickUp API Config and Helper Functions
##############################################################################

CLICKUP_API_KEY = os.environ.get("CLICKUP_API_KEY", "pk_120072344_2DN7VGSUJX3IBQN8AI6I0NZGP3YP5QNI")
BASE_URL = "https://api.clickup.com/api/v2"

def _headers():
    return {
        "Authorization": CLICKUP_API_KEY,
        "Content-Type": "application/json"
    }

def get_folders(space_id: str):
    """
    Retrieve all folders for a given space.
    """
    url = f"{BASE_URL}/space/{space_id}/folder"
    resp = requests.get(url, headers=_headers())
    if resp.status_code == 200:
        return resp.json()
    else:
        raise Exception(f"Error retrieving folders: {resp.status_code} - {resp.text}")

def create_folder(space_id: str, folder_name: str) -> str:
    """
    Create a new folder within a space and return its ID.
    """
    url = f"{BASE_URL}/space/{space_id}/folder"
    payload = {"name": folder_name}
    resp = requests.post(url, json=payload, headers=_headers())
    if resp.status_code == 200:
        return resp.json().get("id")
    else:
        raise Exception(f"Error creating folder '{folder_name}': {resp.status_code} - {resp.text}")

def create_list(folder_id: str, list_name: str) -> str:
    """
    Create a list within a folder and return its ID.
    """
    url = f"{BASE_URL}/folder/{folder_id}/list"
    payload = {"name": list_name}
    resp = requests.post(url, json=payload, headers=_headers())
    if resp.status_code == 200:
        return resp.json().get("id")
    else:
        raise Exception(f"Error creating list '{list_name}': {resp.status_code} - {resp.text}")

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
    If parent_id is provided, it will create a subtask (task with 'parent').
    """
    url = f"{BASE_URL}/list/{list_id}/task"

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
        # ClickUp expects a string of milliseconds, but your data may be in seconds
        # If your timestamps are in seconds, multiply by 1000
        payload["start_date"] = str(start_date * 1000)
    if due_date is not None:
        payload["due_date"] = str(due_date * 1000)
    if parent_id:
        payload["parent"] = parent_id
    if priority is not None:
        payload["priority"] = priority

    # Remove any Nones
    for k in list(payload.keys()):
        if payload[k] is None:
            del payload[k]

    resp = requests.post(url, json=payload, headers=_headers())
    if resp.status_code == 200:
        return resp.json().get("id")
    else:
        raise Exception(f"Error creating task '{name}': {resp.status_code} - {resp.text}")

def set_dependency(task_id: str, depends_on_id: str):
    """
    Make 'task_id' depend on 'depends_on_id' in ClickUp.
    i.e., 'task_id' cannot be completed unless 'depends_on_id' is finished.
    
    POST /task/{task_id}/dependency
    with {"depends_on": depends_on_id}
    """
    url = f"{BASE_URL}/task/{task_id}/dependency"
    payload = {"depends_on": depends_on_id}
    resp = requests.post(url, json=payload, headers=_headers())
    if resp.status_code != 200:
        raise Exception(
            f"Error setting dependency for task {task_id} on {depends_on_id}: "
            f"{resp.status_code} - {resp.text}"
        )

##############################################################################
# 4. process_schedule: Create Folders/Lists/Tasks in ClickUp
##############################################################################

# def process_schedule(space_id: str, schedule: Schedule):
    """
    Given a validated 'Schedule' object, create the structure in ClickUp:
      1) For each TaskList, create a Folder and a List
      2) Create each Task + Subtask
      3) In a second pass, set dependencies
    """

    # Optionally get existing folders to check for duplicates
    _existing_folders = get_folders(space_id)

    # A map to store the created tasks' IDs by their name
    name_to_id_map = {}

    # First pass: Create Folders, Lists, and their tasks
    for tl in schedule.lists:
        folder_id = create_folder(space_id, tl.list_name)
        list_id = create_list(folder_id, tl.list_name)

        for task in tl.tasks:
            # Create main task
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

    # Second pass: Set dependencies
    for tl in schedule.lists:
        for task in tl.tasks:
            current_task_id = name_to_id_map[task.name]
            if task.depends_on:
                for dep_name in task.depends_on:
                    if dep_name in name_to_id_map:
                        set_dependency(current_task_id, name_to_id_map[dep_name])
                    else:
                        print(f"Warning: No ID found for dependency '{dep_name}'")

            # Subtasks
            for sub in task.subtasks:
                current_sub_id = name_to_id_map[sub.name]
                if sub.depends_on:
                    for dep_name in sub.depends_on:
                        if dep_name in name_to_id_map:
                            set_dependency(current_sub_id, name_to_id_map[dep_name])
                        else:
                            print(f"Warning: No ID found for dependency '{dep_name}'")

def process_schedule(space_id: str, schedule: Schedule):
    """
    Revised approach to create exactly ONE folder named after the schedule,
    and multiple lists under that folder.

    Folder => schedule.schedule_name
    ├── List 1 => schedule.lists[0].list_name
    │   └── Tasks & Subtasks
    ├── List 2 => schedule.lists[1].list_name
    │   └── Tasks & Subtasks
    └── ...
    """

    # 1. Create ONE folder using schedule.schedule_name
    folder_id = create_folder(space_id, schedule.schedule_name)

    # 2. Prepare a map to store created tasks by name -> ClickUp Task ID
    name_to_id_map = {}

    # 3. Create each TaskList *as a separate list* under that one folder
    for task_list in schedule.lists:
        # Create a List under the single Folder
        list_id = create_list(folder_id, task_list.list_name)

        # For each Task in this TaskList, create a Task in the newly created List
        for task in task_list.tasks:
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

            # For each Subtask in this Task, create a subtask with parent=task_id
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

    # 4. Second Pass: Set dependencies (if you're using depends_on fields)
    for task_list in schedule.lists:
        for task in task_list.tasks:
            current_task_id = name_to_id_map[task.name]
            if task.depends_on:
                for dep_name in task.depends_on:
                    dep_id = name_to_id_map.get(dep_name)
                    if dep_id:
                        set_dependency(current_task_id, dep_id)
                    else:
                        print(f"Warning: No ID found for dependency '{dep_name}'")

            # Subtasks
            for sub in task.subtasks:
                current_sub_id = name_to_id_map[sub.name]
                if sub.depends_on:
                    for dep_name in sub.depends_on:
                        dep_id = name_to_id_map.get(dep_name)
                        if dep_id:
                            set_dependency(current_sub_id, dep_id)
                        else:
                            print(f"Warning: No ID found for dependency '{dep_name}'")


##############################################################################
# 5. Example Usage (Main Function)
##############################################################################

if __name__ == "__main__":
    # Example usage:
    # 1. Provide a 'prompt' for the LLM to generate a schedule
    user_prompt = "Create a weekly cleaning and meal schedule that harmonizes the order and efficiency of household management. Be as detailed as possible."

    # 2. Generate the schedule from the LLM
    print("Generating schedule from the LLM...")
    generated_schedule = generate_schedule_from_prompt(user_prompt)
    print("\nGenerated Schedule (parsed via Pydantic):")
    print(generated_schedule.model_dump_json(indent=2))

    # 3. Provide your ClickUp space ID
    space_id = 90112974722

    # 4. Process the schedule in ClickUp
    #    (Creates folders, lists, tasks, subtasks, sets dependencies)
    print("\nCreating schedule in ClickUp...")
    process_schedule(space_id, generated_schedule)
    print("Done!")
