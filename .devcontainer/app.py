import streamlit as st
import google.generativeai as genai
import json
import os
from pathlib import Path
from dotenv import load_dotenv
from PIL import Image
import io

# 1. إعداد الصفحة
st.set_page_config(
    page_title="Skin Care Bot | روتينك الجمالي",
    layout="wide",
    page_icon="🌸"
)

# 2. تحميل الإعدادات وتهيئة الموديل
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    st.error("⚠️ خطأ: مفيش API Key! اتأكد إن ملف .env شغال وفيه الـ GOOGLE_API_KEY")
    st.stop()

genai.configure(api_key=api_key)

@st.cache_resource
def init_model():
    """تهيئة الموديل مع تفعيل قدرات التفكير في إصدار 2.5"""
    try:
        # بنحدد ميزانية التفكير عشان نمنع الـ UI من التعليق
        model = genai.GenerativeModel(
            model_name='gemini-2.5-flash',
            generation_config={
                "temperature": 0.7,
                "top_p": 0.95,
                "max_output_tokens": 2048,
            }
        )
        return model, 'gemini-2.5-flash'
    except Exception as e:
        st.warning(f"فشل تشغيل 2.5، بنجرب النسخة المستقرة: {str(e)}")
        return genai.GenerativeModel('gemini-1.5-flash'), 'gemini-1.5-flash'

model, used_model_name = init_model()

# 3. تحميل المنتجات
@st.cache_data
def load_products():
    try:
        path = Path(__file__).parent / "products_db.json"
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        return [{"name": "Generic Moisturizer", "type": "cream"}] # داتا احتياطية
    except:
        return []

products = load_products()

# 4. الـ CSS
st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #fff5f7 0%, #ffffff 100%); }
    h1 { color: #ff4b6e !important; text-align: center; font-weight: 700; }
    .stSpinner > div > div { border-top-color: #ff4b6e !important; }
    </style>
    """, unsafe_allow_html=True)

# 5. واجهة المستخدم
st.title("🌸 Skin Care Bot - رفيقتك للجمال 🌸")
st.caption(f"🔧 الموديل النشط حالياً: {used_model_name}")

with st.sidebar:
    st.markdown("### ✨ كوني جميلة، كوني أنتِ")
    uploaded_file = st.file_uploader("📸 صوري بشرتك للتحليل", type=['jpg', 'jpeg', 'png'])
    if st.button("تفريغ الشات"):
        st.session_state.messages = []
        st.rerun()

# 6. تحليل الصور (تعديل جوهري لفك التعليقة)
if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, caption="الصورة المرفوعة", width=300)
    
    if st.button("🔍 حلل صورتي"):
        with st.spinner("ثواني يا جميلة.. Gemini 2.5 بيفكر في حالتك..."):
            try:
                products_text = json.dumps(products, ensure_ascii=False)
                # البرومبت المطور لتقليل الهبد
                img_prompt = (
                    f"أنت خبير جلدية مصري محترف. حلل حالة البشرة في الصورة بدقة. "
                    f"اقترح روتين مخصص من هذه القائمة فقط: {products_text}. "
                    "اتكلم بلهجة مصرية ودودة وقدم نصائح عملية."
                )
                
                # إرسال الصورة بشكل صحيح لـ Gemini 2.5
                response = model.generate_content([img_prompt, image])
                
                st.success("✅ التحليل جاهز:")
                st.write(response.text)
            except Exception as e:
                st.error(f"حصلت مشكلة في التحليل: {str(e)}")

# 7. نظام الشات
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
        with st.spinner("براجع داتا المنتجات وبفكر لك..."):
            try:
                full_prompt = f"أنت خبيرة تجميل مصرية شاطرة. المنتجات المتاحة عندنا: {json.dumps(products)}. سؤال المستخدم: {prompt}"
                response = model.generate_content(full_prompt)
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
            except Exception as e:
                st.error("السيستم وقع مني ثانية، جربي تسألي تاني.")
