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
    """Custom Streamlit callback handler for streaming responses."""
    def __init__(self, container):
        self.container = container
        self.text = ""

    def on_llm_new_token(self, token: str, **kwargs):
        """Stream tokens in real-time to Streamlit container."""
        self.text += token
        self.container.markdown(self.text)


# --- PAGE CONFIG ---
st.set_page_config(page_title=" Chat with Company DB", page_icon="💬", layout="wide")
st.title("💬  Chat with Company DB")


# --- LOAD ENV ---
load_dotenv()
api_key = os.getenv("GROQ_API_KEY")

# --- VALIDATION ---
if not api_key:
    st.error("⚠️ GROQ_API_KEY missing in environment variables.")
    st.stop()


# --- MODEL SELECTION ---
model_options = ["llama-3.3-70b-versatile"]
selected_model = st.sidebar.selectbox("🧠  Model Using ", options=model_options, index=0)




# --- LLM CONFIG ---
llm = ChatGroq(
    groq_api_key=api_key,
    model=selected_model,
    streaming=True
)


# --- DATABASE CONFIG (SQLite only) ---
@st.cache_resource(ttl="2h")
def configur_db():
    dbfilepath = (Path(__file__).parent / "company.db").absolute()
    return SQLDatabase(create_engine(f"sqlite:///{dbfilepath}", connect_args={"uri": True}))

db = configur_db()


# --- TOOLKIT AND AGENT ---
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
/* === SIDEBAR === */
[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #4338ca, #7c3aed); /* Dark purple gradient */
  border-right: 2px solid #a5b4fc;
}

[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] p {
  color: #f9fafb !important; /* Soft white text */
  font-weight: 600;
}

/* Sidebar selectbox */
[data-testid="stSidebar"] label {
  color: #ffffff !important;
  font-size: 18px !important;
  font-weight: 700;
}

/* Sidebar clear history button */
[data-testid="stSidebar"] button[kind="secondary"] {
  color: #f9fafb !important;
  background-color: transparent !important;
  border: 2px solid #f9fafb !important;
  font-weight: 600 !important;
  border-radius: 8px !important;
}
[data-testid="stSidebar"] button[kind="secondary"]:hover {
  background-color: rgba(255, 255, 255, 0.15) !important;
}

/* Sidebar help expander header (like black button) */
[data-testid="stSidebar"] [data-testid="stExpander"] > div[role="button"] {
    background-color: #000000 !important; /* Black background */
    color: #ffffff !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    padding: 10px 12px !important;
    border: 1px solid #f9fafb !important;
}
[data-testid="stSidebar"] [data-testid="stExpander"] > div[role="button"]:hover {
    background-color: rgba(255, 255, 255, 0.15) !important;
}

/* Sidebar help expander content */
[data-testid="stSidebar"] [data-testid="stExpander"] div[data-testid="stMarkdownContainer"] {
    background-color: rgba(0, 0, 0, 0.2) !important; /* Dark transparent bg */
    color: #f1f5f9 !important;
    padding: 12px !important;
    border-radius: 8px !important;
    margin-top: 5px;
}

/* Chat bubbles */
.chat-left {
  background-color: #dbeafe !important;  /* assistant bubble */
  color: #1e3a8a !important;
  border-radius: 10px;
  padding: 10px 15px;
  margin: 5px 0;
  max-width: 70%;
  text-align: left;
}

.chat-right {
  background-color: #e0f2fe !important;  /* user bubble */
  color: #1e3a8a !important;
  border-radius: 10px;
  padding: 10px 15px;
  margin: 5px 0;
  max-width: 70%;
  text-align: left;
  margin-left: auto;
}

/* Main page title */
h1, h2, h3, h4 {
  color: #2563eb;
  font-size: 1.8rem;
}
</style>
<hr style="border: none; height: 2px; background: #dbeafe; margin-top: -10px; margin-bottom: 20px">
""", unsafe_allow_html=True)


# --- INITIAL CHAT SESSION ---
if "messages" not in st.session_state or st.sidebar.button("🧹 Clear message history"):
    st.session_state["messages"] = [
        {"role": "assistant", "content": (
            "👋 How can I help you with your Company database today?\n\n"
        )}
    ]
    
# --- EXAMPLE QUESTIONS ---
st.sidebar.markdown("**💡 Example Questions:**")
st.sidebar.markdown(
    "- Show all employees list in the  company.db  \n"
    "- Name all the departments in the company \n"
    "- How many employees are there in the compnay \n"
    "- Name the employee who has highest salary"
    
)



# --- DISPLAY CHAT HISTORY ---
for msg in st.session_state["messages"]:
    if msg["role"] == "user":
        st.markdown(f'<div class="chat-right">{msg["content"]}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="chat-left">{msg["content"]}</div>', unsafe_allow_html=True)


# --- USER INPUT ---
user_query = st.chat_input(placeholder="Ask anything About  Company ")

if user_query:
    st.session_state["messages"].append({"role": "user", "content": user_query})
    st.markdown(f'<div class="chat-right">{user_query}</div>', unsafe_allow_html=True)

    response = None
    forbidden_commands = ["DROP", "DELETE", "UPDATE", "ALTER", "INSERT"]

    if any(cmd in user_query.upper() for cmd in forbidden_commands):
        st.warning("⚠️ Destructive queries are not allowed.")
    else:
        with st.chat_message("assistant"):
            st_callback_container = st.empty()
            streamlit_callback = StreamlitCallbackHandler(st_callback_container)
            try:
                response_dict = agent.invoke({"input": user_query}, callbacks=[streamlit_callback])
                response = response_dict["output"]
            except Exception as e:
                if "token limit" in str(e).lower():
                    st.warning("⚠️ Token limit reached. Please visit after some time ")
                else:
                    response = "⚠️ Token limit reached. Please visit after some time"
                   
               

    if response:
        st.session_state["messages"].append({"role": "assistant", "content": response})
        st_callback_container.markdown(f'<div class="chat-left">{response}</div>', unsafe_allow_html=True)

















