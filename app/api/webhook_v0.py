from flask import Blueprint, request, jsonify
import json
import logging
from app.functions import get_character_inspiration_tool, get_random_name
from app.rag import pinecone_rag
import json
import asyncio

LOG_FILE_PATH="/Users/clydeclarke/Documents/server-example-python-flask/app/response_data/webhook_logs.txt"
LOG_TOOL_PATH="/Users/clydeclarke/Documents/server-example-python-flask/app/response_data/tool_logs.txt"
webhook = Blueprint('webhook', __name__)
finalize_details_list = []




@webhook.route('/', methods=['POST'])
async def webhook_route():
    try:
        # Parse incoming JSON
        request_data = request.get_json()
        payload = request_data.get('message')

        # Log payload type and keys
        # Log the payload type and keys
        log_entry = (
            f"Payload Type: {payload.get('type')}\n"
            f"Payload Keys: {list(payload.keys())}\n"
            f"Payload Content: {payload}\n"
            f"{'='*50}\n"
        )

        # Save log to a text file
        with open(LOG_FILE_PATH, "a") as log_file:
            log_file.write(log_entry)

        # Process the payload based on its type
        if payload['type'] == "function-call":
            response = await function_call_handler(payload)
            return jsonify(payload), 201
        elif payload['type'] == "tool-calls":
            # logging.info("Tool Call Payload: %s", payload)
            response = await tool_call_handler(payload)
            await process_tool_calls(payload)
            return jsonify(response), 201
        elif payload['type'] == "status-update":
            response = await status_update_handler(payload)
            return jsonify(response), 201
        elif payload['type'] == "conversation-update":
            response = await status_update_handler(payload)
            return jsonify(response), 201
        elif payload['type'] == "assistant-request":
            response = await assistant_request_handler(payload)
            return jsonify(payload), 201
        elif payload['type'] == "end-of-call-report":
            await end_of_call_report_handler(payload)
            return jsonify({}), 201
        elif payload['type'] == "speech-update":
            response = await speech_update_handler(payload)
            return jsonify(response), 201
        elif payload['type'] == "transcript":
            response = await transcript_handler(payload)
            return jsonify(response), 201
        elif payload['type'] == "hang":
            response = await hang_event_handler(payload)
            return jsonify(response), 201
        elif not payload['type']:
            logging.warning("Payload type is missing.")
            pass
        elif payload['type'] == 'model-output':
            response = payload
            return jsonify(response), 201
        else:
            raise ValueError('Unhandled message type')

    except Exception as e:
        logging.error("An error occurred: %s", str(e))
        return jsonify({"error": "An unexpected error occurred."}), 500


# async def tool_call_handler(payload):
#     finalize_details_list = []
#     # # Check `toolCalls`
#     # tool_calls = payload.get("tool-calls", {}).get("toolCalls", [])
#     # print('THIS IS THE TOOL CALLS', tool_calls)
#     # for call in tool_calls:
#     #     function = call.get("function", {})
#     #     if function.get("name") == "finalizeDetails":
#     #         finalize_details_list.append(function)

#     # # Check `toolCallList`
#     # tool_call_list = payload.get("payload", {}).get("toolCallList", [])
#     # for call in tool_call_list:
#     #     function = call.get("function", {})
#     #     if function.get("name") == "finalizeDetails":
#     #         finalize_details_list.append(function)

#     # # Check `toolWithToolCallList`
#     # tool_with_tool_call_list = payload.get("payload", {}).get("toolWithToolCallList", [])
#     # for item in tool_with_tool_call_list:
#     #     function = item.get("function", {})
#     #     if function.get("name") == "finalizeDetails":
#     #         finalize_details_list.append(function)

#     # Check `artifact.messages`
#     artifact_messages = payload.get("artifact", {}).get("messages", [])
#     for message in artifact_messages:
#         tool_calls = message.get("toolCalls", [])
#         for call in tool_calls:
#             function = call.get("function", {})
#             if function.get("name") == "finalizeDetails":
#                 finalize_details_list.append(function)
#                 with open(LOG_TOOL_PATH, "a") as log_file:
#                     log_file.write(finalize_details_list)
#     print('THIS IS THE FINALIZE DETAILS LIST', finalize_details_list)
    # return finalize_details_list


# async def tool_call_handler(payload):

#     # Check `artifact.messages` for finalizeDetails
#     artifact_messages = payload.get("artifact", {}).get("messages", [])
#     for message in artifact_messages:
#         tool_calls = message.get("toolCalls", [])
#         for call in tool_calls:
#             function = call.get("function", {})
#             if function.get("name") == "finalizeDetails":
#                 # Save finalizeDetails to the list and file
#                 finalize_details_list.append(function)
#                 try:
#                     with open("finalize_details_log.txt", "a") as log_file:
#                         # Serialize the last added entry to JSON and save it
#                         log_file.write(json.dumps(finalize_details_list, indent=4) + "\n")
#                 except Exception as e:
#                     print(f"Error writing to file: {e}")

