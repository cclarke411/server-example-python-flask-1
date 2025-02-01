import os
import json
import logging
import time  # Used for simulating a delay in streaming
from flask import Blueprint, request, Response, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
import instructor
from openai import OpenAI
from dotenv import load_dotenv
from app.rag import pinecone_rag
from groq import Groq
from pinecone import Pinecone
from app.functions.get_custom_llm_streaming import generate_user_uuid, augment_system_lists
from app.rag.db import get_user_by_email, get_user_by_id, add_color_to_user, change_char, check_if_user_exists, create_user

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
finalize_details_args = []

pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
user_index = pc.Index("user-data-openai-embedding")
book_index = pc.Index("ah-test")

custom_llm = Blueprint('custom_llm', __name__)

# client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
# client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# OpenAI Client
client_openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
client = instructor.from_openai(client_openai)


@custom_llm.route('/token', methods=['POST'])
def test():
    # print(request.json)
    username, email, picture = request.json.get('username'), request.json.get(
        'email'), request.json.get('picture')
    user_exists = check_if_user_exists(email)
    if not user_exists:
        result = str(
            create_user({
                'username': username,
                'email': email,
                'picture': picture,
                'current_bg': 'black',
                'notifications': [],
                'character': {
                    'name': '',
                    'alias': '',
                    'super_skill': '',
                    'weakness': '',
                    'powers': [],
                    'equipments': [],
                    'height': '',
                    'age': 0,
                    'birthplace': ''
                }
            }).inserted_id)
        access_token = create_access_token(identity=result)
    else:
        result = str(get_user_by_email(email)['_id'])
        access_token = create_access_token(identity=result)

    return jsonify(access_token=access_token, success=True)


@custom_llm.route('/user')
@jwt_required()
def get_user():
    user_id = get_jwt_identity()
    user = get_user_by_id(user_id)
    user['_id'] = str(user['_id'])
    return jsonify(user=user, success=True)


@custom_llm.route('/color', methods=['POST'])
@jwt_required()
def add_color():
    user_id = get_jwt_identity()
    color = request.json['color']
    add_color_to_user(color, user_id)
    return jsonify(success=True)


@custom_llm.route('/character', methods=['POST'])
@jwt_required()
def add_to_book():
    user_id = get_jwt_identity()
    key, value = f"{request.json['key']}", request.json['value']
    changes = {key: value}
    change_char(changes, user_id)
    return jsonify(success=True)


@custom_llm.route('/basic/chat/completions', methods=['POST'])
def basic_custom_llm_route():
    request_data = request.get_json()
    response = {
        "id":
        "chatcmpl-8mcLf78g0quztp4BMtwd3hEj58Uof",
        "object":
        "chat.completion",
        "created":
        int(time.time()),
        "model":
        "gpt-3.5-turbo-0613",
        "system_fingerprint":
        None,
        "choices": [{
            "index": 0,
            "delta": {
                "content":
                request_data['messages'][-1]['content']
                if len(request_data['messages']) > 0 else ""
            },
            "logprobs": None,
            "finish_reason": "stop"
        }]
    }
    return jsonify(response), 200


# @custom_llm.route('/chat/completions', methods=['POST'])
# def openai_advanced_custom_llm_basic_route():
#     """Handle POST requests to the chat completions endpoint."""
#     try:
#         # Parse incoming request data
#         request_data = request.get_json()
#         if not request_data:
#             raise ValueError("No JSON data provided in the request.")

#         # Extract required data from the request
#         messages = request_data.get("messages")
#         if not messages:
#             raise ValueError("Messages field is required in the request.")

#         model_config = request_data.get("message", {}).get("assistant", {}).get("model", {})
#         stream = request_data.get("message", {}).get("analysis", {}).get("streaming", True)

#         # Prepare the request payload for the LLM client
#         llm_request_data = {
#             "model": model_config.get("model", "gpt-3.5-turbo"),
#             "messages": messages,
#             "temperature": model_config.get("temperature", 0.7),
#             "stream": stream
#         }

