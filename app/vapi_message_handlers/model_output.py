from pydantic import BaseModel, Field, AnyUrl
from typing import List, Optional, Dict, Any
from datetime import datetime

# Models for inner structures
class FunctionParameters(BaseModel):
    type: str
    required: List[str]
    properties: Dict[str, Any]

class Function(BaseModel):
    name: str
    description: str
    parameters: FunctionParameters

class Tool(BaseModel):
    type: str
    function: Function

class Message(BaseModel):
    role: str
    content: str

class Monitor(BaseModel):
    listenUrl: AnyUrl  # Changed to AnyUrl to support wss
    controlUrl: AnyUrl  # Changed to AnyUrl to support wss

class Transport(BaseModel):
    assistantVideoEnabled: bool

class Call(BaseModel):
    id: str
    orgId: str
    createdAt: datetime
    updatedAt: datetime
    type: str
    monitor: Monitor
    transport: Transport
    webCallUrl: AnyUrl
    status: str
    assistantId: str
    assistantOverrides: Dict[str, List[str]]

class Credential(BaseModel):
    id: str
    orgId: str
    provider: str
    createdAt: datetime
    updatedAt: datetime
    apiKey: Optional[str]
    userId: Optional[str]

class Metadata(BaseModel):
    email: str  # Changed from EmailStr to str for compatibility
    user_id: str

# Main payload model
class ModelOutput(BaseModel):
    model: str
    messages: List[Message]
    temperature: float
    tools: List[Tool]
    stream: bool
    max_tokens: int
    call: Call
    metadata: Metadata
    credentials: List[Credential]

# Example Usage
# if __name__ == "__main__":
#     import json

#     # Example payload as a dictionary (parsed from the JSON you provided)
#     payload_dict = {
#         "model": "gpt-3.5-turbo",
#         "messages": [
#             {"role": "system", "content": "Just say hi and have a conversation with the user."},
#             {"role": "assistant", "content": "Hello."},
#             {"role": "user", "content": "Hi."},
#         ],
#         "temperature": 0.7,
#         "tools": [
#             {
#                 "type": "function",
#                 "function": {
#                     "name": "collect_user_info",
#                     "description": "Collects key-value pair information when a user volunteers personal or preference data.",
#                     "parameters": {
#                         "type": "object",
#                         "required": ["key", "value"],
#                         "properties": {
#                             "key": {
#                                 "type": "string",
#                                 "description": "The category or type of personal information provided by the user."
#                             },
#                             "value": {
#                                 "type": "string",
#                                 "description": "The actual information provided by the user."
#                             }
#                         }
#                     }
#                 }
#             }
#         ],
#         "stream": True,
#         "max_tokens": 250,
#         "call": {
#             "id": "01a8c996-ce9b-4aa3-9ad3-173d2a378776",
#             "orgId": "bf389f00-a6ab-4e59-b031-fb09510545d1",
#             "createdAt": "2024-12-26T20:10:25.385Z",
#             "updatedAt": "2024-12-26T20:10:25.385Z",
#             "type": "webCall",
#             "monitor": {
#                 "listenUrl": "wss://phone-call-websocket.aws-us-west-2-backend-production2.vapi.ai/01a8c996-ce9b-4aa3-9ad3-173d2a378776/listen",
#                 "controlUrl": "https://phone-call-websocket.aws-us-west-2-backend-production2.vapi.ai/01a8c996-ce9b-4aa3-9ad3-173d2a378776/control"
#             },
#             "transport": {"assistantVideoEnabled": False},
#             "webCallUrl": "https://vapi.daily.co/QLo5PHhQUqBr2eUK0zhb",
#             "status": "queued",
#             "assistantId": "b33d016a-db85-4e34-801b-5f7a175a077e",
#             "assistantOverrides": {"clientMessages": ["transfer-update", "transcript"]}
#         },
#         "metadata": {
#             "email": "fake_email@yamama.com",
#             "user_id": "fake_user_id"
#         },
#         "credentials": [
#             {
#                 "id": "368196a6-3a9a-4474-8b02-126cb4b94117",
#                 "orgId": "bf389f00-a6ab-4e59-b031-fb09510545d1",
#                 "provider": "custom-llm",
#                 "createdAt": "2024-05-12T02:27:18.293Z",
#                 "updatedAt": "2024-05-12T02:27:18.293Z",
#                 "apiKey": "2gIG1X7WB8n2XeV6mdMPV0y90vm_4NCf3npu38H7peCMCmdYe",
#                 "userId": None
#             }
#         ]
#     }

#     # Parse and validate the payload
#     payload = VAPIPayload.model_validate(payload_dict)

#     # Access specific fields
#     print(payload)
#     print(payload.messages)  # Output: gpt-3.5-turbo
#     print(payload.call.monitor.listenUrl)  # Output: wss://...
#     print(payload.tools[0].function.name)  # Output: collect_user_info

