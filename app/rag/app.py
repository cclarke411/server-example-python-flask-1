import logging
import json
import os
import time
from datetime import datetime, date
from db import *
from typing import List, Union, Literal
from pydantic import BaseModel, Field, ValidationError
import pinecone_rag  # Import the RAG functionality
from pinecone import Pinecone
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from flask_cors import CORS
from flask import Flask, Blueprint, Response, request, jsonify
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity, verify_jwt_in_request
from user_models import UserQueryData
from models import AddKnowledge, Action, Category, MemoryData
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)
app.config["SECRET_KEY"] = "03faa7b5-3058-41ae-b7f4-225ffdf80a0f"

CORS(app)
JWTManager(app)


@app.route('/')
def home():
    return jsonify(message="working..")

@app.route('/token', methods=['POST'])
def test():
    print(request.json)
    username, email, picture = request.json.get('username'), request.json.get('email'), request.json.get('picture')
    user_exists = check_if_user_exists(email)
    if not user_exists:
        result = str(create_user({
            'username': username,
            'email': email,
            'picture': picture,
            'current_bg': 'black',
            'notifications': [],
            'character': {
                'name': '', 
                'alias': '', 
                'super_skill':'', 
                'weakness' : '', 
                'powers':[], 
                'equipments':[], 
                'height' : '', 
                'age':0, 
                'birthplace': '' 
            }
        }).inserted_id)
        access_token = create_access_token(identity=result)
    else:
        result = str(get_user_by_email(email)['_id'])
        access_token = create_access_token(identity=result)
    
    return jsonify(access_token=access_token,success=True)

@app.route('/user')
@jwt_required()
def get_user():
    user_id = get_jwt_identity()
    user = get_user_by_id(user_id)
    user['_id'] = str(user['_id'])
    return jsonify(user=user, success=True)



@app.route('/color', methods=['POST'])
@jwt_required()
def add_color():
    user_id = get_jwt_identity()
    color = request.json['color']
    add_color_to_user(color, user_id)
    return jsonify(success=True)


@app.route('/character', methods=['POST'])
@jwt_required()
def add_to_book():
    user_id = get_jwt_identity()
    key, value = f"{request.json['key']}", request.json['value']
    changes = {key: value}
    change_char(changes, user_id)
    return jsonify(success=True)
    

class Message(BaseModel):
    role: Literal['system', 'user', 'assistant']
    content: str

class MemoryData(BaseModel):
    messages: List[Union[Message, str]]

# Initialize the Pinecone client
pc_key = os.getenv("PINECONE_API_KEY")

pc = Pinecone(api_key=pc_key)
user_index = pc.Index("user-data-openai-embedding")
book_index = pc.Index("ah-test")

# Simulate a database with dictionaries
user_db = {}
memory_db = {}

async def get_memory(user_id: str) -> MemoryData:
    return memory_db.get(user_id, MemoryData(messages=[]))

async def update_memory(user_id: str, memory_data: MemoryData):
    memory_db[user_id] = memory_data



# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize database session
Session = sessionmaker(bind=create_engine('sqlite:///user_db.db'))

# Function to provide interaction assistance and command handling
def provide_interaction_assistance() -> str:
    assistance_text = (
        f'''You can ask me anything about the book, such as summaries, key concepts, practical tips, and more
        For example, you can say things like: What is the book 'Atomic Habits' about. How do I build good habits. What is the Two-Minute Rule"
        Can you give me some tips on habit tracking Feel free to explore different topics and ask follow-up questions to dive deeper into specific concepts"
        If you're not sure where to start, just say 'Help' or 'What can I ask?' and I'll provide some suggestions.
        To navigate through different sections, you can say commands like 'next chapter,' 'previous tip,' or 'go back.
        You can also ask for quotes, case studies, or success stories from the book for more inspiration.
        If you'd like, I can send you daily reminders and motivational quotes to help you stay on track with your habits.'''
    )
    return assistance_text