#         # Log the processed request payload
#         logger.info(f"LLM Request data: {json.dumps(llm_request_data, indent=2)}")

#         # Handle streaming and non-streaming cases
#         if stream:
#             # Generate streaming response
#             chat_completion_stream = client.chat.completions.create(**llm_request_data)
#             return Response(generate_streaming_response(chat_completion_stream),
#                             content_type='text/event-stream')
#         else:
#             # Generate non-streaming response
#             chat_completion = client.chat.completions.create(**llm_request_data)
#             return Response(chat_completion.model_dump_json(),
#                             content_type='application/json')

#     except ValueError as ve:
#         logger.error(f"ValueError: {str(ve)}")
#         return jsonify({"error": str(ve)}), 400
#     except Exception as e:
#         logger.error(f"Unexpected error: {str(e)}", exc_info=True)
#         return jsonify({"error": "An unexpected error occurred. Please try again later."}), 500

# @custom_llm.route('/chat/completions', methods=['POST'])
# def openai_advanced_custom_llm_basic_route():
#     """Handle POST requests to the chat completions endpoint."""
#     # Parse incoming request data
#     request_data = request.get_json()
#     payload = request_data.get('message')
#     tools = request_data.get('tools')
#     # print(tools)
#     ts = time.time()
#     # payload_type = payload['type']
#     # print(request_data)
#     with open(f'/Users/clydeclarke/Documents/server-example-python-flask/app/response_data/response_data_{ts}.json', "a") as log_file:
#       log_file.write(json.dumps(request_data,indent=4))
#     # Check if the model field is not an empty list
#     if request_data.get("model", []):
#         try:
#             if not request_data:
#                 raise ValueError("No JSON data provided in the request.")

#             # Extract required data from the request
#             messages = request_data.get("messages")
#             if not messages:
#                 raise ValueError("Messages field is required in the request.")

#             model_config = request_data.get("message", {}).get("assistant", {}).get("model", {})
#             stream = request_data.get("message", {}).get("analysis", {}).get("streaming", True)

#             query_string = messages[-1]['content']

#             if query_string.lower() in ["help", "what can i ask?"]:
#                 assistance_text = provide_interaction_assistance()
#                 return Response(generate_streaming_introduction(assistance_text), content_type='text/event-stream')

#             # Prepare the request payload for the LLM client
#             llm_request_data = {
#                 "model": "llama3-groq-70b-8192-tool-use-preview",#model_config.get("model", "gpt-3.5-turbo"),
#                 "messages": messages,
#                 "temperature": model_config.get("temperature", 0.7),
#                 "stream": stream,
#                 "tools": tools
#             }

#             # Handle streaming and non-streaming cases
#             if stream:
#                 # Generate streaming response
#                 chat_completion_stream = client.chat.completions.create(**llm_request_data)
#                 return Response(generate_streaming_response(chat_completion_stream),
#                                 content_type='text/event-stream')
#             else:
#                 # Generate non-streaming response
#                 chat_completion = client.chat.completions.create(**llm_request_data)
#                 return Response(chat_completion.model_dump_json(),
#                                 content_type='application/json')

#         except ValueError as ve:
#             logger.error(f"ValueError: {str(ve)}")
#             return jsonify({"error": str(ve)}), 400
#         except Exception as e:
#             logger.error(f"Unexpected error: {str(e)}", exc_info=True)
#             return jsonify({"error": "An unexpected error occurred. Please try again later."}), 500
#     else:
#         # If model field is an empty list, skip the try block and return a response
#         return jsonify({"message": "Model field is empty or not provided. No operation performed."}), 400


