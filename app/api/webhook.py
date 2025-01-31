from flask import Blueprint, request, jsonify
import json
import logging
import sqlite3
import os
from pathlib import Path
import asyncio
from app.functions import get_character_inspiration_tool, get_random_name
from app.rag import pinecone_rag
from app.functions.schedule_clickup import generate_schedule, process_schedule, transform_llm_output
from app.functions.get_custom_llm_streaming import generate_user_uuid
import time
from app.vapi_message_handlers.conversation_update import ConversationUpdate
from app.vapi_message_handlers.end_of_call_report import EndOfCallReport
from app.vapi_message_handlers.model_output import ModelOutput
from app.vapi_message_handlers.speech_update import SpeechUpdate
from app.vapi_message_handlers.transcript import Transcript


# Constants
LOG_FILE_PATH = "/Users/clydeclarke/Documents/server-example-python-flask/app/response_data/webhook_logs.txt"
LOG_TOOL_PATH = "/Users/clydeclarke/Documents/server-example-python-flask/app/response_data/tool_logs.txt"
DB_BASE_PATH = "data/databases"

# Pinecone Indexes
pinecone_rag.user_index
pinecone_rag.book_index

# Pinecone Client
pinecone_rag.client

# Initialize Blueprint
webhook = Blueprint('webhook', __name__)
# Dictionary to register tool handlers
tool_handlers = {}

def init_database_directory():
    """
    Initialize the database directory at startup
    """
    Path(DB_BASE_PATH).mkdir(parents=True, exist_ok=True)
def ensure_db_directory(db_path):
    """
    Ensure the directory for the database exists.
    """
    db_dir = os.path.dirname(db_path)
    if db_dir:
        Path(db_dir).mkdir(parents=True, exist_ok=True)
def store_in_database(data, db_name, table_name, schema):
    """
    Store extracted data into a SQLite database with dynamic table creation.
    Handles AUTOINCREMENT columns automatically.
    """
    try:
        ensure_db_directory(db_name)
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()

        try:
            cursor.execute(f"CREATE TABLE IF NOT EXISTS {table_name} ({schema})")
        except sqlite3.OperationalError as e:
            logging.error(f"Error creating table {table_name}: {e}")
            conn.close()
            return False

        if data:
            # Filter out AUTOINCREMENT columns for INSERT
            columns = ", ".join(
                col.split()[0] for col in schema.split(",")
                if "AUTOINCREMENT" not in col.upper()
            )
            placeholders = ", ".join("?" for _ in data[0])

            try:
                cursor.executemany(
                    f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})",
                    data
                )
                conn.commit()
            except sqlite3.Error as e:
                logging.error(f"Error inserting data into {table_name}: {e}")
                conn.rollback()
                conn.close()
                return False

        conn.close()
        return True

    except sqlite3.Error as e:
        logging.error(f"Database error: {e}")
        return False
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        return False

@webhook.route('/', methods=['POST'])
async def webhook_route():
    """
    Main webhook route handler
    """
    try:
        request_data = request.get_json()
        payload = request_data.get('message')

        if not payload:
            return jsonify({"error": "No message in payload"}), 400

        log_entry = (
            f"Payload Type: {payload.get('type')}\n"
            f"Payload Keys: {list(payload.keys())}\n"
            f"Payload Content: {payload}\n"
            f"{'='*50}\n"
        )
        with open(LOG_FILE_PATH, "a") as log_file:
            log_file.write(log_entry)

        handlers = {
            "function-call": function_call_handler,
            "tool-calls": tool_call_handler,
            "status-update": status_update_handler,
            "conversation-update": conversation_update_handler,
            "transcript": transcript_handler,
            "assistant-request": assistant_request_handler,
            "end-of-call-report": end_of_call_report_handler,
            "speech-update": speech_update_handler,
            "hang": hang_event_handler,
            "voice-input": voice_input_handler,
            "model-output": lambda p: p
        }

        payload_type = payload.get('type')
        handler = handlers.get(payload_type)

        if handler:
            import asyncio
            if asyncio.iscoroutinefunction(handler):
                response = await handler(payload)  # ✅ Corrected with await
            else:
                response = handler(payload)  # For sync functions

            if payload_type == "tool-calls":
                await process_tool_calls(payload)
            return jsonify(response), 201
        else:
            logging.warning(f"Unhandled message type: {payload_type}")
            return jsonify({"error": "Unhandled message type"}), 400

    except Exception as e:
        logging.error(f"An error occurred ok: {str(e)}")
        return jsonify({"error": "An unexpected error occurred."}), 500

def register_tool_handler(tool_name):
    """
    Decorator to register tool handlers
    """
    def decorator(func):
        tool_handlers[tool_name] = func
        return func
    return decorator
