import streamlit as st
import os
from pathlib import Path
from sqlalchemy import create_engine
from dotenv import load_dotenv

# LLM & Agent
from langchain_groq import ChatGroq
from langchain_community.agent_toolkits.sql.base import create_sql_agent, SQLDatabaseToolkit
from langchain_community.utilities import SQLDatabase
from langchain_core.callbacks.base import BaseCallbackHandler


# --- CUSTOM STREAMLIT CALLBACK HANDLER ---
class StreamlitCallbackHandler(BaseCallbackHandler):
    def __init__(self, container):
        self.container = container
        self.text = ""

    def on_llm_new_token(self, token: str, **kwargs):
        self.text += token
        self.container.markdown(self.text)


# --- PAGE CONFIG ---
st.set_page_config(page_title="Chat with Company DB", page_icon="💬", layout="wide")
st.title("💬 Alpha Assist")


# --- LOAD ENV ---
load_dotenv()
api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    st.error("⚠️ GROQ_API_KEY missing.")
    st.stop()


# --- MODEL ---
model_name = "llama-3.3-70b-versatile"
llm = ChatGroq(groq_api_key=api_key, model=model_name, streaming=True)


# --- DATABASE ---
@st.cache_resource(ttl="2h")
def configur_db():
    dbfilepath = (Path(__file__).parent / "company.db").absolute()
    return SQLDatabase(create_engine(f"sqlite:///{dbfilepath}", connect_args={"uri": True}))

db = configur_db()


# --- SQL AGENT ---
toolkit = SQLDatabaseToolkit(db=db, llm=llm)
agent = create_sql_agent(
    llm=llm,
    toolkit=toolkit,
    verbose=True,
    agent_type="zero-shot-react-description",
    handle_parsing_errors=True
)


# --- STYLING ---
st.markdown("""
<style>
.chat-left { background-color: #dbeafe; padding: 10px; border-radius: 10px; }
.chat-right { background-color: #e0f2fe; padding: 10px; border-radius: 10px; margin-left: auto; }
</style>
""", unsafe_allow_html=True)


# --- INITIAL CHAT ---
if "messages" not in st.session_state:
    st.session_state["messages"] = [
        {"role": "assistant", "content": "👋 How can I help you with your Company DB today?"}
    ]


# --- SHOW CHAT ---
for msg in st.session_state["messages"]:
    if msg["role"] == "user":
        st.markdown(f'<div class="chat-right">{msg["content"]}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="chat-left">{msg["content"]}</div>', unsafe_allow_html=True)


# --- USER INPUT ---
user_query = st.chat_input("Ask anything about the company DB")

if user_query:
    st.session_state["messages"].append({"role": "user", "content": user_query})
    st.markdown(f'<div class="chat-right">{user_query}</div>', unsafe_allow_html=True)

    with st.chat_message("assistant"):
        container = st.empty()
        callback = StreamlitCallbackHandler(container)

        try:
            result = agent.invoke({"input": user_query}, callbacks=[callback])
            response = result["output"]
        except:
            response = "⚠️ Something went wrong."

        st.session_state["messages"].append({"role": "assistant", "content": response})
        container.markdown(f'<div class="chat-left">{response}</div>', unsafe_allow_html=True)