@custom_llm.route('/chat/completions', methods=['POST'])
async def openai_advanced_chat_completions_route_new():
    """Handle POST requests for advanced OpenAI chat completions."""
    # Parse incoming request data
    request_data = request.get_json()
    # print(request_data)
    if not request_data.get("model", []):
        return jsonify({"error": "No JSON data provided in the request."}), 400

    # Log the incoming request data for debugging
    timestamp = request_data.get("message", {}).get("timestamp", time.time())
    # with open(f'/Users/clydeclarke/Documents/server-example-python-flask/app/response_data/user_data_log.json-{timestamp}', 'w') as log_file:
    #     json.dump(request_data, log_file, indent=4)

    # Check if the model field is not empty or missing
    if request_data.get("model", []):
        try:
            # print("*****************THIS IS METADATA*************\n", request_data.get("metadata", []))

            # Extract relevant data from the request
            messages = request_data.get("messages", [])
            tools = request_data.get("tools", None)
            model_config = request_data.get("message",
                                            {}).get("assistant",
                                                    {}).get("model", {})
            stream = request_data.get("message",
                                      {}).get("analysis",
                                              {}).get("streaming", True)

            if not messages:
                raise ValueError("Messages field is required in the request.")

            # Extract the user query from the messages
            query_string = messages[-1]['content']
            if query_string.lower() in ["help", "what can i ask?"]:
                assistance_text = provide_interaction_assistance()
                return Response(
                    generate_streaming_introduction(assistance_text),
                    content_type='text/event-stream')

            # Classify the input to determine context
            atomic_habits_keywords = [
                "habit", "Atomic Habits", "James Clear", "self-improvement",
                "routine", "productivity"
            ]
            classification_result = pinecone_rag.classify(
                query_string, atomic_habits_keywords)
            classification_label = classification_result.label

            # Get embedding for the query string
            # embedding = pinecone_rag.get_embedding(query_string)
            # print(query_string,embedding)
            # Metadata Format:
            # metadata{
            #         "data":{
            #               user: {
            #                     "email":email,
            #                     "username":"username"
            #                     }
            #                }
            #      }

            # email_address = request_data.get("metadata", {}).get("data", {}).get("user", {}).get('email', 'unknown')
            # user_name = request_data.get("metadata",{}).get("data", {}).get("user", {}).get('username', 'unknown')

            user_name = request_data.get('metadata', []).get('user_id', [])
            email_address = request_data.get('metadata', []).get('user_id', [])

            user_id = generate_user_uuid(user_name, email_address)

            # Vector context retrieval based on classification
            contexts = []
            if classification_label == "PERSONAL":
                # user_index = "user-data-openai-embedding"  # Specify the user index
                res = pinecone_rag.query_pinecone_user(
                    query_string,
                    user_index,
                    top_k=1,
                    namespace='user-data-openai-embedding')
                contexts.extend(
                    [x['metadata']['text'] for x in res['matches']])
                # print("******USER CONTEXT*********",contexts)
            elif classification_label == "ATOMIC_HABITS":
                # book_index = "ah-test"  # Specify the book index
                context_strings = pinecone_rag.query_pinecone_book(
                    query_string, book_index, top_k=1, namespace='ah-test')
                # contexts.extend([x['metadata']['text'] for x in res['matches']])
                contexts.extend(context_strings)
                # print("******BOOK CONTEXT*********",contexts)
            # Retrieve email for system message

            conversation = []

            system_message = [{"role": "system", \
                              "content": f"""The email address of the interviewee is: {email_address}, 
                                             remove all special characters from your response such as #,*, &, ^, %, $, !"""}]

            conversation = augment_system_lists(system_message, messages)

            prompt_end = "The following may or may not be relevant information from past conversations. If it is not relevant to this conversation, ignore it:\n\n"
            prompt = query_string + "\n\n" + prompt_end + "\n\n---\n\n".join(
                contexts[:1])

            # Augment the origin_sys with final_sys
            conversation.append({
                "role":
                "user",
                "content":
                f'Use the following information {prompt} \n to answer the {query_string} is applicable else just answer to the best of your ability'
            })
            # print(conversation)
            # Prepare the request payload for the LLM client
            llm_request_data = {
                "model": "gpt-4o",  #model_config.get("model", "gpt-4o"),
                "messages": conversation,
                "temperature": model_config.get("temperature", 0.7),
                "stream": stream,
                "tools": tools,
            }

            # Handle streaming and non-streaming cases
            if stream:
                chat_completion_stream = client_openai.chat.completions.create(
                    **llm_request_data)
                return Response(
                    generate_streaming_response(chat_completion_stream),
                    content_type='text/event-stream')
            else:
                chat_completion = client.chat.completions.create(
                    **llm_request_data)
                return Response(chat_completion.model_dump_json(),
                                content_type='application/json')

        except ValueError as ve:
            logger.error(f"ValueError: {str(ve)}")
            return jsonify({"error": str(ve)}), 400
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}", exc_info=True)
            return jsonify({
                "error":
                "An unexpected error occurred. Please try again later."
            }), 500
    else:
        pass
    # If the model field is empty or missing, return a 400 response
    return jsonify({
        "message":
        "Model field is empty or not provided. No operation performed."
    }), 400