@app.route('/openai-advanced/chat/completions', methods=['POST'])
async def openai_advanced_chat_completions_route():
    session = Session()
    try:
        request_data = request.get_json()
        print("********THIS IS REQUEST DATA********",request_data)
        messages = request_data.get('messages')
        model = request_data.get('model')
        streaming = request_data.get('stream', False)
        
        # Extract the user query from messages
        query_string = messages[-1]['content']
        call_id = request_data.get('call', {}).get('id', 'default_call_id')
        print(call_id)

        # Check if the user asked for help or interaction assistance
        if query_string.lower() in ["help", "what can i ask?"]:
            assistance_text = provide_interaction_assistance()
            return Response(generate_streaming_introduction(assistance_text), content_type='text/event-stream')

        # Fetch memory data for context
        memory_data = await get_memory(call_id)
        print(f"**********THIS IS THE MEMORY DATA***********", memory_data)

        # Classify the input to determine context
        atomic_habits_keywords = ["habit", "Atomic Habits", "James Clear", "self-improvement", "routine", "productivity","habit"]
        classification_result = pinecone_rag.classify(query_string, atomic_habits_keywords)
        classification_label = classification_result.label

        # Get embedding for the query string
        embedding_response = pinecone_rag.get_embedding(query_string)
        xq = embedding_response

        # Vector context retrieval based on classification
        contexts = []
        if classification_label == "PERSONAL":
            res = pinecone_rag.query_pinecone_user(query_string, user_index, top_k=1, namespace='user-data-openai-embedding')
            contexts = contexts + [x['metadata']['text'] for x in res['matches']]
            print(f"Response: {res}")
        elif classification_label == "ATOMIC_HABITS":
            book_res = pinecone_rag.query_pinecone_book( query_string,book_index, top_k=1, namespace='ah-test')
            print(f"Response: {book_res}")
            contexts = contexts + [x['metadata']['text'] for x in book_res['matches']]
        
        print(f"Retrieved {len(contexts)} contexts")
        
        # Construct prompt and generate text
        # Prepare the conversation context
        now = datetime.now()
        current_time = now.strftime("%H:%M:%S")
        today = date.today()
        date_string = str(today)
        system_message = {"role": "system", "content": f"It is {current_time} on {date_string} and you are a friendly robot that enjoys being helpful to your human friend."}
        user_greeting = {"role": "user", "content": "Hey bot."}
        bot_response = {"role": "assistant", "content": "What's up?"}
        conversation = [system_message, user_greeting, bot_response]

        # Merge context with user query and update conversation history
        prompt_end = "The following may or may not be relevant information from past conversations. If it is not relevant to this conversation, ignore it:\n\n"
        prompt = query_string + "\n\n" + prompt_end + "\n\n---\n\n".join(contexts[:1])
        conversation.append({"role": "user", "content": prompt})

        # Pass conversation + context + prompt to OpenAI LLM
        completion = pinecone_rag.client_openai.chat.completions.create(
            model="gpt-4o",  # Replace with the appropriate OpenAI model
            messages=conversation,
            max_tokens=300,
            stream=True,
            presence_penalty=0,
            temperature=0.5,
            top_p=0.9,
        )
        # print(f"**********RAG Completion***********\\n\\n", completion)
        response_text = extract_response_text(completion)
        print("**********RAG Response*******\\n\\n", response_text + "\\n")

        # Manage tokens and summarize if needed
        conversation = await pinecone_rag.manage_conversation_tokens(conversation, call_id) # Figure out how to add in stored memory from dictioinary memory_data.context + [query_string, response_text]

        # Update memory with the new query and response
        conversation.append({"role": "user", "content": response_text})
        print("**********NEW CONTEXT***********", completion)
        await update_memory(call_id, MemoryData(messages=conversation))
        print("AWAITED MEMORY UPDATE")
        session.commit()

        return Response(generate_streaming_introduction(response_text), content_type='text/event-stream')
    
    except Exception as e:
        session.rollback()
        logger.error(f"Error processing user data: {str(e)}", exc_info=True)
        return jsonify({"status": "error", "detail": f"Internal Server Error: {str(e)}"}), 500
    finally:
        session.close()

def generate_streaming_response(data):
    """
    Generator function to simulate streaming data.
    """
    for message in data:
        print(message)
        json_data = message.model_dump_json()
        yield f"data: {json_data}\n\n"

def generate_streaming_introduction(data: str):
    """
    Generator function to simulate streaming data in the OpenAI format, word by word.
    """
    words = data.split()
    for word in words:
        print(word)
        json_data = json.dumps({"choices": [{"delta": {"content": word + " "}}]})
        yield f"data: {json_data}\n\n"

def extract_response_text(completion):
    text=""
    for chunks in completion:
        mini_chunk = chunks.choices[0].delta.content
        if mini_chunk is None:
            mini_chunk = ""
        text += mini_chunk
        # Return None if no messages are found
    return(text)

if __name__ == "__main__":
    app.run(port=5001, debug=True)

pinecone_rag.client_groq()