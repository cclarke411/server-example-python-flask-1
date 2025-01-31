import json
import uuid
from typing import List

def generate_streaming_response(data):
    """
    Generator function to stream data.
    """
    for message in data:
        json_data = json.dumps(message)
        yield f"data: {json_data}\n\n"


def provide_interaction_assistance() -> str:
    """
    Provides text for assisting users with interaction.
    """
    assistance_text = f"""
        You can ask me anything about the book, such as summaries, key concepts, practical tips, and more.

        For example, you can say things like:
        'What is the book 'Atomic Habits' about'
        'How do I build good habits'
        'What is the Two-Minute Rule'
        'Can you give me some tips on habit tracking'

        Feel free to explore different topics and ask follow-up questions to dive deeper into specific concepts.
        If you're not sure where to start, just say 'Help' or 'What can I ask?' and I'll provide some suggestions.
        To navigate through different sections, you can say commands like 'next chapter,' 'previous tip,' or 'go back.'
        You can also ask for quotes, case studies, or success stories from the book for more inspiration.
        If you'd like, I can send you daily reminders and motivational quotes to help you stay on track with your habits.
        """
    return assistance_text


def generate_streaming_introduction(data: str):
    """
    Generator function to simulate streaming data in the OpenAI format, word by word.
    """
    words = data.split()
    for word in words:
        json_data = json.dumps({"choices": [{"delta": {"content": word + " "}}]})
        yield f"data: {json_data}\n\n"

def augment_system_lists(origin: List[str], final: List[str])-> List[str]:
    """
    Augments the 'origin' list with entries from the 'final' list, 
    specifically combining system messages while preserving other message types.

    Args:
        origin: The original list of messages.
        final: The list of messages to be augmented into the 'origin' list.

    Returns:
        The augmented list of messages.

    Raises:
        ValueError: If the 'origin' list is empty or its first entry is not a dictionary 
                    with a 'content' key.
    """
    if not origin:
        raise ValueError("The `origin` list is empty. Cannot augment an empty list.")
    
    if not isinstance(origin[0], dict) or "content" not in origin[0]:
        raise ValueError("The first item in `origin` must be a dictionary with a 'content' key.")
    
    for entry in final:
        if entry["role"] == "system":
            origin[0]["content"] += f"\n\n{entry['content']}"
        else:
            origin.append(entry)
    
    return origin

def generate_user_uuid(user_name: str, email_address: str):
    """
    Generates a consistent UUID based on username and email.

    Args:
        user_name: The user's username.
        email_address: The user's email address.

    Returns:
        A UUID string.
    """
    combined = f"{user_name}-{email_address}"
    namespace = uuid.uuid5(uuid.NAMESPACE_DNS, combined)
    return str(namespace)