# @custom_llm.route('/finalizeDetails', methods=['POST'])
# def finalize_details():
#     """Handle POST requests to the finalize details endpoint."""
#     try:
#         # Parse incoming request data
#         request_data = request.get_json()
#         payload = request_data.get('message')
#         print(payload)
#         if not request_data:
#             raise ValueError("No JSON data provided in the request.")
#         else:
#             return(jsonify(payload), 200)
#     except Exception as e:
#             logger.error(f"Unexpected error: {str(e)}", exc_info=True)
#             return jsonify({"error": "An unexpected error occurred. Please try again later."}), 500


@custom_llm.route('/finalizeDetails', methods=['POST'])
def finalize_details():
    """Handle POST requests to the finalize details endpoint."""
    try:
        # Parse incoming request data
        request_data = request.get_json()
        payload = request_data.get('message')
        payload_type = payload['type']
        # print(payload_type)
        if not request_data:
            raise ValueError("No JSON data provided in the request.")

        # Extract relevant payload
        payload = request_data.get('message')

        # Function to extract finalizeDetails arguments
        def extract_finalize_details_arguments(data):
            arguments_list = []

            # Search in `toolCalls`
            tool_calls = data.get("toolCalls", [])
            for call in tool_calls:
                function = call.get("function", {})
                if function.get("name") == "finalizeDetails":
                    arguments_list.append(function.get("arguments"))

            # Search in `toolWithToolCallList`
            tool_with_tool_call_list = data.get("toolWithToolCallList", [])
            for item in tool_with_tool_call_list:
                tool_call = item.get("toolCall", {}).get("function", {})
                if tool_call.get("name") == "finalizeDetails":
                    arguments_list.append(tool_call.get("arguments"))

            # Search in `artifact.messages`
            artifact_messages = data.get("artifact", {}).get("messages", [])
            for message in artifact_messages:
                tool_calls = message.get("toolCalls", [])
                for call in tool_calls:
                    function = call.get("function", {})
                    if function.get("name") == "finalizeDetails":
                        arguments_list.append(function.get("arguments"))

            # Search in `messagesOpenAIFormatted`
            formatted_messages = data.get("artifact",
                                          {}).get("messagesOpenAIFormatted",
                                                  [])
            for message in formatted_messages:
                tool_calls = message.get("tool_calls", [])
                for call in tool_calls:
                    function = call.get("function", {})
                    if function.get("name") == "finalizeDetails":
                        arguments_list.append(function.get("arguments"))

            return arguments_list

        # Extract arguments
        extracted_arguments = extract_finalize_details_arguments(payload)
        save_path = "/Users/clydeclarke/Documents/server-example-python-flask/app/response_data"  # Directory to save responses
        os.makedirs(save_path, exist_ok=True)  # Ensure the directory exists

        for i, arguments in enumerate(extracted_arguments):
            file_name = os.path.join(save_path, f"response_{i + 1}.json")
            with open(file_name, "w") as json_file:
                json.dump(arguments, json_file, indent=2)
        # Include extracted arguments in the response
        response = {
            "payload":
            payload,
            "finalizeDetailsArguments":
            extracted_arguments,
            "savedFiles": [
                f"response_{i + 1}.json"
                for i in range(len(extracted_arguments))
            ]
        }
        # print(response)
        return jsonify(response), 200

    except ValueError as ve:
        logger.error(f"ValueError: {str(ve)}")
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        return jsonify(
            {"error":
             "An unexpected error occurred. Please try again later."}), 500


