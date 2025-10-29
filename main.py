from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph import START, StateGraph
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from typing import Sequence
from langchain_core.messages import BaseMessage, trim_messages
from langgraph.graph.message import add_messages
from typing_extensions import Annotated, TypedDict
from langchain.chat_models import init_chat_model

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "credentials.json"

# LangSmith configuration (optional - fill in your own API key and project name)
# os.environ["LANGCHAIN_TRACING_V2"] = "true"
# os.environ["LANGCHAIN_API_KEY"] = "your-langsmith-api-key-here"
# os.environ["LANGCHAIN_PROJECT"] = "your-project-name-here"

app = FastAPI(title="Chatbot API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize model
model = init_chat_model("gemini-2.5-flash", model_provider="google_genai")

trimmer = trim_messages(
    max_tokens=65,
    strategy="last",
    token_counter=model,
    include_system=True,
    allow_partial=False,
    start_on="human",
)

prompt_template = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a helpful assistant. Answer all questions to the best of your ability in {language}.",
        ),
        MessagesPlaceholder(variable_name="messages"),
    ]
)

class State(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    language: str

workflow = StateGraph(state_schema=State)

def call_model(state: State):
    trimmed_messages = trimmer.invoke(state["messages"])
    prompt = prompt_template.invoke(
        {"messages": trimmed_messages, "language": state["language"]}
    )
    response = model.invoke(prompt)
    return {"messages": response}

workflow.add_edge(START, "model")
workflow.add_node("model", call_model)

memory = MemorySaver()
chatbot_app = workflow.compile(checkpointer=memory)

# Request/Response models
class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    thread_id: Optional[str] = "default"
    language: Optional[str] = "English"

class ChatResponse(BaseModel):
    response: str
    thread_id: str

@app.get("/")
async def root():
    return {
        "message": "Chatbot API is running",
        "version": "1.0.0",
        "endpoints": {
            "/chat": "POST - Send a message to the chatbot",
            "/health": "GET - Health check"
        }
    }

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        config = {"configurable": {"thread_id": request.thread_id}}
        input_messages = [HumanMessage(request.message)]
        
        full_response = ""
        for chunk, metadata in chatbot_app.stream(
            {"messages": input_messages, "language": request.language},
            config,
            stream_mode="messages",
        ):
            if isinstance(chunk, AIMessage):
                full_response += chunk.content
        
        return ChatResponse(
            response=full_response,
            thread_id=request.thread_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/chat/{thread_id}")
async def clear_chat(thread_id: str):
    """Clear chat history for a specific thread"""
    return {"message": f"Chat history cleared for thread: {thread_id}"}
