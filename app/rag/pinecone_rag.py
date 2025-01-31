import openai
import os
import tiktoken
from datetime import datetime, date
from typing import List, Literal
from pydantic import BaseModel, Field
import instructor
from pinecone import Pinecone
from dotenv import load_dotenv
from openai import OpenAI
from groq import Groq
import requests
import json

load_dotenv()

# Initialize the Pinecone client
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))

user_index = pc.Index("user-data-openai-embedding")
book_index = pc.Index("ah-test")

# Initialize the Clients (OpenAI, Instructor, Groq, SentenceTransformer)
openai.api_key = os.getenv("OPENAI_API_KEY")

# Initialize OpenAI
client_openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
client_openai_instructor = instructor.from_openai(
    client_openai)  # Apply the patch to the OpenAI client

# Initialize Groq
client_groq = Groq(api_key=os.getenv("GROQ_API_KEY"))
client = instructor.from_groq(client_groq, mode=instructor.Mode.TOOLS)

# embedder = SentenceTransformer("Alibaba-NLP/gte-Qwen2-1.5B-instruct")


# Classification model
class ClassificationResponse(BaseModel):
    label: Literal["ATOMIC_HABITS", "PERSONAL", "WEB_SEARCH"] = Field(
        ...,
        description="The predicted class label.",
    )


# Classification LLM for branch path
def classify(data: str, keywords: List[str]) -> ClassificationResponse:
    """Perform single-label classification on the input text."""
    return client_openai_instructor.chat.completions.create(
        # model="gpt-3.5-turbo",
        model='gpt-4o',
        response_model=ClassificationResponse,
        messages=[
            {
                'role':
                'system',
                'content':
                f'Use these keywords to determine the appropriate classification if any of them match the data then the classification should be ATOMIC_HABITS: {" ".join(keywords)}'
            },
            {
                "role": "user",
                "content": f"Classify the following text: {data}",
            },
        ],
    )

    # def get_embedding(text, model="Alibaba-NLP/gte-Qwen2-1.5B-instruct"):
    #     response = embedder.encode([text])[0]
    #     return response

    # def get_embedding(query, model="nomic-embed-text"):
    #   """
    #   Sends a POST request to the specified endpoint to get the embedding for the given query.

    #   Args:
    #     query: The text for which to generate an embedding.
    #     model: The name of the embedding model to use. Defaults to "nomic-embed-text".

    #   Returns:
    #     A dictionary containing the embedding response from the server.
    #   """
    #   url = "http://localhost:11434/api/embeddings"
    #   data = {
    #       "model": model,
    #       "prompt": query
    #   }
    #   headers = {'Content-Type': 'application/json'}

    #   response = requests.post(url, json=data, headers=headers)
    #   response.raise_for_status()  # Raise an exception for bad status codes
    #   data = response.json()
    #   data = data.get('embedding',[])
    #   return data

    # def get_embedding(text, model="rjmalagon/gte-qwen2-1.5b-instruct-embed-f16"):
    """
    Get embedding for a given text using the specified model via the Ollama API.

    Parameters:
        text (str): The text to embed.
        model (str): The name of the model to use for embedding.
        api_endpoint (str): The API endpoint for embedding.
        api_key (str, optional): API key for authentication, if required.

    Returns:
        dict: A dictionary containing the embedding or an error message.
    """
    api_endpoint = "http://localhost:11434/v1/embeddings"
    headers = {"Content-Type": "application/json"}
    payload = {
        "model": model,
        "input": text  # Single input text for embedding
    }

    try:
        # Make the API request
        response = requests.post(api_endpoint,
                                 headers=headers,
                                 data=json.dumps(payload))
        response.raise_for_status()  # Raise an error for HTTP error responses

        # Parse the response
        embedding_result = response.json().get('data', [])
        print(len(embedding_result[0]['embedding']))
        return embedding_result[0]['embedding']
    except requests.exceptions.RequestException as e:
        return {"success": False, "error": str(e)}


def get_embedding(text, model="text-embedding-ada-002"):
    print("This is TEXT", text)
    response = client_openai.embeddings.create(input=[text], model=model)
    return response.data[0].embedding


def query_pinecone_user(query_string,
                        index,
                        top_k=10,
                        namespace="",
                        filter={"user_id": "fake_user_id"}):
    xc = get_embedding(query_string)
    result = user_index.query(vector=xc,
                              top_k=top_k,
                              include_metadata=True,
                              namespace=namespace,
                              filter=filter)
    return result