@custom_llm.route('/openai-sse/chat/completions', methods=['POST'])
def custom_llm_openai_sse_handler():
    request_data = request.get_json()
    streaming = request_data.get('stream', False)

    if streaming:
        # Simulate a stream of responses

        chat_completion_stream = client.chat.completions.create(**request_data)

        return Response(generate_streaming_response(chat_completion_stream),
                        content_type='text/event-stream')
    else:
        # Simulate a non-streaming response
        chat_completion = client.chat.completions.create(**request_data)
        return Response(chat_completion.model_dump_json(),
                        content_type='application/json')


@custom_llm.route('/openai-advanced/chat/completions', methods=['POST'])
def openai_advanced_custom_llm_route():
    request_data = request.get_json()
    streaming = request_data.get('stream', False)

    last_message = request_data['messages'][-1]
    prompt = f"""
    Create a prompt which can act as a prompt template where I put the original prompt and it can modify it according to my intentions so that the final modified prompt is more detailed. You can expand certain terms or keywords.
    ----------
    PROMPT: {last_message['content']}.
    MODIFIED PROMPT: """
    completion = client.completions.create(model="gpt-3.5-turbo-instruct",
                                           prompt=prompt,
                                           max_tokens=500,
                                           temperature=0.7)
    modified_message = request_data['messages'][:-1] + [{
        'content':
        completion.choices[0].text,
        'role':
        last_message['role']
    }]

    request_data['messages'] = modified_message
    if streaming:
        chat_completion_stream = client.chat.completions.create(**request_data)

        return Response(generate_streaming_response(chat_completion_stream),
                        content_type='text/event-stream')
    else:
        # Simulate a non-streaming response
        chat_completion = client.chat.completions.create(**request_data)
        return Response(chat_completion.model_dump_json(),
                        content_type='application/json')


# Function to provide interaction assistance and command handling
def provide_interaction_assistance() -> str:
    assistance_text = (
        '''You can ask me anything about the book, such as summaries, key concepts, practical tips, and more
        For example, you can say things like: What is the book 'Atomic Habits' about. How do I build good habits. What is the Two-Minute Rule"
        Can you give me some tips on habit tracking Feel free to explore different topics and ask follow-up questions to dive deeper into specific concepts"
        If you're not sure where to start, just say 'Help' or 'What can I ask?' and I'll provide some suggestions.
        To navigate through different sections, you can say commands like 'next chapter,' 'previous tip,' or 'go back.
        You can also ask for quotes, case studies, or success stories from the book for more inspiration.
        If you'd like, I can send you daily reminders and motivational quotes to help you stay on track with your habits.'''
    )
    return assistance_text


def generate_streaming_response(data):
    """
  Generator function to simulate streaming data.
  """
    for message in data:
        json_data = message.model_dump_json()
        yield f"data: {json_data}\n\n"


def generate_streaming_introduction(data: str):
    """
    Generator function to simulate streaming data in the OpenAI format, word by word.
    """
    words = data.split()
    for word in words:
        # print(word)
        json_data = json.dumps(
            {"choices": [{
                "delta": {
                    "content": word + " "
                }
            }]})
        yield f"data: {json_data}\n\n"
