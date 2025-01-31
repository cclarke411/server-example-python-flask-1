from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Union

class Message(BaseModel):
    role: str
    message: Optional[str] = None
    content: Optional[str] = None
    time: Optional[int] = None
    secondsFromStart: Optional[Union[float, int]] = None
    endTime: Optional[int] = None
    duration: Optional[int] = None
    source: Optional[str] = None

class ArtifactData(BaseModel):
    messages: List[Message]
    messagesOpenAIFormatted: List[Message]

class FunctionParameters(BaseModel):
    type: str
    required: Optional[List[str]] = None
    properties: Dict

class Function(BaseModel):
    name: str
    async_: bool = Field(alias='async')
    parameters: FunctionParameters
    description: str

class Tool(BaseModel):
    id: str
    createdAt: str
    updatedAt: str
    type: str
    function: Function
    orgId: str
    server: Dict
    async_: bool = Field(alias='async')

class Model(BaseModel):
    url: str
    model: str
    toolIds: List[str]
    messages: List[Message]
    provider: str
    temperature: float
    emotionRecognitionEnabled: bool
    tools: List[Tool]

class Voice(BaseModel):
    model: str
    voiceId: str
    provider: str
    fillerInjectionEnabled: bool

class Transcriber(BaseModel):
    model: str
    language: str
    provider: str

class Metadata(BaseModel):
    email: str
    user_id: str

class MessagePlan(BaseModel):
    idleMessages: List[str]

class StartSpeakingPlan(BaseModel):
    smartEndpointingEnabled: bool

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
    assistantOverrides: Dict

class Assistant(BaseModel):
    id: str
    orgId: str
    name: str
    voice: Voice
    createdAt: str
    updatedAt: str
    model: Model
    firstMessage: str
    transcriber: Transcriber
    silenceTimeoutSeconds: int
    clientMessages: List[str]
    serverMessages: List[str]
    serverUrl: str
    maxDurationSeconds: int
    metadata: Metadata
    backgroundSound: str
    backchannelingEnabled: bool
    backgroundDenoisingEnabled: bool
    messagePlan: MessagePlan
    startSpeakingPlan: StartSpeakingPlan

class Transcript(BaseModel):
    timestamp: int
    type: str
    role: str
    transcriptType: str
    transcript: str
    artifact: ArtifactData
    call: Call
    assistant: Assistant
    
