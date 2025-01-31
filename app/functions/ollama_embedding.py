exec("""
def get_embedding(text, model="rjmalagon/gte-qwen2-1.5b-instruct-embed-f16:latest"):
    \"\"\"
    Get embedding for a given text using the specified model via the Ollama API.

    Parameters:
        text (str): The text to embed.
        model (str): The name of the model to use for embedding.

    Returns:
        dict: A dictionary containing the embedding or an error message.
    \"\"\"
    import requests
    import json
    
    api_endpoint = "http://localhost:11434/v1/embeddings"
    headers = {
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "input": text  # Single input text for embedding
    }

    try:
        # Make the API request
        response = requests.post(
            api_endpoint, 
            headers=headers, 
            data=json.dumps(payload)
        )
        response.raise_for_status()  # Raise an error for HTTP error responses
        
        # Print the raw response for debugging
        print("Response Status Code:", response.status_code)
        print("Response Text:", response.json())

        # Parse the response
        embedding_result = response.json().get('data', [])
        return embedding_result[0]['emdedding]

    except requests.exceptions.RequestException as e:
        print("Request Error:", str(e))
        return {
            "success": False,
            "error": str(e)
        }
""")
