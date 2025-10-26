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
st.set_page_config(page_title="AI Company Analyst", page_icon="💬", layout="wide")
st.title("💬 AI Company Analyst")


# --- LOAD ENV ---
load_dotenv()
api_key = os.getenv("GROQ_API_KEY")

# --- VALIDATION ---
if not api_key:
    st.error("⚠️ GROQ_API_KEY missing in environment variables.")
    st.stop()


# --- MODEL SELECTION ---
model_options = ["llama-3.3-70b-versatile"]
selected_model = st.sidebar.selectbox("🧠 Choose Model", options=model_options, index=0)


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
  background: linear-gradient(180deg, #4338ca, #7c3aed); /* Darker purple gradient */
  border-right: 2px solid #a5b4fc;
}
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] p {
  color: #f9fafb; /* Soft white text */
  font-weight: 600;
}

/* === SIDEBAR MODEL SELECTBOX === */
[data-testid="stSidebar"] label {
  color: #ffffff !important;
  font-size: 18px !important;
  font-weight: 700;
}

/* === SIDEBAR CLEAR HISTORY BUTTON === */
[data-testid="stSidebar"] button[kind="secondary"] {
  color: #f9fafb !important;
  background-color: transparent !important;
  border: 2px solid #f9fafb !important;
  font-weight: 600 !important;
  border-radius: 8px !important; /* Added rounded corners */
}
[data-testid="stSidebar"] button[kind="secondary"]:hover {
  background-color: rgba(255, 255, 255, 0.15) !important;
}

/* === SIDEBAR HELP EXPANDER === */
[data-testid="stSidebar"] [data-testid="stExpander"] > div[role="button"] {
    background-color: rgba(255, 255, 255, 0.1) !important; /* Light transparent bg */
    color: #ffffff !important;
    border: 1px solid #f9fafb !important; /* White border */
    border-radius: 8px !important;
    font-weight: 600 !important;
    padding: 10px 12px !important;
}
[data-testid="stSidebar"] [data-testid="stExpander"] > div[role="button"]:hover {
    background-color: rgba(255, 255, 255, 0.2) !important; /* Darker on hover */
}
[data-testid="stSidebar"] [data-testid="stExpander"] div[data-testid="stMarkdownContainer"] {
    background-color: rgba(0, 0, 0, 0.2) !important; /* Dark transparent bg */
    color: #f1f5f9 !important;
    padding: 12px !important;
    border-radius: 8px !important;
    margin-top: 5px;
}

/* === NATIVE CHAT BUBBLES (Replaces .chat-left/.chat-right) === */
[data-testid="stChatMessage"] {
    max-width: 70%;
    padding: 10px 15px;
    border-radius: 10px;
    margin-bottom: 5px;
}
/* User (Left) */
[data-testid="stChatMessage"][data-testid="chat-avatar-user"] {
    margin-right: auto;
    background-color: #e0f2fe;
    color: #1e3a8a;
}
/* Assistant (Right) */
[data-testid="stChatMessage"][data-testid="chat-avatar-assistant"] {
    margin-left: auto;
    background-color: #dbeafe;
    color: #1e3a8a;
}

/* === MAIN PAGE TITLE === */
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
        {"role": "assistant", "content": "👋 How can I help you with your company database today?"}
    ]


# --- HELP SECTION --
with st.sidebar.expander("ℹ️ How to use this chat", expanded=False):
    st.markdown("""
    <b>💡 You can ask questions like:</b><br>
    📊 <i>Show all employees in the Sales department</i><br>
    💰 <i>What is the average salary in each department?</i><br>
    👥 <i>Name the employee with highest salary</i><br>
    🏢 <i>How many departments does the company have?</i><br>
    ⏰ <i>Which employees have experience greater than 5 years?</i><br><br>

    <b>📝 Notes:</b><br>
    - Uses your <b>SQLite company.db</b> file.<br>
    - ❌ Commands like <code>DROP</code>, <code>DELETE</code>, <code>UPDATE</code>, <code>INSERT</code>, <code>ALTER</code> are blocked.<br>
    - ✅ Only <b>SELECT</b>-type (read-only) queries are allowed.<br>
    - 💬 Ask naturally — the AI converts English to SQL automatically.
    """, unsafe_allow_html=True)


# --- DISPLAY CHAT HISTORY ---
# (Updated to use native st.chat_message)
for msg in st.session_state["messages"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])


# --- USER INPUT ---
# (Updated to use native st.chat_message and cleaner logic)
user_query = st.chat_input(placeholder="Ask anything from the SQLite database...")

if user_query:
    # Add user message to session state and display it
    st.session_state["messages"].append({"role": "user", "content": user_query})
    with st.chat_message("user"):
        st.markdown(user_query)

    forbidden_commands = ["DROP", "DELETE", "UPDATE", "ALTER", "INSERT"]
    
    # Check for forbidden commands
    if any(cmd in user_query.upper() for cmd in forbidden_commands):
        response = "⚠️ Destructive queries are not allowed."
        with st.chat_message("assistant"):
            st.warning(response)
        st.session_state["messages"].append({"role": "assistant", "content": response})
    
    # If allowed, run the agent
    else:
        with st.chat_message("assistant"):
            st_callback_container = st.empty()
            streamlit_callback = StreamlitCallbackHandler(st_callback_container)
            try:
                response_dict = agent.invoke(
                    {"input": user_query}, 
                    callbacks=[streamlit_callback]
                )
                response = response_dict["output"]
            except Exception as e:
                response = f"⚠️ An error occurred: {e}"
            
            # Display the final response (or error) and add to history
            st_callback_container.markdown(response)
            st.session_state["messages"].append({"role": "assistant", "content": response})
