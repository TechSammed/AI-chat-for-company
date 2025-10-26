st.markdown("""
<style>
/* --- SIDEBAR STYLING --- */
[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #4338ca, #7c3aed);
  border-right: 2px solid #a5b4fc;
}
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] p {
  color: #f9fafb;
  font-weight: 600;
}

/* Sidebar selectbox label */
[data-testid="stSidebar"] label {
  color: #ffffff !important;
  font-size: 18px !important;
  font-weight: 700;
}

/* Sidebar buttons */
[data-testid="stSidebar"] button[kind="secondary"] {
  color: #f9fafb !important;
  background-color: transparent !important;
  border: 2px solid #f9fafb !important;
  font-weight: 600 !important;
}
[data-testid="stSidebar"] button[kind="secondary"]:hover {
  background-color: rgba(255, 255, 255, 0.15) !important;
}

/* --- CHAT STYLING --- */
.chat-left {
  background-color: #e0f2fe; /* light blue */
  color: #1e3a8a;            /* dark navy text */
  border-radius: 10px;
  padding: 10px 15px;
  margin: 5px 0;
  max-width: 70%;
  text-align: left;
}
.chat-right {
  background-color: #dbeafe; /* soft blue */
  color: #1e3a8a;
  border-radius: 10px;
  padding: 10px 15px;
  margin: 5px 0;
  max-width: 70%;
  text-align: left;
  margin-left: auto;
}

/* Headings */
h1, h2, h3, h4 {
  color: #2563eb;
  font-size: 1.8rem;
}

/* --- EXPANDER (Help Box) FIX --- */
[data-testid="stSidebar"] [data-testid="stExpander"] div[role="button"] {
  color: #ffffff !important;
}
[data-testid="stSidebar"] [data-testid="stExpander"] div[data-testid="stMarkdownContainer"] {
  background-color: rgba(255, 255, 255, 0.15);
  padding: 10px;
  border-radius: 8px;
  color: #f1f5f9;
}
</style>
<hr style="border: none; height: 2px; background: #dbeafe; margin-top: -10px; margin-bottom: 20px">
""", unsafe_allow_html=True)
