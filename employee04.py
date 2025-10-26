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
st.set_page_config(page_title="Langchain Chat with SQLite Database", page_icon="💬", layout="wide")
st.title(" Langchain Chat with SQLite DB 💬")

# --- LOAD ENV ---
load_dotenv()
api_key = os.getenv("GROQ_API_KEY")

# --- VALIDATION ---
if not api_key:
    st.error("⚠️ GROQ_API_KEY missing in environment variables.")
    st.stop()

# --- MODEL SELECTION ---
model_options = [
    "llama-3.3-70b-versatile",  # Groq model
]
selected_model = st.sidebar.selectbox(" Model useing ", options=model_options, index=0)

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
[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #6366f1, #8b5cf6);
border-right: 2px solid #a5b4fc;
            }
[data-testid="stSidebar"] h2, 
[data-testid="stSidebar"] h3,
[data-testid="stSidebar"] label, 
[data-testid="stSidebar"] p {
    color: #f9fafb;  /* Soft white */
    font-weight: 600;
}

/* Style for the sidebar selectbox label */
[data-testid="stSidebar"] label {
    color: #ffffff !important;    /* change color */
    font-size: 18px !important;   /* change size */
    font-weight: 700;             /* make it bold */
}

/* Make sidebar button always visible on your gradient */
            
[data-testid="stSidebar"] button[kind="secondary"] {
    color: #f9fafb !important;      
    background-color: transparent !important; 
    border: 2px solid #f9fafb !important;    
    font-weight: 600 !important;   
}
[data-testid="stSidebar"] button[kind="secondary"]:hover {
    background-color: rgba(255, 255, 255, 0.1) !important; /* Optional hover effect */
}

         
.chat-left {
    background-color: #e5f1fb;
    color: #1f2937;
    border-radius: 10px;
    padding: 10px 15px;
    margin: 5px 0;
    max-width: 70%;
    text-align: left;
}
.chat-right {
    background-color: #dbeafe;
    color: #1f2937;
    border-radius: 10px;
    padding: 10px 15px;
    margin: 5px 0;
    max-width: 70%;
    text-align: left;
    margin-left: auto;
}
h1, h2, h3, h4 {
    color: #2563eb;
    font-size: 1.8rem; 
}
</style>
<hr style="border: none; height: 2px; background: #dbeafe; margin-top: -10px; margin-bottom: 20px">
""", unsafe_allow_html=True)
# --- INITIAL CHAT SESSION ---
if "messages" not in st.session_state or st.sidebar.button("🧹 Clear message history"):
    st.session_state["messages"] = [{"role": "assistant", "content": "👋 How can I help you with your SQLite database today?"}]

with st.sidebar.expander("ℹ️ How to use this chat", expanded=False):
    st.markdown("""
    <div style="
        background-color: rgba(0, 0, 0, 0.25);
        padding: 12px;
        border-radius: 8px;
        color: #f8fafc;
        font-size: 15px;
        line-height: 1.6;
    ">
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
    </div>
    """, unsafe_allow_html=True)
# Display previous messages
for msg in st.session_state["messages"]:
    if msg["role"] == "user":
        st.markdown(f'<div class="chat-left">{msg["content"]}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="chat-right">{msg["content"]}</div>', unsafe_allow_html=True)

# --- USER INPUT ---
user_query = st.chat_input(placeholder="Ask anything from the SQLite database...")
if user_query:
    st.session_state["messages"].append({"role": "user", "content": user_query})
    st.markdown(f'<div class="chat-left">{user_query}</div>', unsafe_allow_html=True)

    response = None
    forbidden_commands = ["DROP", "DELETE", "UPDATE", "ALTER", "INSERT"]

    if any(cmd in user_query.upper() for cmd in forbidden_commands):
        st.warning("⚠️ Destructive queries are not allowed.")
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
                st.error(response)

    if response:
        st.session_state["messages"].append({"role": "assistant", "content": response})
        st_callback_container.markdown(response)