def extract_tool_calls(payload):
    """
    Extract tool call data from the payload and categorize it by tool type.
    """
    extracted_data = {}
    tool_calls = payload.get("toolCalls", [])
    
    for call in tool_calls:
        function_data = call.get("function", {})
        tool_name = function_data.get("name")
        arguments = function_data.get("arguments", {})

        if isinstance(arguments, str):
            try:
                arguments = json.loads(arguments)
            except json.JSONDecodeError:
                logging.error(f"Invalid JSON in arguments for tool {tool_name}")
                continue

        if tool_name not in extracted_data:
            extracted_data[tool_name] = []

        if tool_name == "collect_user_info":
            key = arguments.get("key")
            value = arguments.get("value")
            description = f"Preference for {key} is '{value}'." if key and value else None
            extracted_data[tool_name].append((key, value, description))

        elif tool_name == "finalizeDetails":
            question = arguments.get("question")
            answer = arguments.get("answer")
            extracted_data[tool_name].append((question, answer))

        elif tool_name == "getCharacterInspiration":
            theme = arguments.get("theme")
            setting = arguments.get("setting")
            traits = json.dumps(arguments.get("traits", []))
            extracted_data[tool_name].append((theme, setting, traits))

        elif tool_name == 'note_taking_tool':
            action = arguments.get('action')
            tags = arguments.get('tags')
            priority=arguments.get('priority')
            note_content = arguments.get('note_content')
            context_window= arguments.get('context_window')
            extracted_data[tool_name].append((action, tags, priority, note_content, context_window))


    return extracted_data
async def tool_call_handler(payload):
    """
    Generalized handler for processing tool calls in a payload.
    """
    artifact_messages = payload.get("artifact", {}).get("messages", [])
    results = []

    for message in artifact_messages:
        tool_calls = message.get("toolCalls", [])
        for call in tool_calls:
            tool_call_id = call.get("id", "")
            function = call.get("function", {})
            tool_name = function.get("name")
            arguments = function.get("arguments", {})

            # Parse arguments if provided as a string
            if isinstance(arguments, str):
                try:
                    arguments = json.loads(arguments)
                except json.JSONDecodeError:
                    logging.error(f"Invalid JSON in arguments for tool {tool_name}")
                    continue

            handler = tool_handlers.get(tool_name)

            # ✅ Fixed async handling check
            if handler:
                import asyncio
                if asyncio.iscoroutinefunction(handler):
                    result = await handler(tool_call_id, **arguments)
                else:
                    result = handler(tool_call_id, **arguments)
                results.append(result)
            else:
                logging.warning(f"No handler registered for tool {tool_name}")

    return results
async def process_tool_calls(payload):
    """
    Process tool calls, extract data, and store it in respective databases.
    """
    extracted_data = extract_tool_calls(payload)

    db_mappings = {
        "collect_user_info": {
            "db": f"{DB_BASE_PATH}/preferences.db",
            "table": "user_preferences",
            "schema": "id INTEGER PRIMARY KEY AUTOINCREMENT, key TEXT, value TEXT, description TEXT",
        },
        "finalizeDetails": {
            "db": f"{DB_BASE_PATH}/details.db",
            "table": "finalized_details",
            "schema": "id INTEGER PRIMARY KEY AUTOINCREMENT, summary TEXT, details TEXT",
        },
        "getCharacterInspiration": {
            "db": f"{DB_BASE_PATH}/characters.db",
            "table": "character_inspirations",
            "schema": "id INTEGER PRIMARY KEY AUTOINCREMENT, theme TEXT, setting TEXT, traits TEXT",
        },
    }

    for tool_name, data in extracted_data.items():
        if tool_name in db_mappings:
            db_info = db_mappings[tool_name]
            success = store_in_database(
                data,
                db_name=db_info["db"],
                table_name=db_info["table"],
                schema=db_info["schema"]
            )
            if success:
                logging.info(f"Data for '{tool_name}' successfully stored in {db_info['db']} -> {db_info['table']}.")
            else:
                logging.error(f"Failed to store data for '{tool_name}' in {db_info['db']}.")
        else:
            logging.warning(f"No database mapping found for tool: {tool_name}")

## Tool Handlers
@register_tool_handler("finalizeDetails")
async def handle_finalize_details(tool_call_id, question, answer):
    """Handler for the finalizeDetails tool."""
    try:
        with open("finalize_details_log.txt", "a") as log_file:
            log_file.write(json.dumps({
                "id": tool_call_id,
                "question": question,
                "answer": answer
            }, indent=4) + "\n")
    except Exception as e:
        logging.error(f"Error writing to file: {e}")

    return {
        "tool": "finalizeDetails",
        "status": "processed",
        "summary": question,
        "details": answer
    }

# Register the new tool handler for collect_user_info
@register_tool_handler("collect_user_info")
async def handle_collect_user_info(tool_call_id, key, value):
    """Handler for the collect_user_info tool."""
    description = f"Preference for {key} is '{value}'."
    try:
        with open("user_info_log.txt", "a") as log_file:
            log_file.write(json.dumps({
                "id": tool_call_id,
                "key": key,
                "value": value,
                "description": description
            }, indent=4) + "\n")
    except Exception as e:
        logging.error(f"Error writing to file: {e}")

    return {
        "tool": "collect_user_info",
        "key": key,
        "value": value,
        "description": description
    }

