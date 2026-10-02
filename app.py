import streamlit as st
import requests
import time

GROQ_API_KEY = st.secrets.get("GROQ_API_KEY", "")

st.set_page_config(
    page_title="PulseAI - ChatGPT Edition",
    page_icon="🤖",
    layout="wide"
)

st.markdown("""
    <style>
    .main { background-color: #0d1117; }
    [data-testid="stChatMessage"] {
        direction: rtl;
        text-align: right;
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 0.5rem;
    }
    [data-testid="stChatMessage"] p, [data-testid="stChatMessage"] div {
        unicode-bidi: plaintext;
        text-align: right;
    }
    [data-testid="stChatInput"] input {
        direction: rtl;
        text-align: right;
    }
    </style>
""", unsafe_allow_html=True)

if "chats" not in st.session_state:
    st.session_state.chats = {"المحادثة الرئيسية": []}
if "current_chat" not in st.session_state:
    st.session_state.current_chat = "المحادثة الرئيسية"

with st.sidebar:
    st.title("🤖 PulseAI Pro")
    
    if st.button("➕ محادثة جديدة", use_container_width=True):
        new_chat_name = f"محادثة {len(st.session_state.chats) + 1}"
        st.session_state.chats[new_chat_name] = []
        st.session_state.current_chat = new_chat_name
        st.rerun()

    st.subheader("💬 المحادثات السابقة")
    chat_list = list(st.session_state.chats.keys())
    selected_chat = st.radio("اختر محادثة:", chat_list, index=chat_list.index(st.session_state.current_chat))
    st.session_state.current_chat = selected_chat

    st.divider()
    
    st.subheader("⚙️ الإعدادات والشخصية")
    selected_model = st.selectbox(
        "النموذج:",
        ["openai/gpt-oss-20b", "openai/gpt-oss-120b", "qwen/qwen3.8-27b"]
    )
    
    system_role = st.selectbox(
        "دور المساعد (System Prompt):",
        ["مساعد عام ذكي", "مساعد برمجة وتكاويد", "مترجم احترافي", "كاتب محتوى وإبداعي"]
    )

roles_map = {
    "مساعد عام ذكي": "أنت مساعد ذكي ومفيد يجيب بدقة ووضوح باللغة العربية.",
    "مساعد برمجة وتكاويد": "أنت مهندس برمجيات خبير. قدم حلولاً برمجية واضحة وشرحاً للكود مع أمثلة.",
    "مترجم احترافي": "أنت مترجم احترافي. قم بجمجمة النصوص بدقة عالية مع الحفاظ على المعنى والسياق.",
    "كاتب محتوى وإبداعي": "أنت كاتب محتوى إبداعي يتقن صياغة المقالات والأفكار بأسلوب شائق ومقنع."
}

st.title(f"🤖 {st.session_state.current_chat}")
st.caption(f"الدور الحالي: {system_role}")
st.divider()

current_messages = st.session_state.chats[st.session_state.current_chat]
for msg in current_messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

def ask_groq(prompt_text, primary_model):
    fallback_models = [primary_model, "openai/gpt-oss-20b", "openai/gpt-oss-120b", "qwen/qwen3.8-27b"]
    models_to_try = list(dict.fromkeys(fallback_models))
    
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    messages_payload = [{"role": "system", "content": roles_map[system_role]}]
    messages_payload.extend([{"role": m["role"], "content": m["content"]} for m in current_messages])

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

if prompt := st.chat_input("أسأل PulseAI أي شيء..."):
    current_messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("جاري التفكير..."):
            answer, err = ask_groq(prompt, selected_model)
            
            if answer:
                st.markdown(answer)
                current_messages.append({"role": "assistant", "content": answer})
            else:
                st.error(f"تنبيه: {err}")