#                 print('THIS IS THE FINALIZE DETAILS LIST', finalize_details_list)
#                 # return  # If finalizeDetails is handled, stop processing
#     # Check `toolCalls` for function calls
#     for call in tool_calls:
#         function = call.get("function", {})
#         toolCallId = call.get("id",{})
#         print(toolCallId)
#         name = function.get("name")
#         if name == "getCharacterInspiration":
#             parameters = function.get('arguments',{})
#             print('THIS IS THE PARAMETERS', parameters)
#             if isinstance(parameters, str):
#                 parameters = json.loads(parameters) 
#             return get_character_inspiration_tool.get_character_inspiration(toolCallId,**parameters)
#         elif name == "getRandomName":
#             return function.get('arguments')
#         elif name == 'getRandomName':
#             # Set parameters and call the respective function
#             params = get_random_name.NameParams(gender="male", nat="US")
#             return get_random_name.get_random_name(params)
#         else:
#             # If no matching function, return None
#             return None


# Dictionary to register tool handlers by name
tool_handlers = {}

# Decorator to register tool handlers
def register_tool_handler(tool_name):
    def decorator(func):
        tool_handlers[tool_name] = func
        return func
    return decorator

# Generalized tool call handler
async def tool_call_handler(payload):
    """
    Generalized handler for processing tool calls in a payload.
    """
    # Extract artifact messages
    artifact_messages = payload.get("artifact", {}).get("messages", [])
    results = []

    for message in artifact_messages:
        tool_calls = message.get("toolCalls", [])
        for call in tool_calls:
            tool_call_id = call.get("id", "")
            function = call.get("function", {})
            tool_name = function.get("name")
            arguments = function.get("arguments", {})

            # Handle stringified arguments
            if isinstance(arguments, str):
                try:
                    arguments = json.loads(arguments)
                except json.JSONDecodeError:
                    print(f"Invalid JSON in arguments for tool {tool_name}: {arguments}")
                    continue

            # Check if a specific handler exists for this tool
            handler = tool_handlers.get(tool_name)
            if handler:
                try:
                    # Call the registered handler
                    result = await handler(tool_call_id, **arguments)
                    results.append(result)
                except Exception as e:
                    print(f"Error handling tool {tool_name}: {e}")
            else:
                print(f"No handler registered for tool {tool_name}")

    return results

# Handlers for specific tools
@register_tool_handler("finalizeDetails")
async def handle_finalize_details(tool_call_id, summary, details):
    """
    Handler for the `finalizeDetails` tool.
    """
    print(f"Handling finalizeDetails with ID: {tool_call_id}")
    print(f"Summary: {summary}")
    print(f"Details: {details}")

    # Custom logic: Save to a file
    try:
        with open("finalize_details_log.txt", "a") as log_file:
            log_file.write(json.dumps({"id": tool_call_id, "summary": summary, "details": details}, indent=4) + "\n")
    except Exception as e:
        print(f"Error writing to file: {e}")

    return {"tool": "finalizeDetails", "status": "processed", "summary": summary, "details": details}


@register_tool_handler("collect_user_info")
async def handle_collect_user_info(tool_call_id, key, value):
    """
    Handler for the `collect_user_info` tool.
    """
    print(f"Collecting user info with ID: {tool_call_id}")
    print(f"Key: {key}, Value: {value}")

    # Custom logic: Save to a database or log
    description = f"Preference for {key} is '{value}'."
    try:
        with open("user_info_log.txt", "a") as log_file:
            log_file.write(json.dumps({"id": tool_call_id, "key": key, "value": value, "description": description}, indent=4) + "\n")
    except Exception as e:
        print(f"Error writing to file: {e}")

    return {"tool": "collect_user_info", "key": key, "value": value, "description": description}


@register_tool_handler("getCharacterInspiration")
async def handle_get_character_inspiration(tool_call_id, theme=None, setting=None, traits=None):
    """
    Handler for the `getCharacterInspiration` tool.
    """
    print(f"Getting character inspiration with ID: {tool_call_id}")
    print(f"Theme: {theme}, Setting: {setting}, Traits: {traits}")

    # Custom logic: Generate mock character inspiration
    inspiration = {
        "theme": theme or "heroic",
        "setting": setting or "medieval fantasy",
        "traits": traits or ["brave", "loyal", "determined"]
    }

    return {"tool": "getCharacterInspiration", "inspiration": inspiration}


# Example General Handler for Undefined Tools
@register_tool_handler("default")
async def handle_default_tool(tool_call_id, **kwargs):
    """
    Fallback handler for undefined tools.
    """
    print(f"Default handler invoked for tool ID: {tool_call_id}")
    print(f"Arguments: {kwargs}")

    return {"tool": "default", "status": "unhandled", "arguments": kwargs}