# transcript = {'timestamp': 1735580379014, 'type': 'transcript', 'role': 'assistant', 'transcriptType': 'final', 'transcript': 'Hello?', 'artifact': {'messages': [{'role': 'system', 'message': 'You are a Personal Learning and Implementation Assistant with specialized knowledge of Atomic Habits by James Clear. Your role is to engage in meaningful and goal-oriented conversations with the user while leveraging your unique capabilities and tools to enhance their learning and personal growth. You aim to help the user understand and apply the principles from Atomic Habits in their life or other areas they are interested in.\n\nEngagement Guidelines:\nConversational Flow:\n\nAlways respond in a natural and friendly tone.\nDo not explicitly mention background activities, tools, or systems unless the user explicitly asks about them.\nIf the user expresses gratitude or contributes something helpful, acknowledge it and continue naturally.\nGoal-Oriented Assistance:\n\nIf the user expresses interest in achieving a goal, prompt them for:\nA clear definition of their goal.\nA timeline for achieving the goal.\nAny resources or support they feel they might need.\nUse this information to plan and assist th...', 'time': 1735580370550, 'secondsFromStart': 0}, {'role': 'bot', 'message': 'Hi there.', 'time': 1735580372255, 'endTime': 1735580372995, 'secondsFromStart': 1.36, 'duration': 740, 'source': ''}, {'role': 'user', 'message': 'Hi.', 'time': 1735580373535, 'endTime': 1735580374035, 'secondsFromStart': 2.6399999, 'duration': 500}], 'messagesOpenAIFormatted': [{'role': 'system', 'content': 'You are a Personal Learning and Implementation Assistant with specialized knowledge of Atomic Habits by James Clear. Your role is to engage in meaningful and goal-oriented conversations with the user while leveraging your unique capabilities and tools to enhance their learning and personal growth. You aim to help the user understand and apply the principles from Atomic Habits in their life or other areas they are interested in.\n\nEngagement Guidelines:\nConversational Flow:\n\nAlways respond in a natural and friendly tone.\nDo not explicitly mention background activities, tools, or systems unless the user explicitly asks about them.\nIf the user expresses gratitude or contributes something helpful, acknowledge it and continue naturally.\nGoal-Oriented Assistance:\n\nIf the user expresses interest in achieving a goal, prompt them for:\nA clear definition of their goal.\nA timeline for achieving the goal.\nAny resources or support they feel they might need.\nUse this information to plan and assist th...'}, {'role': 'assistant', 'content': 'Hi there.'}, {'role': 'user', 'content': 'Hi.'}]}, 'call': {'id': '07587321-0342-4e16-94ed-15e2a53792ae', 'orgId': 'bf389f00-a6ab-4e59-b031-fb09510545d1', 'createdAt': '2024-12-30T17:39:29.461Z', 'updatedAt': '2024-12-30T17:39:29.461Z', 'type': 'webCall', 'monitor': {'listenUrl': 'wss://phone-call-websocket.aws-us-west-2-backend-production3.vapi.ai/07587321-0342-4e16-94ed-15e2a53792ae/listen', 'controlUrl': 'https://phone-call-websocket.aws-us-west-2-backend-production3.vapi.ai/07587321-0342-4e16-94ed-15e2a53792ae/control'}, 'transport': {'assistantVideoEnabled': False}, 'webCallUrl': 'https://vapi.daily.co/HbEP08zl8HDPBBLBZxf4', 'status': 'queued', 'assistantId': 'b33d016a-db85-4e34-801b-5f7a175a077e', 'assistantOverrides': {'clientMessages': ['transfer-update', 'transcript']}}, 'assistant': {'id': 'b33d016a-db85-4e34-801b-5f7a175a077e', 'orgId': 'bf389f00-a6ab-4e59-b031-fb09510545d1', 'name': 'Groq Custom LLM Webhook', 'voice': {'model': 'sonic-english', 'voiceId': '248be419-c632-4f23-adf1-5324ed7dbf1d', 'provider': 'cartesia', 'fillerInjectionEnabled': False}, 'createdAt': '2024-12-23T21:02:04.662Z', 'updatedAt': '2024-12-30T17:38:37.692Z', 'model': {'url': 'https://remotely-trusty-sole.ngrok-free.app/api/custom-llm/', 'model': 'gpt-3.5-turbo', 'toolIds': ['14b85a80-946c-4f66-a123-b2b557a6b7af', 'ddd4a044-84bd-404f-8317-99348eae3afa', 'ff2e0213-5b7e-492e-9670-b2772f15da5b'], 'messages': [{'role': 'system', 'content': 'You are a Personal Learning and Implementation Assistant with specialized knowledge of Atomic Habits by James Clear. Your role is to engage in meaningful and goal-oriented conversations with the user while leveraging your unique capabilities and tools to enhance their learning and personal growth. You aim to help the user understand and apply the principles from Atomic Habits in their life or other areas they are interested in.\n\nEngagement Guidelines:\nConversational Flow:\n\nAlways respond in a natural and friendly tone.\nDo not explicitly mention background activities, tools, or systems unless the user explicitly asks about them.\nIf the user expresses gratitude or contributes something helpful, acknowledge it and continue naturally.\nGoal-Oriented Assistance:\n\nIf the user expresses interest in achieving a goal, prompt them for:\nA clear definition of their goal.\nA timeline for achieving the goal.\nAny resources or support they feel they might need.\nUse this information to plan and assist them.\nKnowledge of Atomic Habits:\n\nDraw on principles from Atomic Habits to guide and inspire the user. For example:\nHabit stacking.\nThe Four Laws of Behavior Change.\nThe Two-Minute Rule.\nIdentity-based habits.\nDiscuss and explain these principles before implementing a solution using tools.\nLearning Support:\n\nAssist the user in exploring concepts, answering questions, and providing summaries or actionable insights from the book.\nTailor responses to the user\'s level of familiarity with the content.\nResource Navigation:\n\nHelp the user explore related tools and resources, such as:\nA scheduler tool for creating actionable plans and timelines.\nA finalize details tool for organizing key information or strategies.\nOther specialized tools that help in goal tracking, data retrieval, or habit monitoring.\nSeamless Tool Integration:\n\nUse tools intuitively during the conversation, ensuring that their use feels like a natural extension of the interaction.\nFor instance:\nBefore scheduling a habit, guide the user through understanding the Atomic Habits principles that underpin the habit.\nLeverage your RAG (retrieval-augmented generation) knowledge system to provide detailed insights.\nKey Goals:\nProvide educational support and actionable insights on Atomic Habits.\nHelp users clarify and implement their personal and professional goals.\nSeamlessly integrate tools to add value and enhance user outcomes.\nMaintain a clear separation of concerns by using tools effectively and only when required, ensuring the conversation remains focused and engaging.\nExample Behavior:\nIf the user says:\n\n"I\'d like to develop a habit of reading daily," your response might include:\nA walkthrough of relevant Atomic Habits concepts, such as habit stacking or the Two-Minute Rule.\nClarifying the user’s goal (e.g., how much time they’d like to read daily, what types of books they enjoy).\nUsing the scheduler tool to set up a reading schedule.\nUsing the finalize details tool to summarize the user’s plan.\nIf the user simply engages in casual conversation:\n\nStay conversational and helpful, navigating the discussion naturally without invoking tools unnecessarily.\nCapabilities:\nAtomic Habits Knowledge Base: Deep understanding and ability to retrieve insights from the book Atomic Habits.\nScheduler Tool: Create structured plans, reminders, and timelines for user goals.\nFinalize Details Tool: Organize and refine key information or strategies.\nRAG System: Access to retrieval-augmented generation for in-depth answers.\nAdaptability: Flexibility to interact with tools in combination to meet complex user needs.\nBy maintaining these principles, you can effectively guide the user in both understanding and achieving their goals while fostering a conversational and engaging experience.'}], 'provider': 'custom-llm', 'temperature': 0.7, 'emotionRecognitionEnabled': True, 'tools': [{'id': '14b85a80-946c-4f66-a123-b2b557a6b7af', 'createdAt': '2024-12-23T20:19:15.305Z', 'updatedAt': '2024-12-26T16:52:05.385Z', 'type': 'function', 'function': {'name': 'collect_user_info', 'async': False, 'parameters': {'type': 'object', 'required': ['key', 'value'], 'properties': {'key': {'type': 'string', 'description': "The category or type of personal information provided by the user (e.g., 'username', 'preference', 'email', etc.)."}, 'value': {'type': 'string', 'description': '"The actual information provided by the user (e.g., \'John Doe\', \'likes pizza\', \'john.doe@example.com\')."'}}}, 'description': 'Collects key-value pair information when a user volunteers personal or preference data.'}, 'orgId': 'bf389f00-a6ab-4e59-b031-fb09510545d1', 'server': {'url': 'https://remotely-trusty-sole.ngrok-free.app/api/webhook/'}, 'async': True}, {'id': 'ddd4a044-84bd-404f-8317-99348eae3afa', 'createdAt': '2024-11-08T02:11:18.743Z', 'updatedAt': '2024-12-26T16:53:25.922Z', 'type': 'function', 'function': {'name': 'finalizeDetails', 'async': False, 'parameters': {'type': 'object', 'required': ['question'], 'properties': {'answer': {'type': 'string', 'description': 'The users answer'}, 'question': {'type': 'string', 'description': 'The interviewer question'}}}, 'description': 'Whenever there are questions being asked by the assistant to the user then this function should be called. It should get the question being asked and the answer obtained from the user as a dictionary of two key value pairs:\n{"question": "What is your name",\n\'answer": "Clyde"} for example '}, 'orgId': 'bf389f00-a6ab-4e59-b031-fb09510545d1', 'server': {'url': 'https://remotely-trusty-sole.ngrok-free.app/api/webhook/'}, 'async': False}, {'id': 'ff2e0213-5b7e-492e-9670-b2772f15da5b', 'createdAt': '2024-12-24T19:27:38.544Z', 'updatedAt': '2024-12-26T16:51:52.960Z', 'type': 'function', 'function': {'name': 'schedule_clickup', 'async': False, 'parameters': {'type': 'object', 'properties': {'goal': {'type': 'string', 'description': 'A description of the user goals'}, 'timeline': {'type': 'string', 'description': 'A description of over what timeline the user will expect to carry out the project'}, 'resources': {'type': 'string', 'description': 'A list of any special resources needed by the user to accomplish their goal'}}}, 'description': 'Tool Description:\n\nThis tool leverages a large language model (LLM) and the Pydantic library to generate a ClickUp-compatible schedule based on user input.\n\nKey Features:\n\nUser-Friendly Input: Users provide a high-level goal or objective (e.g., "Write a research paper," "Plan a vacation," "Prepare for an exam").\nFlexible Input: Users can optionally provide additional context such as timelines, available resources, and personal preferences.\nIntelligent Schedule Generation: The LLM analyzes the user input and generates a schedule that:\nBreaks down the goal into smaller, actionable tasks.\nCreates a logical sequence of tasks with appropriate dependencies.\nAssigns realistic start and due dates for each task.\nOrganizes tasks into relevant lists within ClickUp.\nOptionally, creates subtasks for more complex tasks.'}, 'orgId': 'bf389f00-a6ab-4e59-b031-fb09510545d1', 'server': {'url': 'https://remotely-trusty-sole.ngrok-free.app/api/webhook/'}, 'async': False}]}, 'firstMessage': 'Hi there! ', 'transcriber': {'model': 'nova-2', 'language': 'en', 'provider': 'deepgram'}, 'silenceTimeoutSeconds': 2689, 'clientMessages': ['transcript', 'hang', 'function-call', 'speech-update', 'metadata', 'transfer-update', 'conversation-update'], 'serverMessages': ['conversation-update', 'end-of-call-report', 'function-call', 'hang', 'model-output', 'phone-call-control', 'speech-update', 'status-update', 'transcript', 'tool-calls', 'transfer-destination-request', 'user-interrupted', 'voice-input'], 'serverUrl': 'https://remotely-trusty-sole.ngrok-free.app/api/webhook/', 'maxDurationSeconds': 43200, 'metadata': {'email': 'fake_email@yamama.com', 'user_id': 'fake_user_id'}, 'backgroundSound': 'off', 'backchannelingEnabled': False, 'backgroundDenoisingEnabled': False, 'messagePlan': {'idleMessages': ['Are you still there?']}, 'startSpeakingPlan': {'smartEndpointingEnabled': True}}}
# Transcript.model_validate(transcript)

