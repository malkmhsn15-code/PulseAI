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

# تصميم CSS كامل لمحاكاة واجهة Gemini / ChatGPT
st.markdown("""
    <style>
    /* الخلفية العامة والخطوط */
    .stApp {
        background: radial-gradient(circle at 50% 30%, #1e2230 0%, #0e1117 100%);
        color: #e6e6e6;
    }
    
    /* الشريط الجانبي */
    [data-testid="stSidebar"] {
        background-color: #131722;
        border-left: 1px solid #232736;
    }
    
    /* أزرار الشريط الجانبي والمحادثات */
    div.stButton > button {
        background-color: transparent;
        color: #c5c7d0;
        border: none;
        text-align: right;
        justify-content: flex-start;
        border-radius: 8px;
        padding: 8px 12px;
        font-size: 14px;
        transition: 0.2s;
    }
    div.stButton > button:hover {
        background-color: #232838;
        color: #ffffff;
    }
    
    /* زر محادثة جديدة المميز */
    [data-testid="stSidebar"] div.stButton:first-child > button {
        background-color: #1f2536;
        border: 1px solid #2e364f;
        font-weight: bold;
    }
    [data-testid="stSidebar"] div.stButton:first-child > button:hover {
        background-color: #2b344c;
    }

    /* شاشة الترحيب في المنتصف */
    .welcome-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        height: 50vh;
        text-align: center;
    }
    .welcome-title {
        font-size: 2.8rem;
        font-weight: bold;
        color: #e2e8f0;
        margin-bottom: 2rem;
    }

    /* رسائل الدردشة */
    [data-testid="stChatMessage"] {
        direction: rtl;
        text-align: right;
        background-color: transparent;
    }
    [data-testid="stChatMessage"] p, [data-testid="stChatMessage"] div {
        unicode-bidi: plaintext;
        text-align: right;
    }
    
    /* شريط الإدخال المودرن */
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

# إدارة المحادثات والجلسات
if "chats" not in st.session_state:
    st.session_state.chats = {}
if "current_chat_id" not in st.session_state:
    st.session_state.current_chat_id = None

# الشريط الجانبي
with st.sidebar:
    st.title("🧠 PulseAI")
    
    if st.button("➕ محادثة جديدة", use_container_width=True):
        st.session_state.current_chat_id = None
        st.rerun()

    st.markdown("### **الأحدث**")
    
    # عرض قائمة المحادثات السابقة
    for chat_id, messages in list(st.session_state.chats.items()):
        # اسم المحادثة هو أول سؤال سأله المستخدم
        first_prompt = messages[0]["content"] if messages else "محادثة فارغة"
        title = first_prompt[:25] + "..." if len(first_prompt) > 25 else first_prompt
        
        if st.button(f"💬 {title}", key=f"btn_{chat_id}", use_container_width=True):
            st.session_state.current_chat_id = chat_id
            st.rerun()

    st.divider()
    selected_model = st.selectbox(
        "النموذج:",
        ["openai/gpt-oss-20b", "openai/gpt-oss-120b", "qwen/qwen3.8-27b"]
    )

SYSTEM_PROMPT = (
    "أنت PulseAI، مساعد ذكاء اصطناعي شامل وفاخر مطوّر بواسطة PulseAI. "
    "تساعد المستخدم بذكاء ودقة باللغة العربية تجيب بأسلوب احترافي ومباشر."
)

# عرض الرسائل أو شاشة الترحيب
current_messages = st.session_state.chats.get(st.session_state.current_chat_id, [])

if not current_messages:
    # شاشة الترحيب مثل Gemini عند فتح محادثة جديدة
    st.markdown("""
        <div class="welcome-container">
            <div class="welcome-title">من أين نبدأ؟</div>
        </div>
    """, unsafe_allow_html=True)
else:
    for msg in current_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

def ask_groq(messages_list, primary_model):
    fallback_models = [primary_model, "openai/gpt-oss-20b", "openai/gpt-oss-120b", "qwen/qwen3.8-27b"]
    models_to_try = list(dict.fromkeys(fallback_models))
    
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    messages_payload = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages_payload.extend([{"role": m["role"], "content": m["content"]} for m in messages_list])

    last_error = ""
    for model in models_to_try:
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
                last_error = res_data.get("error", {}).get("message", "خطأ غير معروف")
                time.sleep(0.5)
        except Exception as e:
            last_error = str(e)
            continue

    return None, last_error

# إدخال السؤال
if prompt := st.chat_input("اسأل PulseAI..."):
    # إنشاء رقم محادثة جديدة عند بدء كتابة أول سؤال
    if st.session_state.current_chat_id is None:
        new_id = f"chat_{int(time.time())}"
        st.session_state.chats[new_id] = []
        st.session_state.current_chat_id = new_id

    chat_messages = st.session_state.chats[st.session_state.current_chat_id]
    chat_messages.append({"role": "user", "content": prompt})
    
    st.rerun()

# إذا كان هناك سؤال ينتظر الإجابة
if current_messages and current_messages[-1]["role"] == "user":
    with st.chat_message("assistant"):
        with st.spinner("جاري التفكير..."):
            answer, err = ask_groq(current_messages, selected_model)
            if answer:
                st.markdown(answer)
                current_messages.append({"role": "assistant", "content": answer})
                st.rerun()
            else:
                st.error(f"تنبيه: {err}")
