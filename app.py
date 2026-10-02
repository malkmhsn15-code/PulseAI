import streamlit as st
import requests
import time

GROQ_API_KEY = st.secrets.get("GROQ_API_KEY", "")

st.set_page_config(
    page_title="PulseAI",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
        padding: 6px 10px;
        font-size: 14px;
        transition: 0.2s;
    }
    div.stButton > button:hover {
        background-color: #232838;
        color: #ffffff;
    }

    .pinned-box {
        background-color: #1a233a;
        border-right: 4px solid #4f46e5;
        padding: 10px;
        border-radius: 8px;
        margin-bottom: 15px;
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

if "chats" not in st.session_state:
    st.session_state.chats = {}
if "current_chat_id" not in st.session_state:
    st.session_state.current_chat_id = None
if "rename_id" not in st.session_state:
    st.session_state.rename_id = None

SYSTEM_PROMPT = (
    "أنت PulseAI، مساعد ذكاء اصطناعي شامل وفاخر مطوّر بواسطة PulseAI. "
    "تساعد المستخدم بذكاء ودقة باللغة العربية بأسلوب احترافي ومباشر."
)

def call_groq_api(messages_payload, model):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": messages_payload,
        "temperature": 0.7
    }
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=15)
        res_data = response.json()
        if response.status_code == 200:
            return res_data["choices"][0]["message"]["content"], None
        else:
            return None, res_data.get("error", {}).get("message", "خطأ في الاتصال")
    except Exception as e:
        return None, str(e)

def generate_chat_title(user_prompt, model):
    prompt_payload = [
        {"role": "system", "content": "أنت مصمم عناوين. اكتب عنواناً جذاباً ومختصراً جداً (من 3 إلى 5 كلمات فقط) يلخص فكرة السؤال التالي بدون أقواس أو علامات تنقيط:"},
        {"role": "user", "content": user_prompt}
    ]
    title, _ = call_groq_api(prompt_payload, model)
    if title:
        return title.strip().replace('"', '').replace("'", "")
    return user_prompt[:25]

with st.sidebar:
    st.title("🧠 PulseAI")
    
    if st.button("➕ محادثة جديدة", use_container_width=True):
        st.session_state.current_chat_id = None
        st.session_state.rename_id = None
        st.rerun()

    st.markdown("### **الأحدث**")
    
    for cid, chat_data in list(st.session_state.chats.items()):
        col1, col2, col3 = st.columns([0.7, 0.15, 0.15])
        
        with col1:
            title_display = chat_data["title"]
            if st.button(f"💬 {title_display}", key=f"select_{cid}", use_container_width=True):
                st.session_state.current_chat_id = cid
                st.rerun()
                
        with col2:
            if st.button("✏️️", key=f"ren_{cid}"):
                st.session_state.rename_id = cid if st.session_state.rename_id != cid else None
                st.rerun()
                
        with col3:
            if st.button("🗑️", key=f"del_{cid}"):
                del st.session_state.chats[cid]
                if st.session_state.current_chat_id == cid:
                    st.session_state.current_chat_id = None
                st.rerun()
                
        if st.session_state.rename_id == cid:
            new_title = st.text_input("العنوان الجديد:", value=chat_data["title"], key=f"inp_{cid}")
            if st.button("حفظ", key=f"save_{cid}"):
                st.session_state.chats[cid]["title"] = new_title
                st.session_state.rename_id = None
                st.rerun()

    st.divider()
    selected_model = st.selectbox(
        "النموذج:",
        ["openai/gpt-oss-20b", "openai/gpt-oss-120b", "qwen/qwen3.8-27b"]
    )

current_chat = st.session_state.chats.get(st.session_state.current_chat_id, None)

if not current_chat or not current_chat["messages"]:
    st.markdown("""
        <div class="welcome-container">
            <div class="welcome-title">من أين نبدأ؟</div>
        </div>
    """, unsafe_allow_html=True)
else:
    if current_chat.get("pinned"):
        st.markdown(f"""
            <div class="pinned-box">
                📌 <b>الرسالة المثبتة:</b><br>{current_chat['pinned']}
            </div>
        """, unsafe_allow_html=True)
        if st.button("❌ إلغاء التثبيت", key="unpin_btn"):
            current_chat["pinned"] = None
            st.rerun()

    for idx, msg in enumerate(current_chat["messages"]):
        with st.chat_message(msg["role"]):
            c1, c2 = st.columns([0.93, 0.07])
            with c1:
                st.markdown(msg["content"])
            with c2:
                if st.button("📌", key=f"pin_{idx}"):
                    current_chat["pinned"] = msg["content"]
                    st.rerun()

if prompt := st.chat_input("اسأل PulseAI..."):
    if st.session_state.current_chat_id is None:
        new_id = f"chat_{int(time.time())}"
        smart_title = generate_chat_title(prompt, selected_model)
        st.session_state.chats[new_id] = {
            "title": smart_title,
            "messages": [],
            "pinned": None
        }
        st.session_state.current_chat_id = new_id

    active_chat = st.session_state.chats[st.session_state.current_chat_id]
    active_chat["messages"].append({"role": "user", "content": prompt})
    st.rerun()

if current_chat and current_chat["messages"] and current_chat["messages"][-1]["role"] == "user":
    with st.chat_message("assistant"):
        with st.spinner("جاري التفكير..."):
            payload = [{"role": "system", "content": SYSTEM_PROMPT}]
            payload.extend([{"role": m["role"], "content": m["content"]} for m in current_chat["messages"]])
            
            answer, err = call_groq_api(payload, selected_model)
            if answer:
                st.markdown(answer)
                current_chat["messages"].append({"role": "assistant", "content": answer})
                st.rerun()
            else:
                st.error(f"تنبيه: {err}")