# Register the new tool handler for getCharacterInspiration
@register_tool_handler("getCharacterInspiration")
async def handle_get_character_inspiration(tool_call_id, theme=None, setting=None, traits=None):
    """Handler for the getCharacterInspiration tool."""
    inspiration = {
        "theme": theme or "heroic",
        "setting": setting or "medieval fantasy",
        "traits": traits or ["brave", "loyal", "determined"]
    }
    return {
        "tool": "getCharacterInspiration",
        "inspiration": inspiration
    }

# Register the new tool handler for schedule_clickup
@register_tool_handler("schedule_clickup")
async def handle_schedule_clickup(tool_call_id, goal,timeline,resources, space_id=90112974722):
    """
    Handler for schedule_clickup tool.
    Generates a schedule using an LLM and integrates it with ClickUp.
    """
    try:
        # Log the received request
        # logging.info(f"Processing schedule_clickup tool call: {tool_call_id}, prompt: {goal}")
        prompt = goal + timeline + resources
        # Generate the schedule
        raw_schedule = await generate_schedule(prompt)
        validated_schedule = transform_llm_output(raw_schedule)

        # Process the schedule and integrate with ClickUp
        await process_schedule(space_id=space_id, schedule=validated_schedule)

        return {
            "tool": "schedule_clickup",
            "status": "success",
            "schedule_name": validated_schedule.schedule_name,
            "message": f"Schedule '{validated_schedule.schedule_name}' successfully created in ClickUp."
        }
    except Exception as e:
        logging.error(f"Error in handle_schedule_clickup: {e}")
        return {
            "tool": "schedule_clickup",
            "status": "error",
            "message": str(e)
        }

# Other handlers remain the same
async def function_call_handler(payload):
    """Handle function calls."""
    function_call = payload.get('toolCall')
    if not function_call:
        raise ValueError("Invalid Request.")
    
    name = function_call.get('name')
    parameters = function_call.get('parameters')

    if name == 'getCharacterInspiration':
        return get_character_inspiration_tool.get_character_inspiration(**parameters)
    elif name == 'getRandomName':
        params = get_random_name.NameParams(gender="male", nat="US")
        return get_random_name.get_random_name(params)
    return None

async def status_update_handler(payload):
    """Handle status updates."""
    return {}

async def voice_input_handler(payload):
    """Handle voice-input calls."""
    return {}

async def status_update_handler(payload):
    """Handle status updates."""
    return {}

async def end_of_call_report_handler(payload):
    """Handle end of call reports."""
    # logging.info(f"End of call report received: {payload}")
    # summarization = pinecone_rag.summarize_conversation(payload)
    # summary_embedding = pinecone_rag.get_embedding(summarization)
    # # print(summarization)

    user_id = payload.get('assistant',[]).get('metadata',[]).get('user_id',[])
    summarization = payload.get('summary')
    # summary_embedding = pinecone_rag.get_embedding(summarization)
    print(summarization)
    # idv = "id" + str(time.time())
    # pinecone_rag.user_index.upsert(vectors=[{"id": idv, 
    #                                "values": summary_embedding, 
    #                                "metadata": {'text': summarization, 'user_id': user_id}}],
    #                                namespace='user-data-openai-embedding')
    return [summarization]    

async def speech_update_handler(payload):
    """Handle speech updates."""
    return {}

async def transcript_handler(payload):
    """Handle transcripts."""
    return {}

async def hang_event_handler(payload):
    """Handle hang events."""
    return {}

async def assistant_request_handler(payload):
    """Handle assistant requests."""
    if payload and 'call' in payload:
        assistant = {
            'name': 'Paula',
            'model': {
                'provider': 'openai',
                'model': 'gpt-3.5-turbo',
                'temperature': 0.7,
                'systemPrompt': "You're Paula, an AI assistant who can help user draft beautiful emails to their clients based on the user requirements. Then Call sendEmail function to actually send the email.",
                'functions': [
                    {
                        'name': 'sendEmail',
                        'description': 'Send email to the given email address and with the given content.',
                        'parameters': {
                            'type': 'object',
                            'properties': {
                                'email': {
                                    'type': 'string',
                                    'description': 'Email to which we want to send the content.'
                                },
                                'content': {
                                    'type': 'string',
                                    'description': 'Actual Content of the email to be sent.'
                                }
                            },
                            'required': ['email']
                        }
                    }
                ]
            },
            'voice': {
                'provider': '11labs',
                'voiceId': 'paula'
            },
            'firstMessage': "Hi, I'm Paula, your personal email assistant."
        }
        return {'assistant': assistant}

    raise ValueError('Invalid call details provided.')

# Initialize database directory when the module loads
init_database_directory()