import streamlit as st
import requests
import time

GROQ_API_KEY = st.secrets.get("GROQ_API_KEY", "")

st.set_page_config(
    page_title="PulseAI",
    page_icon="🧠",
    layout="wide"
)

st.markdown("""
    <style>
    [data-testid="stChatMessage"] {
        direction: rtl;
        text-align: right;
    }
    
    [data-testid="stChatMessage"] p, [data-testid="stChatMessage"] div {
        unicode-bidi: plaintext;
        text-align: right;
    }

    [data-testid="stChatMessageAvatar"] {
        margin-left: 10px;
        margin-right: 0px;
    }
    
    [data-testid="stChatInput"] input {
        direction: rtl;
        text-align: right;
    }
    </style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.title("🧠 PulseAI")
    st.caption("مساعد ذكي مدعوم بواسطة Groq")
    st.divider()

    if st.button("➕ محادثة جديدة", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    st.subheader("⚙️ نموذج الذكاء الاصطناعي")
    selected_model = st.selectbox(
        "اختر النموذج الرئيسي:",
        ["openai/gpt-oss-20b", "openai/gpt-oss-120b", "qwen/qwen3.8-27b"]
    )
    st.info("🟢 الحالة: متصل بـ Groq")

col1, col2 = st.columns([1, 10])
with col1:
    st.markdown("## 🧠")
with col2:
    st.title("PulseAI")

st.write("أهلاً بك في PulseAI! كيف يمكنني مساعدتك اليوم؟")
st.divider()

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

def ask_groq(prompt_text, primary_model):
    fallback_models = [primary_model, "openai/gpt-oss-20b", "openai/gpt-oss-120b", "qwen/qwen3.8-27b"]
    models_to_try = list(dict.fromkeys(fallback_models))
    
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    api_messages = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]

    last_error = ""
    for model in models_to_try:
        payload = {
            "model": model,
            "messages": api_messages,
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

if prompt := st.chat_input("اكتب سؤالك هنا..."):
    
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("PulseAI يفكر الآن..."):
            answer, err = ask_groq(prompt, selected_model)
            
            if answer:
                st.markdown(answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})
            else:
                st.error(f"تنبيه من Groq: {err}")
