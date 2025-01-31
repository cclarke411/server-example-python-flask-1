from pydantic import BaseModel, Field
from typing import Literal, List, Optional, Dict, Any


class Message(BaseModel):
    role: Literal['system', 'assistant', 'user']
    content: str


class DetailedMessage(BaseModel):
    role: Literal['system', 'assistant', 'user', 'bot']
    message: str
    time: int
    endTime: Optional[int] = None
    secondsFromStart: Optional[float] = None
    duration: Optional[float] = None
    source: Optional[str] = None


class Artifact(BaseModel):
    messages: List[DetailedMessage]
    messagesOpenAIFormatted: List[Message]


class Monitor(BaseModel):
    listenUrl: str
    controlUrl: str


class Transport(BaseModel):
    assistantVideoEnabled: bool


class Call(BaseModel):
    id: str
    orgId: str
    createdAt: str
    updatedAt: str
    type: str
    monitor: Monitor
    transport: Transport
    webCallUrl: str
    status: str
    assistantId: str
    assistantOverrides: Dict[str, List[str]]


class Voice(BaseModel):
    model: str
    voiceId: str
    provider: str
    fillerInjectionEnabled: bool


class Model(BaseModel):
    url: str
    model: str
    toolIds: List[str]
    messages: List[Message]
    provider: str
    temperature: float
    emotionRecognitionEnabled: bool
    tools: List[Dict[str, Any]]


class Assistant(BaseModel):
    id: str
    orgId: str
    name: str
    voice: Voice
    createdAt: str
    updatedAt: str
    model: Model


class ConversationUpdate(BaseModel):
    timestamp: int
    type: Literal['conversation-update']
    conversation: List[Message]
    messages: List[DetailedMessage]
    artifact: Artifact
    call: Call
    assistant: Assistant


# Example usage
# if __name__ == "__main__":
#     payload = {
#         "timestamp": 1735448156783,
#         "type": "conversation-update",
#         "conversation": [
#             {"role": "system", "content": "You are a Personal Learning and Implementation Assistant..."},
#             {"role": "assistant", "content": "Hi there."},
#             {"role": "user", "content": "Hi."},
#             {"role": "assistant", "content": "How are you today?"}
#         ],
#         "messages": [
#             {
#                 "role": "system",
#                 "message": "You are a Personal Learning and Implementation Assistant with specialized knowledge of Atomic Habits...",
#                 "time": 1735448123681,
#                 "secondsFromStart": 0
#             },
#             {
#                 "role": "assistant",
#                 "message": "Hi there.",
#                 "time": 1735448125093,
#                 "endTime": 1735448125753,
#                 "secondsFromStart": 1.2,
#                 "duration": 660,
#                 "source": ""
#             },
#             {
#                 "role": "user",
#                 "message": "Hi.",
#                 "time": 1735448126613,
#                 "endTime": 1735448127113,
#                 "secondsFromStart": 2.7,
#                 "duration": 500
#             }
#         ],
#         "artifact": {
#             "messages": [
#                 {
#                     "role": "system",
#                     "message": "You are a Personal Learning and Implementation Assistant with specialized knowledge of Atomic Habits...",
#                     "time": 1735448123681,
#                     "secondsFromStart": 0
#                 },
#                 {
#                     "role": "assistant",
#                     "message": "Hi there.",
#                     "time": 1735448125093,
#                     "endTime": 1735448125753,
#                     "secondsFromStart": 1.2,
#                     "duration": 660,
#                     "source": ""
#                 },
#                 {
#                     "role": "user",
#                     "message": "Hi.",
#                     "time": 1735448126613,
#                     "endTime": 1735448127113,
#                     "secondsFromStart": 2.7,
#                     "duration": 500
#                 }
#             ],
#             "messagesOpenAIFormatted": [
#                 {"role": "system", "content": "You are a Personal Learning and Implementation Assistant..."},
#                 {"role": "assistant", "content": "Hi there."},
#                 {"role": "user", "content": "Hi."}
#             ]
#         },
#         "call": {
#             "id": "1e9893d4-d71b-455f-aad0-7ac54c58e5f4",
#             "orgId": "bf389f00-a6ab-4e59-b031-fb09510545d1",
#             "createdAt": "2024-12-29T04:55:22.615Z",
#             "updatedAt": "2024-12-29T04:55:22.615Z",
#             "type": "webCall",
#             "monitor": {
#                 "listenUrl": "wss://phone-call-websocket.aws-us-west-2-backend-production2.vapi.ai/1e9893d4-d71b-455f-aad0-7ac54c58e5f4/listen",
#                 "controlUrl": "https://phone-call-websocket.aws-us-west-2-backend-production2.vapi.ai/1e9893d4-d71b-455f-aad0-7ac54c58e5f4/control"
#             },
#             "transport": {"assistantVideoEnabled": False},
#             "webCallUrl": "https://vapi.daily.co/d4U8OXMj9EiDwFsKqMyC",
#             "status": "queued",
#             "assistantId": "b33d016a-db85-4e34-801b-5f7a175a077e",
#             "assistantOverrides": {"clientMessages": ["transfer-update", "transcript"]}
#         },
#         "assistant": {
#             "id": "b33d016a-db85-4e34-801b-5f7a175a077e",
#             "orgId": "bf389f00-a6ab-4e59-b031-fb09510545d1",
#             "name": "Groq Custom LLM Webhook",
#             "voice": {
#                 "model": "sonic-english",
#                 "voiceId": "248be419-c632-4f23-adf1-5324ed7dbf1d",
#                 "provider": "cartesia",
#                 "fillerInjectionEnabled": False
#             },
#             "createdAt": "2024-12-23T21:02:04.662Z",
#             "updatedAt": "2024-12-29T04:55:12.518Z",
#             "model": {
#                 "url": "https://remotely-trusty-sole.ngrok-free.app/api/custom-llm/",
#                 "model": "gpt-3.5-turbo",
#                 "toolIds": ["14b85a80-946c-4f66-a123-b2b557a6b7af"],
#                 "messages": [{"role": "system", "content": "You are a Personal Learning and Implementation Assistant..."}],
#                 "provider": "custom-llm",
#                 "temperature": 0.7,
#                 "emotionRecognitionEnabled": True,
#                 "tools": [{"id": "14b85a80-946c-4f66-a123-b2b557a6b7af"}]
#             }
#         }
#     }

#     try:
#         validated_payload = ConversationUpdate.model_validate(payload)
#         print("Validation successful! Here is the parsed object:")
#         print(validated_payload.model_dump_json(indent=4))
#     except Exception as e:
#         print("Validation failed with error:", e)

