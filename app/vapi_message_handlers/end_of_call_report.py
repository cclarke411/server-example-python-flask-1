from pydantic import BaseModel, Field
from typing import Literal, List, Optional, Dict, Union

class Analysis(BaseModel):
    summary: str
    successEvaluation: str

class Message(BaseModel):
    role: Literal['system', 'bot', 'user']
    message: str
    time: Optional[int] = None
    endTime: Optional[int] = None
    secondsFromStart: Optional[float] = None
    duration: Optional[float] = None
    source: Optional[str] = None

class Artifact(BaseModel):
    messages: List[Message]
    messagesOpenAIFormatted: List[Dict[str, str]]
    transcript: str
    recordingUrl: Optional[str] = None
    stereoRecordingUrl: Optional[str] = None

class CostBreakdown(BaseModel):
    stt: float
    llm: float
    tts: float
    vapi: float
    total: float
    llmPromptTokens: int
    llmCompletionTokens: int
    ttsCharacters: int
    analysisCostBreakdown: Dict[str, float]

class Cost(BaseModel):
    type: str
    cost: float
    minutes: Optional[float] = None
    model: Optional[Dict[str, str]] = None
    transcriber: Optional[Dict[str, str]] = None
    voice: Optional[Dict[str, str]] = None
    subType: Optional[str] = None
    analysisType: Optional[str] = None

class EndOfCallMessage(BaseModel):
    timestamp: int
    type: Literal['end-of-call-report']

class EndOfCallReport(BaseModel):
    message: EndOfCallMessage
    analysis: Analysis
    artifact: Artifact
    startedAt: str
    endedAt: str
    endedReason: str
    cost: float
    costBreakdown: CostBreakdown
    costs: List[Cost]
    durationMs: int
    durationSeconds: float
    durationMinutes: float

# Example Usage
# if __name__ == "__main__":
#     payload = {
#         "message": {"timestamp": 1731437694251, "type": "end-of-call-report"},
#         "timestamp": 1731437694251,
#         "type": "end-of-call-report",
#         "analysis": {
#             "summary": "The call introduces \"Atomic Habits,\" a guide that explains how small changes can lead to significant long-term results.",
#             "successEvaluation": "false"
#         },
#         "artifact": {
#             "messages": [
#                 {
#                     "role": "system",
#                     "message": "You are a highly skilled assistant...",
#                     "time": 1731437673073,
#                     "secondsFromStart": 0
#                 },
#                 {
#                     "role": "bot",
#                     "message": "Welcome to Atomic Habits...",
#                     "time": 1731437674506,
#                     "endTime": 1731437680436,
#                     "secondsFromStart": 1.36,
#                     "duration": 5560.000244140625,
#                     "source": ""
#                 },
#                 {
#                     "role": "user",
#                     "message": "Hello?",
#                     "time": 1731437684106,
#                     "endTime": 1731437684606,
#                     "secondsFromStart": 10.96,
#                     "duration": 500
#                 }
#             ],
#             "messagesOpenAIFormatted": [
#                 {"role": "system", "content": "You are a highly skilled assistant..."},
#                 {"role": "assistant", "content": "Welcome to Atomic Habits..."},
#                 {"role": "user", "content": "Hello?"}
#             ],
#             "transcript": "AI: Welcome to Atomic Habits...\nUser: Hello?",
#             "recordingUrl": "https://example.com/recording.wav",
#             "stereoRecordingUrl": "https://example.com/stereo_recording.wav"
#         },
#         "startedAt": "2024-11-12T18:54:34.972Z",
#         "endedAt": "2024-11-12T18:54:49.158Z",
#         "endedReason": "pipeline-error-custom-llm-llm-failed",
#         "cost": 0.0192,
#         "costBreakdown": {
#             "stt": 0.0033,
#             "llm": 0.0,
#             "tts": 0.0,
#             "vapi": 0.0118,
#             "total": 0.0192,
#             "llmPromptTokens": 0,
#             "llmCompletionTokens": 0,
#             "ttsCharacters": 0,
#             "analysisCostBreakdown": {
#                 "summary": 0.001,
#                 "successEvaluation": 0.0031
#             }
#         },
#         "costs": [
#             {"type": "transcriber", "cost": 0.0033, "minutes": 0.3065, "transcriber": {"provider": "deepgram", "model": "nova-2"}},
#             {"type": "vapi", "cost": 0.0118, "minutes": 0.2364}
#         ],
#         "durationMs": 14186,
#         "durationSeconds": 14.186,
#         "durationMinutes": 0.2364
#     }

#     try:
#         validated_payload = EndOfCallReport.model_validate(payload)
#         print("Validation successful! Here is the parsed object:")
#         print(validated_payload.model_dump_json(indent=4))
#     except Exception as e:
#         print("Validation failed with error:", e)
