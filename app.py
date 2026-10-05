import streamlit as st
import requests
import time
from supabase import create_client, Client
from streamlit_cookies_controller import CookieController

GROQ_API_KEY = st.secrets.get("GROQ_API_KEY", "")
SUPABASE_URL = st.secrets.get("SUPABASE_URL", "")
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", "")

APP_URL = "https://pulseai-fftvktkyjjfexvce6capphx.streamlit.app"

st.set_page_config(
    page_title="PulseAI",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

controller = CookieController()

@st.cache_resource
def init_supabase() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_supabase()

if "user" not in st.session_state:
    st.session_state.user = None
if "session" not in st.session_state:
    st.session_state.session = None
if "user_chats" not in st.session_state:
    st.session_state.user_chats = {}
if "current_chat_id" not in st.session_state:
    st.session_state.current_chat_id = None
if "active_options_id" not in st.session_state:
    st.session_state.active_options_id = None
if "rename_id" not in st.session_state:
    st.session_state.rename_id = None

def get_authenticated_supabase() -> Client:
    session = st.session_state.get("session")
    if session and hasattr(session, "access_token"):
        client = create_client(SUPABASE_URL, SUPABASE_KEY)
        client.postgrest.auth(session.access_token)
        return client
    return supabase

def load_user_chats(user_id):
    try:
        db_client = get_authenticated_supabase()
        res = db_client.table("user_chats").select("*").eq("user_id", str(user_id)).execute()
        chats = {}
        for row in res.data:
            chats[row["id"]] = {
                "title": row["title"],
                "pinned": row.get("pinned", False),
                "messages": row.get("messages", [])
            }
        return chats
    except Exception:
        return {}

query_params = st.query_params
if "code" in query_params:
    auth_code = query_params["code"]
    try:
        res = supabase.auth.exchange_code_for_session({"auth_code": auth_code})
        if res and hasattr(res, "user") and res.user:
            st.session_state.user = res.user
            st.session_state.session = res.session
            st.session_state.user_chats = load_user_chats(res.user.id)
            
            if res.session and hasattr(res.session, "access_token"):
                controller.set('sb_access_token', res.session.access_token, max_age=30*24*60*60)
                controller.set('sbأكيد، تم إزالة كافة الشروحات (التعليقات/Comments) من داخل الكود. تفضل الكود النظيف:

```html
<!DOCTYPE html>
<html lang="ar">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>حاسبة الفائدة المركبة</title>
  <style>
    :root {
      --bg-color: #f4f7f6;
      --card-bg: #ffffff;
      --text-color: #2c3e50;
      --accent-color: #3498db;
      --border-color: #e0e0e0;
    }

    body {
      font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
      background-color: var(--bg-color);
      color: var(--text-color);
      margin: 0;
      padding: 20px;
      direction: rtl;
    }

    .container {
      max-width: 600px;
      margin: 20px auto;
      background-color: var(--card-bg);
      padding: 25px;
      border-radius: 12px;
      box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
    }

    h1 {
      margin-top: 0;
      font-size: 1.5rem;
      text-align: center;
    }

    .form-group {
      margin-bottom: 15px;
    }

    label {
      display: block;
      margin-bottom: 5px;
      font-weight: 600;
    }

    input, select {
      width: 100%;
      padding: 10px;
      border: 1px solid var(--border-color);
      border-radius: 6px;
      box-sizing: border-box;
      font-size: 1rem;
    }

    button {
      width: 100%;
      padding: 12px;
      background-color: var(--accent-color);
      color: white;
      border: none;
      border-radius: 6px;
      font-size: 1rem;
      font-weight: bold;
      cursor: pointer;
      margin-top: 10px;
    }

    button:hover {
      opacity: 0.9;
    }

    .results {
      margin-top: 25px;
      padding-top: 20px;
      border-top: 2px solid var(--border-color);
      display: none;
    }

    .result-item {
      display: flex;
      justify-content: space-between;
      margin-bottom: 10px;
      font-size: 1.1rem;
    }

    .result-item.highlight {
      font-weight: bold;
      color: var(--accent-color);
      font-size: 1.2rem;
    }
  </style>
</head>
<body>

  <div class="container">
    <h1>حاسبة الفائدة المركبة</h1>
    
    <div class="form-group">
      <label for="principal">المبلغ الأصلي:</label>
      <input type="number" id="principal" value="10000" min="0">
    </div>

    <div class="form-group">
      <label for="rate">نسبة الفائدة السنوية (%):</label>
      <input type="number" id="rate" value="5" step="0.1" min="0">
    </div>

    <div class="form-group">
      <label for="years">المدة (بالسنوات):</label>
      <input type="number" id="years" value="10" min="1">
    </div>

    <div class="form-group">
      <label for="frequency">تكرار التراكب:</label>
      <select id="frequency">
        <option value="1">سنوياً</option>
        <option value="2">نصف سنوي</option>
        <option value="4">ربع سنوي</option>
        <option value="12" selected>شهرياً</option>
        <option value="365">يومياً</option>
      </select>
    </div>

    <button onclick="calculateInterest()">احسب الناتج</button>

    <div class="results" id="results">
      <div class="result-item">
        <span>إجمالي الفائدة المكتسبة:</span>
        <span id="total-interest">0</span>
      </div>
      <div class="result-item highlight">
        <span>المبلغ النهائي الإجمالي:</span>
        <span id="final-amount">0</span>
      </div>
    </div>
  </div>

  <script>
    function calculateInterest() {
      const P = parseFloat(document.getElementById('principal').value);
      const r = parseFloat(document.getElementById('rate').value) / 100;
      const t = parseFloat(document.getElementById('years').value);
      const n = parseInt(document.getElementById('frequency').value);

      if (isNaN(P) || is
