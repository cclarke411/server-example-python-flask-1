import json
import asyncio

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

# Example Usage
if __name__ == "__main__":
    # Sample payload
    payload = {
        "artifact": {
            "messages": [
                {
                    "toolCalls": [
                        {
                            "id": "call_123",
                            "type": "function",
                            "function": {
                                "name": "collect_user_info",
                                "arguments": {
                                    "key": "book_preference",
                                    "value": "Dune by Frank Herbert"
                                }
                            }
                        },
                        {
                            "id": "call_456",
                            "type": "function",
                            "function": {
                                "name": "finalizeDetails",
                                "arguments": {
                                    "summary": "User likes sci-fi books.",
                                    "details": "Dune is a classic sci-fi book."
                                }
                            }
                        },
                        {
                            "id": "call_789",
                            "type": "function",
                            "function": {
                                "name": "getCharacterInspiration",
                                "arguments": {
                                    "theme": "adventure",
                                    "setting": "desert",
                                    "traits": ["resourceful", "cunning"]
                                }
                            }
                        }
                    ]
                }
            ]
        }
    }
    payload1 = {'timestamp': 1734990578879, 'type': 'tool-calls', 'toolCalls': [{'id': 'call_kwm0', 'type': 'function', 'function': {'name': 'collect_user_info', 'arguments': {'key': 'book_preference', 'value': 'Dune by Frank Herbert'}}}], 'toolCallList': [{'id': 'call_kwm0', 'type': 'function', 'function': {'name': 'collect_user_info', 'arguments': {'key': 'book_preference', 'value': 'Dune by Frank Herbert'}}}], 'toolWithToolCallList': [{'type': 'function', 'function': {'name': 'collect_user_info', 'async': False, 'parameters': {'type': 'object', 'required': ['key', 'value'], 'properties': {'key': {'type': 'string', 'description': "The category or type of personal information provided by the user (e.g., 'username', 'preference', 'email', etc.)."}, 'value': {'type': 'string', 'description': '"The actual information provided by the user (e.g., \'John Doe\', \'likes pizza\', \'john.doe@example.com\')."'}}}, 'description': 'Collects key-value pair information when a user volunteers personal or preference data.'}, 'async': True, 'server': {'url': 'https://mako-ace-sadly.ngrok-free.app/api/webhook/'}, 'messages': [], 'toolCall': {'id': 'call_kwm0', 'type': 'function', 'function': {'name': 'collect_user_info', 'arguments': {'key': 'book_preference', 'value': 'Dune by Frank Herbert'}}}}], 'artifact': {'messages': [{'role': 'system', 'message': 'Just say hi and have a conversation with the user', 'time': 1734990505012, 'secondsFromStart': 0}, {'role': 'bot', 'message': 'Hello.', 'time': 1734990506402, 'endTime': 1734990506902, 'secondsFromStart': 1.12, 'duration': 500, 'source': ''}, {'role': 'user', 'message': 'Hi.', 'time': 1734990508002, 'endTime': 1734990508502, 'secondsFromStart': 2.72, 'duration': 500}, {'role': 'bot', 'message': 'How can I assist you today?', 'time': 1734990509162, 'endTime': 1734990510772, 'secondsFromStart': 3.88, 'duration': 1610, 'source': ''}, {'role': 'user', 'message': 'Uh, I like ice cream.', 'time': 1734990512542, 'endTime': 1734990513972, 'secondsFromStart': 7.26, 'duration': 1430}, {'role': 'bot', 'message': 'Ice cream sounds delicious. Do you have a favorite flavor?', 'time': 1734990514832, 'endTime': 1734990518122, 'secondsFromStart': 9.55, 'duration': 2920, 'source': ''}, {'role': 'user', 'message': 'No.', 'time': 1734990519432.001, 'endTime': 1734990519932.001, 'secondsFromStart': 14.150001, 'duration': 500}, {'role': 'bot', 'message': "If you're looking to try something new, I can recommend a few unique flavors. Would you like some suggestions?", 'time': 1734990520962, 'endTime': 1734990526401.999, 'secondsFromStart': 15.68, 'duration': 5019.9990234375, 'source': ''}, {'role': 'user', 'message': 'Uh, I like to eat, uh, peanuts.', 'time': 1734990528932, 'endTime': 1734990531832, 'secondsFromStart': 23.65, 'duration': 2900}, {'role': 'bot', 'message': 'Peanuts are a great choice. Do you prefer them in a specific dish or just as a snack?', 'time': 1734990533141.999, 'endTime': 1734990537562, 'secondsFromStart': 27.859999, 'duration': 4420.0009765625, 'source': ''}, {'role': 'user', 'message': 'Uh, just as a snack,', 'time': 1734990540562, 'endTime': 1734990542021.998, 'secondsFromStart': 35.28, 'duration': 1459.998046875}, {'toolCalls': [{'id': 'call_2c8w', 'type': 'function', 'function': {'name': 'collect_user_info', 'arguments': '{"key": "flavor_preference", "value": "ice cream"}'}}, {'id': 'call_kecg', 'type': 'function', 'function': {'name': 'collect_user_info', 'arguments': '{"key": "snack_preference", "value": "peanuts"}'}}], 'role': 'tool_calls', 'message': '', 'time': 1734990545636, 'secondsFromStart': 37.73}, {'role': 'tool_call_result', 'time': 1734990545640, 'secondsFromStart': 37.734, 'name': 'collect_user_info', 'result': 'Success.', 'toolCallId': 'call_2c8w'}, {'role': 'tool_call_result', 'time': 1734990545640, 'secondsFromStart': 37.734, 'name': 'collect_user_info', 'result': 'Success.', 'toolCallId': 'call_kecg'}, {'role': 'bot', 'message': "I've noted your preferences for ice cream and peanut as a snack. Is there anything else you'd like to share or any other way I can assist you?", 'time': 1734990546162, 'endTime': 1734990553132, 'secondsFromStart': 40.88, 'duration': 6710.0029296875, 'source': ''}, {'role': 'user', 'message': 'Oh, Um, I like', 'time': 1734990555522, 'endTime': 1734990558712, 'secondsFromStart': 50.24, 'duration': 1450}, {'role': 'bot', 'message': "If you're", 'time': 1734990557911.997, 'endTime': 1734990558562, 'secondsFromStart': 52.629997, 'duration': 650.0029296875, 'source': ''}, {'role': 'user', 'message': 'I like to read books.', 'time': 1734990559512, 'endTime': 1734990561052, 'secondsFromStart': 54.23, 'duration': 1540}, {'role': 'bot', 'message': 'What genre of books do you prefer reading?', 'time': 1734990561982, 'endTime': 1734990564082, 'secondsFromStart': 56.7, 'duration': 2100, 'source': ''}, {'role': 'user', 'message': 'Science fiction.', 'time': 1734990566412, 'endTime': 1734990567212, 'secondsFromStart': 61.13, 'duration': 800}, {'role': 'bot', 'message': 'Science fiction is a fascinating genre. Do you have a favorite author or book?', 'time': 1734990567762, 'endTime': 1734990572112, 'secondsFromStart': 62.48, 'duration': 4020.00390625, 'source': ''}, {'role': 'user', 'message': 'Uh, I like Dune by Frank Herbert.', 'time': 1734990574342, 'endTime': 1734990576602, 'secondsFromStart': 69.06, 'duration': 2260}, {'toolCalls': [{'id': 'call_kwm0', 'type': 'function', 'function': {'name': 'collect_user_info', 'arguments': '{\n  "key": "book_preference",\n  "value": "Dune by Frank Herbert"\n}'}}], 'role': 'tool_calls', 'message': '', 'time': 1734990578878, 'secondsFromStart': 70.972}], 'messagesOpenAIFormatted': [{'role': 'system', 'content': 'Just say hi and have a conversation with the user'}, {'role': 'assistant', 'content': 'Hello.'}, {'role': 'user', 'content': 'Hi.'}, {'role': 'assistant', 'content': 'How can I assist you today?'}, {'role': 'user', 'content': 'Uh, I like ice cream.'}, {'role': 'assistant', 'content': 'Ice cream sounds delicious. Do you have a favorite flavor?'}, {'role': 'user', 'content': 'No.'}, {'role': 'assistant', 'content': "If you're looking to try something new, I can recommend a few unique flavors. Would you like some suggestions?"}, {'role': 'user', 'content': 'Uh, I like to eat, uh, peanuts.'}, {'role': 'assistant', 'content': 'Peanuts are a great choice. Do you prefer them in a specific dish or just as a snack?'}, {'role': 'user', 'content': 'Uh, just as a snack,'}, {'role': 'assistant', 'tool_calls': [{'id': 'call_2c8w', 'type': 'function', 'function': {'name': 'collect_user_info', 'arguments': '{"key": "flavor_preference", "value": "ice cream"}'}}, {'id': 'call_kecg', 'type': 'function', 'function': {'name': 'collect_user_info', 'arguments': '{"key": "snack_preference", "value": "peanuts"}'}}]}, {'role': 'tool', 'tool_call_id': 'call_2c8w', 'content': 'Success.'}, {'role': 'tool', 'tool_call_id': 'call_kecg', 'content': 'Success.'}, {'role': 'assistant', 'content': "I've noted your preferences for ice cream and peanut as a snack. Is there anything else you'd like to share or any other way I can assist you?"}, {'role': 'user', 'content': 'Oh, Um, I like'}, {'role': 'assistant', 'content': "If you're"}, {'role': 'user', 'content': 'I like to read books.'}, {'role': 'assistant', 'content': 'What genre of books do you prefer reading?'}, {'role': 'user', 'content': 'Science fiction.'}, {'role': 'assistant', 'content': 'Science fiction is a fascinating genre. Do you have a favorite author or book?'}, {'role': 'user', 'content': 'Uh, I like Dune by Frank Herbert.'}, {'role': 'assistant', 'tool_calls': [{'id': 'call_kwm0', 'type': 'function', 'function': {'name': 'collect_user_info', 'arguments': '{\n  "key": "book_preference",\n  "value": "Dune by Frank Herbert"\n}'}}]}, {'role': 'tool', 'tool_call_id': 'call_kwm0', 'content': 'Tool Result Still Pending But Proceed Further If Possible.'}]}, 'call': {'id': 'ac8bcf59-3cd1-428f-8409-a4f5f5cdfe74', 'orgId': 'bf389f00-a6ab-4e59-b031-fb09510545d1', 'createdAt': '2024-12-23T21:48:24.618Z', 'updatedAt': '2024-12-23T21:48:24.618Z', 'type': 'webCall', 'monitor': {'listenUrl': 'wss://phone-call-websocket.aws-us-west-2-backend-production2.vapi.ai/ac8bcf59-3cd1-428f-8409-a4f5f5cdfe74/listen', 'controlUrl': 'https://phone-call-websocket.aws-us-west-2-backend-production2.vapi.ai/ac8bcf59-3cd1-428f-8409-a4f5f5cdfe74/control'}, 'transport': {'assistantVideoEnabled': False}, 'webCallUrl': 'https://vapi.daily.co/eaD5Q8PA5LUWR0N6yRGd', 'status': 'queued', 'assistant': {'name': 'Groq Custom LLM Webhook', 'model': {'model': 'gpt-3.5-turbo', 'temperature': 0.7, 'messages': [{'content': 'Just say hi and have a conversation with the user', 'role': 'system'}], 'toolIds': ['14b85a80-946c-4f66-a123-b2b557a6b7af'], 'provider': 'custom-llm', 'url': 'https://mako-ace-sadly.ngrok-free.app/api/custom-llm/'}, 'voice': {'voiceId': '248be419-c632-4f23-adf1-5324ed7dbf1d', 'provider': 'cartesia', 'fillerInjectionEnabled': False}, 'firstMessage': 'Hello', 'clientMessages': ['transcript', 'hang', 'function-call', 'speech-update', 'metadata', 'transfer-update', 'conversation-update'], 'serverMessages': ['end-of-call-report', 'status-update', 'hang', 'function-call'], 'serverUrl': 'https://mako-ace-sadly.ngrok-free.app/api/webhook/', 'backchannelingEnabled': False, 'backgroundDenoisingEnabled': False}, 'assistantOverrides': {'clientMessages': ['transfer-update', 'transcript']}}, 'assistant': {'name': 'Groq Custom LLM Webhook', 'model': {'model': 'gpt-3.5-turbo', 'temperature': 0.7, 'messages': [{'content': 'Just say hi and have a conversation with the user', 'role': 'system'}], 'toolIds': ['14b85a80-946c-4f66-a123-b2b557a6b7af'], 'provider': 'custom-llm', 'url': 'https://mako-ace-sadly.ngrok-free.app/api/custom-llm/', 'tools': [{'id': '14b85a80-946c-4f66-a123-b2b557a6b7af', 'createdAt': '2024-12-23T20:19:15.305Z', 'updatedAt': '2024-12-23T21:33:33.747Z', 'type': 'function', 'function': {'name': 'collect_user_info', 'async': False, 'parameters': {'type': 'object', 'required': ['key', 'value'], 'properties': {'key': {'type': 'string', 'description': "The category or type of personal information provided by the user (e.g., 'username', 'preference', 'email', etc.)."}, 'value': {'type': 'string', 'description': '"The actual information provided by the user (e.g., \'John Doe\', \'likes pizza\', \'john.doe@example.com\')."'}}}, 'description': 'Collects key-value pair information when a user volunteers personal or preference data.'}, 'orgId': 'bf389f00-a6ab-4e59-b031-fb09510545d1', 'server': {'url': 'https://mako-ace-sadly.ngrok-free.app/api/webhook/'}, 'async': True}]}, 'voice': {'voiceId': '248be419-c632-4f23-adf1-5324ed7dbf1d', 'provider': 'cartesia', 'fillerInjectionEnabled': False}, 'firstMessage': 'Hello', 'clientMessages': ['transcript', 'hang', 'function-call', 'speech-update', 'metadata', 'transfer-update', 'conversation-update'], 'serverMessages': ['end-of-call-report', 'status-update', 'hang', 'function-call'], 'serverUrl': 'https://mako-ace-sadly.ngrok-free.app/api/webhook/', 'backchannelingEnabled': False, 'backgroundDenoisingEnabled': False}}
    # Run the tool call handler
    results = asyncio.run(tool_call_handler(payload1))
    print("\nFinal Results:", json.dumps(results, indent=4))
