import streamlit as st
import google.generativeai as genai
import json
import os
from pathlib import Path
from dotenv import load_dotenv
from PIL import Image

# 1. إعداد الصفحة (لازم يكون أول أمر في Streamlit ومرة واحدة فقط)
st.set_page_config(
    page_title="Skin Care Bot | روتينك الجمالي",
    layout="wide",
    page_icon="🌸"
)

# 2. تحميل الإعدادات وتهيئة الموديل (Caching)
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

@st.cache_resource
def init_model():
    """تهيئة الموديل مرة واحدة فقط لسرعة الاستجابة"""
    try:
        # بنحاول نستخدم الفلاش لأنه الأسرع للصور
        model = genai.GenerativeModel('gemini-2.5-flash')
        return model, 'gemini-2.5-flash'
    except:
        return genai.GenerativeModel('gemini-pro'), 'gemini-pro'

model, used_model_name = init_model()

# 3. تحميل المنتجات (Caching)
@st.cache_data
def load_products():
    """تحميل ملف المنتجات في الذاكرة لسرعة الوصول"""
    try:
        path = Path(__file__).parent / "products_db.json"
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

products = load_products()

# 4. الـ CSS (خليناه بره عشان ميتعدش تحميله كل شوية)
st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #fff5f7 0%, #ffffff 100%); }
    h1 { color: #ff4b6e !important; text-align: center; font-weight: 700; text-shadow: 1px 1px 2px #ffb6c1; }
    section[data-testid="stSidebar"] { background-color: #ffe4e8 !important; }
    .stButton>button { width: 100%; background-color: #ff4b6e !important; color: white !important; border-radius: 25px; }
    .stChatMessage { border-radius: 20px !important; }
    [data-testid="stChatMessageAssistant"] { background-color: #fff0f3 !important; }
    </style>
    """, unsafe_allow_html=True)

# 5. واجهة المستخدم
st.markdown('<img src="https://cdn-icons-png.flaticon.com/512/3515/3515155.png" style="display: block; margin: auto; width: 80px;">', unsafe_allow_html=True)
st.title("🌸 Skin Care Bot - رفيقتك للجمال 🌸")
st.caption(f"🔧 الموديل النشط: {used_model_name}")

with st.sidebar:
    st.markdown("### ✨ كوني جميلة، كوني أنتِ")
    uploaded_file = st.file_uploader("📸 صوري بشرتك للتحليل", type=['jpg', 'jpeg', 'png'])
    if st.button("تفريغ الشات"):
        st.session_state.messages = []
        st.rerun()

# 6. تحليل الصور (تعديل لزيادة السرعة)
if uploaded_file is not None:
    image = Image.open(uploaded_file)
    # تصغير حجم الصورة قبل الإرسال لسرعة الرد
    image.thumbnail((500, 500))
    st.image(image, caption="الصورة المرفوعة", width=300)
    
    if st.button("🔍 حلل صورتي"):
        with st.spinner("ثواني يا جميلة.. بنفحص الصورة..."):
            products_text = json.dumps(products, ensure_ascii=False)
            img_prompt = f"أنت خبير جلدية مصري. حلل الصورة المرفقة واقترح روتين من هذه القائمة فقط: {products_text}. اتكلم بلهجة مصرية."
            
            try:
                # استخدمنا الموديل اللي اتعرف فوق
                response = model.generate_content([img_prompt, image])
                st.info(response.text)
            except Exception as e:
                st.error("السيرفر مضغوط شوية، جربي تدوسي تاني.")

# 7. نظام الشات (بسيط وسريع)
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("بشرتك محتاجة إيه النهاردة؟"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("بفكر..."):
            # دمج تعليمات النظام مع سؤال المستخدم في رسالة واحدة لتقليل حجم الداتا المبعوتة
            full_prompt = f"أنت خبيرة تجميل مصرية. المنتجات المتاحة: {json.dumps(products)}. سؤال المستخدم: {prompt}"
            response = model.generate_content(full_prompt)
            st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
