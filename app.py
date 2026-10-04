import streamlit as st
import requests
import time
from supabase import create_client, Client

GROQ_API_KEY = st.secrets.get("GROQ_API_KEY", "")
SUPABASE_URL = st.secrets.get("SUPABASE_URL", "")
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", "")

APP_URL = "https://pulseai-fftvktkyjjfexvce6capphx.streamlit.app"

@st.cache_resource
def init_supabase() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_supabase()

def get_authenticated_supabase() -> Client:
    session = st.session_state.get("session")
    if session and hasattr(session, "access_token"):
        client = create_client(SUPABASE_URL, SUPABASE_KEY)
        client.postgrest.auth(session.access_token)
        return client
    return supabase

st.set_page_config(
    page_title="PulseAI",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

query_params = st.query_params
if "code" in query_params:
    auth_code = query_params["code"]
    try:
        res = supabase.auth.exchange_code_for_session({"auth_code": auth_code})
        st.session_state.user = res.user
        st.session_state.session = res.session
        st.query_params.clear()
        st.rerun()
    except Exception:
        st.query_params.clear()

st.markdown("""
    <style>
    .stApp {
        background: radial-gradient(circle at 50% 30%, #1e2230 0%, #0e1117 100%);
        color: #e6e6e6;
    }
    
    [data-testid="stSidebar"] {
        background-color: #131722;
        border-left: 1px solid #232736;
    }
    
    div.stButton > button {
        background-color: transparent;
        color: #c5c7d0;
        border: none;
        text-align: right;
        justify-content: flex-start;
        border-radius: 8px;
        padding: 4px 8px;
        font-size: 13px;
        transition: 0.2s;
    }
    div.stButton > button:hover {
        background-color: #232838;
        color: #ffffff;
    }

    .options-box {
        background-color: #1a1f2c;
        border-radius: 6px;
        padding: 6px;
        margin-bottom: 8px;
        border: 1px solid #2e364f;
    }

    .welcome-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        height: 45vh;
        text-align: center;
    }
    .welcome-title {
        font-size: 2.8rem;
        font-weight: bold;
        color: #e2e8f0;
        margin-bottom: 1.5rem;
    }

    .login-box {
        max-width: 420px;
        margin: 40px auto 10px auto;
        padding: 20px;
        background-color: #131722;
        border-radius: 12px;
        border: 1px solid #232736;
        text-align: center;
    }

    [data-testid="stChatMessage"] {
        direction: rtl;
        text-align: right;
        background-color: transparent;
    }
    [data-testid="stChatMessage"] p, [data-testid="stChatMessage"] div {
        unicode-bidi: plaintext;
        text-align: right;
    }
    
    [data-testid="stChatInput"] {
        max-width: 750px;
        margin: 0 auto;
    }
    [data-testid="stChatInput"] input {
        direction: rtl;
        text-align: right;
        background-color: #1e2333 !important;
        border: 1px solid #323b54 !important;
        border-radius: 25px !important;
        color: #ffffff !important;
    }
    </style>
""", unsafe_allow_html=True)

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

SYSTEM_PROMPT = (
    "أنت PulseAI، مساعد ذكاء اصطناعي شامل وفاخر مطوّر بواسطة PulseAI. "
    "تساعد المستخدم بذكاء ودقة باللغة العربية بأسلوب احترافي ومباشر."
)

def load_user_chats(user_id):
    try:
        db_client = get_authenticated_supabase()
        res = db_client.table("user_chats").select("*").eq("user_id", user_id).execute()
        chats = {}
        for row in res.data:
            chats[row["id"]] = {
                "title": row["title"],
                "pinned": row.get("pinned", False),
                "messages": row.get("messages", [])
            }
        return chats
    except Exception as e:
        st.error(f"خطأ في جلب المحادثات: {e}")
        return {}

def save_chat_to_db(chat_id, user_id, title, pinned, messages):
    try:
        db_client = get_authenticated_supabase()
        db_client.table("user_chats").upsert({
            "id": chat_id,
            "user_id": user_id,
            "title": title,
            "pinned": pinned,
            "messages": messages
        }).execute()
    except Exception as e:
        st.error(f"خطأ أثناء حفظ المحادثة: {e}")

def delete_chat_from_db(chat_id):
    try:
        db_client = get_authenticated_supabase()
        db_client.table("user_chats").delete().eq("id", chat_id).execute()
    except Exception as e:
        st.error(f"خطأ أثناء حذف المحادثة: {e}")

try:
    session = supabase.auth.get_session()
    if session and session.user:
        st.session_state.user = session.user
        st.session_state.session = session
        if not st.session_state.user_chats:
            st.session_state.user_chats = load_user_chats(session.user.id)
except Exception:
    pass

def show_login():
    st.markdown("""
        <div class="login-box">
            <h2 style="color: #ffffff;">🧠 PulseAI</h2>
            <p style="color: #a0aec0; margin-bottom: 15px;">مرحباً بك! يرجى تسجيل الدخول للمتابعة</p>
        </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        try:
            google_auth_res = supabase.auth.sign_in_with_oauth({
                "provider": "google",
                "options": {
                    "redirect_to": APP_URL
                }
            })
            auth_url = getattr(google_auth_res, "url", None) or (google_auth_res.get("url") if isinstance(google_auth_res, dict) else None)
            if auth_url:
                st.link_button("🌐 الدخول باستخدام جوجل (Google)", auth_url, use_container_width=True)
            else:
                st.error("فشل الحصول على رابط تسجيل الدخول عبر Google")
        except Exception as e:
            st.error(f"حدث خطأ في جلب رابط تسجيل الدخول: {e}")

        st.write("---")
        email = st.text_input("البريد الإلكتروني")
        password = st.text_input("كلمة المرور", type="password")
        
        c1, c2 = st.columns(2)
        with c1:
            login_btn = st.button("تسجيل الدخول", use_container_width=True)
        with c2:
            signup_btn = st.button("حساب جديد", use_container_width=True)
            
        if login_btn:
            if email and password:
                try:
                    res = supabase.auth.sign_in_with_password({"email": email, "password": password})
                    st.session_state.user = res.user
                    st.session_state.session = res.session
                    st.session_state.user_chats = load_user_chats(res.user.id)
                    st.success("تم تسجيل الدخول بنجاح!")
                    st.rerun()
                except Exception as e:
                    st.error(f"فشل تسجيل الدخول: {e}")
            else:
                st.error("يرجى إدخال البريد الإلكتروني وكلمةهلا! تفضل، شلون أقدر أساعدك اليوم؟