async def function_call_handler(payload):
    """
    Handle Business logic here.
    You can handle function calls here. The payload will have function name and parameters.
    You can trigger the appropriate function based on your requirements and configurations.
    You can also have a set of validators along with each function which can be used to first validate the parameters and then call the functions.
    Here Assumption is that the functions are handling the fallback cases as well. They should return the appropriate response in case of any error.
    """
    function_call = payload.get('toolCall')
    print("THIS IS THE TOOL CALL",function_call)

    if not function_call:
        raise ValueError("Invalid Request.")
   
    name = function_call.get('name')
    parameters = function_call.get('parameters')

    if name == 'getCharacterInspiration':
        print('THIS IS CHARACTER INSPIRATION',get_character_inspiration_tool.get_character_inspiration(**parameters))
        return get_character_inspiration_tool.get_character_inspiration(**parameters)
    elif name == 'getRandomName':
        params = get_random_name.NameParams(gender="male", nat="US")
        return get_random_name.get_random_name(params)
    else:
        return None

async def status_update_handler(payload):
    """
    Handle Business logic here.
    Sent during a call whenever the status of the call has changed.
    Possible statuses are: "queued","ringing","in-progress","forwarding","ended".
    You can have certain logic or handlers based on the call status.
    You can also store the information in your database. For example whenever the call gets forwarded.
    """
    temp = payload.get("artifact",{}).get("messageOpenAIFormatted",{}).get("messages",{})
    print(temp)
    return {}



async def end_of_call_report_handler(payload):
    """
    Handle Business logic here.
    You can store the information like summary, typescript, recordingUrl or even the full messages list in the database.
    """
    print(payload)
    return payload

async def speech_update_handler(payload):
    """
    Handle Business logic here.
    Sent during a speech status update during the call. It also lets u know who is speaking.
    You can enable this by passing "speech-update" in the serverMessages array while creating the assistant.
    """
    return {}


async def transcript_handler(payload):
    """
    Handle Business logic here.
    Sent during a call whenever the transcript is available for certain chunk in the stream.
    You can store the transcript in your database or have some other business logic.
    """
    return

async def hang_event_handler(payload):
    """
    Handle Business logic here.
    Sent once the call is terminated by user.
    You can update the database or have some followup actions or workflow triggered.
    """
    return 


async def assistant_request_handler(payload):
    """
    Handle Business logic here.
    You can fetch your database to see if there is an existing assistant associated with this call. If yes, return the assistant.
    You can also fetch some params from your database to create the assistant and return it.
    You can have various predefined static assistant here and return them based on the call details.
    """

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

        # Handle stringified arguments
        if isinstance(arguments, str):
            arguments = json.loads(arguments)

        # Initialize category if not already
        if tool_name not in extracted_data:
            extracted_data[tool_name] = []

        # Process tool-specific arguments
        if tool_name == "collect_user_info":
            key = arguments.get("key")
            value = arguments.get("value")
            description = f"Preference for {key} is '{value}'." if key and value else None
            extracted_data[tool_name].append((key, value, description))

        elif tool_name == "finalizeDetails":
            summary = arguments.get("summary")
            details = arguments.get("details")
            extracted_data[tool_name].append((summary, details))

        elif tool_name == "getCharacterInspiration":
            theme = arguments.get("theme")
            setting = arguments.get("setting")
            traits = json.dumps(arguments.get("traits", []))  # Store traits as JSON
            extracted_data[tool_name].append((theme, setting, traits))

    return extracted_data

def store_in_database(data, db_name, table_name, schema):
    """
    Store extracted data into a SQLite database with dynamic table creation.
    """
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    # Create table dynamically based on schema
    cursor.execute(f"CREATE TABLE IF NOT EXISTS {table_name} ({schema})")

    # Generate placeholders for the query
    placeholders = ", ".join("?" for _ in schema.split(","))
    columns = ", ".join(col.split()[0] for col in schema.split(","))

    # Insert data
    cursor.executemany(
        f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})", data
    )

    conn.commit()
    conn.close()

async def process_tool_calls(payload):
    """
    Process tool calls, extract data, and store it in respective databases.
    """
    # Extract data categorized by tool name
    extracted_data = extract_tool_calls(payload)

    # Define database and table mappings
    db_mappings = {
        "collect_user_info": {
            "db": "preferences.db",
            "table": "user_preferences",
            "schema": "id INTEGER PRIMARY KEY AUTOINCREMENT, key TEXT, value TEXT, description TEXT",
        },
        "finalizeDetails": {
            "db": "details.db",
            "table": "finalized_details",
            "schema": "id INTEGER PRIMARY KEY AUTOINCREMENT, summary TEXT, details TEXT",
        },
        "getCharacterInspiration": {
            "db": "characters.db",
            "table": "character_inspirations",
            "schema": "id INTEGER PRIMARY KEY AUTOINCREMENT, theme TEXT, setting TEXT, traits TEXT",
        },
    }

    # Process and store data for each tool type
    for tool_name, data in extracted_data.items():
        if tool_name in db_mappings:
            db_info = db_mappings[tool_name]
            store_in_database(data, db_name=db_info["db"], table_name=db_info["table"], schema=db_info["schema"])
            print(f"Data for '{tool_name}' stored in {db_info['db']} -> {db_info['table']}.")
        else:
            print(f"No database mapping found for tool: {tool_name}")








