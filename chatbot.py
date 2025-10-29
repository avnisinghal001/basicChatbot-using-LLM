import streamlit as st
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

@st.cache_resource
def get_app():
    memory = MemorySaver()
    return workflow.compile(checkpointer=memory)

st.set_page_config(page_title="Chatbot", page_icon="💬", layout="wide")

st.markdown("""
    <style>
    .stApp {
        max-width: 900px;
        margin: 0 auto;
    }
    .stTextInput > div > div > input {
        background-color: #f0f4f9;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("💬 Chatbot")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Message Chatbot"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        app = get_app()
        config = {"configurable": {"thread_id": "abc234"}}
        
        input_messages = [HumanMessage(prompt)]
        for chunk, metadata in app.stream(
            {"messages": input_messages, "language": "English"},
            config,
            stream_mode="messages",
        ):
            if isinstance(chunk, AIMessage):
                full_response += chunk.content
                message_placeholder.markdown(full_response + "▌")
        
        message_placeholder.markdown(full_response)
    
    st.session_state.messages.append({"role": "assistant", "content": full_response})
