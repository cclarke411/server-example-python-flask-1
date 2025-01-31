import os
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader

data_path = os.path.abspath(os.path.join(os.getcwd(), "data"))

def get_character_inspiration(toolCallId,inspiration):
    fallbackResponse = {
        "results": [
            {
                "toolCallId": toolCallId,
                "result": "Sorry, I am dealing with a technical issue at the moment, perhaps because of heightened user traffic. Come back later and we can try this again. Apologies for that."
            }
        ]
    }

    if inspiration:
        try:
            if os.path.exists(data_path):
                required_exts = [".md"]
                reader = SimpleDirectoryReader(
                    input_dir=data_path, 
                    required_exts=required_exts, 
                    recursive=True
                )
                documents = reader.load_data()
                index = VectorStoreIndex.from_documents(documents)

                queryEngine = index.as_query_engine()

                # Query the engine with the provided inspiration
                response = queryEngine.query(inspiration)

                # Wrap the result in the specified format
                return {
                    "results": [
                        {
                            "toolCallId": toolCallId,
                            "result": response.response
                        }
                    ]
                }
            else:
                return fallbackResponse
        except Exception as e:
            print(f"Error occurred: {e}")
            return fallbackResponse
    else:
        return fallbackResponse