# def query_pinecone_book(query_string,index, top_k=10, namespace=""):
#     xc = get_embedding(query_string)
#     result = book_index.query(vector=xc, top_k=top_k, include_metadata=True, namespace=namespace)
#     print(result)
#     return result
def query_pinecone_book(query_string,
                        index,
                        top_k=1,
                        namespace="default-namespace"):
    """
    Query Pinecone index and combine strings from top similarity vector and the next two sequential indices.

    Args:
        vector (list): The vector to query.
        top_k (int): Number of top results to fetch initially.
        namespace (str): The namespace to query.

    Returns:
        str: Combined strings from the top index and the next two indices, if conditions are met.
    """
    # Ensure the function is aware of the global book_index
    xc = get_embedding(query_string)

    # Query the Pinecone index
    result = index.query(vector=xc,
                         top_k=top_k,
                         include_metadata=True,
                         namespace=namespace)

    if not result or not result.matches:
        return "No results found."

    # Extract the top similarity match
    top_match = result.matches[0]
    top_index = int(
        top_match.id
    )  # Assuming the IDs are integers or convertible to integers
    index_stats = index.describe_index_stats().get('total_vector_count', 0)
    # print('**********INDEX STATS***********',index_stats)
    # print("**********TOP MATCH*************",top_match)
    # Check if the top index is 1451
    if top_index >= 1452:  # 1452 number of vectors in AH index
        return f"Top index {top_index} is restricted. No combined string returned."

    # Fetch strings for indices top_index, top_index + 1, top_index + 2
    indices_to_fetch = [top_index, top_index + 1, top_index + 2]
    # print(indices_to_fetch)
    combined_strings = []

    for index in indices_to_fetch:
        # Query each specific index to fetch its metadata (e.g., string content)
        individual_result = book_index.fetch(ids=[str(index)],
                                             namespace=namespace)
        # print(individual_result)
        if individual_result:
            # Assuming the metadata contains a 'text' field with the string content
            text = individual_result['vectors'][str(index)]['metadata']['text']
            print("**********TEXT***********", text)
            # print("**********INDEX STATS***********",individual_result['metadata'])

            if text:
                combined_strings.append(text)

    # Combine the fetched strings into a single string
    return combined_strings


def construct_prompt(data, query):
    prompt = "Answer the question based on the context below, and if the question can't be answered based on the context, please provide a thoughtful response or indicate that you do not have enough information."


def get_context_string(contexts: List[str]) -> str:
    return " ".join(contexts)


async def manage_conversation_tokens(conversation: List[str],
                                     call_id: str) -> List[str]:

    def num_tokens_from_messages(messages, tkmodel="cl100k_base"):
        encoding = tiktoken.get_encoding(tkmodel)
        num_tokens = 0
        for message in messages:
            num_tokens += 4  # every message follows <im_start>{role/name}\\n{content}<im_end>\\n
            for key, value in message.items():
                num_tokens += len(encoding.encode(value))
                if key == "name":  # if there's a name, the role is omitted
                    num_tokens += -1  # role is always required and always 1 token
        return num_tokens + 2  # every reply is primed with <im_start>assistant

    conv_history_tokens = num_tokens_from_messages(conversation)
    print("tokens: " + str(conv_history_tokens))
    token_limit = 32000
    max_response_tokens = 300
    while (conv_history_tokens + max_response_tokens >= token_limit):
        del conversation[1]
        conv_history_tokens = num_tokens_from_messages(conversation)

    # Summarize if necessary
    if conv_history_tokens + max_response_tokens >= token_limit:
        summarization = summarize_conversation(conversation)
        summary_embedding = get_embedding(summarization)
        idv = "id" + "this_is_a_temp_id"  #str(time.time())
        user_index.upsert(vectors=[{
            "id": idv,
            "values": summary_embedding,
            "metadata": {
                'text': summarization,
                'user_id': call_id
            }
        }],
                          namespace='user-data-openai-embedding')
        return [summarization]

    return conversation


# Summarization function
def summarize_conversation(context: List[str]) -> str:
    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")
    today = date.today()
    date_string = str(today)

    completion = client.chat.completions.create(
        # engine="gpt-3.5-turbo",
        model="llama3-8b-8192",
        prompt=
        f"Summarize the following conversation that occurred at {current_time} on {date_string}:\\n{context}",
        temperature=0.3,
        max_tokens=300,
        top_p=0.9,
        presence_penalty=0)
    summarization = completion.choices[0].text.strip()
    return summarization
