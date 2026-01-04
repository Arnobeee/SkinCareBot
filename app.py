import streamlit as st
import google.generativeai as genai
import json
import os
from pathlib import Path
# تأكد إن السطر ده موجود بالظبط
from dotenv import load_dotenv
from PIL import Image

# إعداد الصفحة
st.set_page_config(
    page_title="ٍSkin Care Bot | روتينك الجمالي",
    layout="wide",
    page_icon="🌸"
)

# إضافة لمسات CSS مخصصة
st.markdown("""
    <style>
    /* تغيير الخلفية العامة */
    .stApp {
        background: linear-gradient(135deg, #fff5f7 0%, #ffffff 100%);
    }
    
    /* تنسيق العناوين */
    h1 {
        color: #ff4b6e !important;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        text-align: center;
        font-weight: 700;
        text-shadow: 1px 1px 2px #ffb6c1;
    }
    
    /* تنسيق القائمة الجانبية */
    section[data-testid="stSidebar"] {
        background-color: #ffe4e8 !important;
        border-right: 2px solid #ffccd5;
    }
    
    /* تنسيق أزرار الـ Sidebar */
    .stButton>button {
        width: 100%;
        background-color: #ff4b6e !important;
        color: white !important;
        border-radius: 25px !important;
        border: none !important;
        transition: 0.3s all ease;
        font-weight: bold;
    }
    
    .stButton>button:hover {
        background-color: #ff85a1 !important;
        transform: scale(1.02);
    }

    /* تنسيق رسائل الشات */
    .stChatMessage {
        border-radius: 20px !important;
        padding: 15px !important;
        margin-bottom: 10px;
    }
    
    /* تمييز رد البوت بلون مختلف */
    [data-testid="stChatMessageAssistant"] {
        background-color: #fff0f3 !important;
        border: 1px solid #ffccd5;
    }

    /* تنسيق الـ Input (مكان الكتابة) */
    .stChatInputContainer {
        border-radius: 30px !important;
        border: 1px solid #ff4b6e !important;
    }
    
    /* أيقونة لطيفة فوق العنوان */
    .header-icon {
        display: block;
        margin-left: auto;
        margin-right: auto;
        width: 100px;
    }
    </style>
    """, unsafe_allow_html=True)

# إضافة صورة لوجو أو أيقونة في البداية
st.markdown('<img src="https://cdn-icons-png.flaticon.com/512/3515/3515155.png" class="header-icon">', unsafe_allow_html=True)
st.title("🌸 Skin Care Bot - رفيقتك للعناية بالجمال 🌸")
# حط هنا الـ API Key اللي جبته من Google AI Studio
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# إعداد الموديل - محاولة استخدام موديل متاح
@st.cache_resource
def init_model():
    """تهيئة الموديل"""
    try:
        # محاولة جلب قائمة الموديلات المتاحة
        available_models = genai.list_models()
        model_names_to_try = []
        
        # البحث عن الموديلات التي تدعم generateContent
        for m in available_models:
            if 'generateContent' in m.supported_generation_methods:
                # إزالة 'models/' من اسم الموديل
                model_name = m.name.replace('models/', '')
                model_names_to_try.append(model_name)
        
        # إذا لم نجد موديلات من list_models، استخدم القائمة الافتراضية
        if not model_names_to_try:
            model_names_to_try = ['gemini-pro']
    except Exception as e:
        # إذا فشل list_models، استخدم القائمة الافتراضية - نبدأ بـ gemini-pro فقط
        model_names_to_try = ['gemini-pro']
    
    # تجربة كل موديل
    for model_name in model_names_to_try:
        try:
            model = genai.GenerativeModel(model_name)
            return model, model_name
        except Exception as e:
            continue
    
    # إذا فشلت كل المحاولات
    return None, None

model, used_model_name = init_model()

if model is None:
    st.error("❌ لم يتم العثور على أي موديل متاح!")
    
    # محاولة عرض الموديلات المتاحة
    try:
        st.info("محاولة جلب قائمة الموديلات المتاحة...")
        available_models = genai.list_models()
        model_list = []
        for m in available_models:
            if 'generateContent' in m.supported_generation_methods:
                model_list.append(m.name.replace('models/', ''))
        
        if model_list:
            st.info(f"الموديلات المتاحة: {', '.join(model_list)}")
        else:
            st.warning("لم يتم العثور على أي موديلات تدعم generateContent")
    except Exception as e:
        st.warning(f"فشل جلب قائمة الموديلات: {str(e)}")
    
    st.info("""
    **الحلول المقترحة:**
    1. تأكد من أن API Key صحيح ومن Google AI Studio: https://makersuite.google.com/app/apikey
    2. تأكد من تفعيل Gemini API في Google Cloud Console
    3. جرب إنشاء API Key جديد
    4. تأكد من أن API Key لديه صلاحيات الوصول لـ Gemini API
    5. تأكد من وجود ملف .env مع GOOGLE_API_KEY
    """)
    st.stop()
else:
    # عرض الموديل المستخدم (اختياري)
    st.caption(f"🔧 الموديل المستخدم: {used_model_name}")

# قراءة قاعدة بيانات المنتجات
@st.cache_data
def load_products():
    """تحميل المنتجات من ملف JSON"""
    # محاولة العثور على الملف بالطرق المختلفة
    json_paths = [
        Path("products_db.json"),  # المسار النسبي (يعمل في Streamlit عادة)
    ]
    
    # محاولة استخدام __file__ إذا كان متوفراً
    try:
        script_dir = Path(__file__).parent
        json_paths.insert(0, script_dir / "products_db.json")
    except:
        pass
    
    # محاولة كل مسار
    for json_path in json_paths:
        try:
            if json_path.exists():
                with open(json_path, "r", encoding="utf-8") as f:
                    products = json.load(f)
                
                if not products:
                    st.warning("ملف المنتجات فارغ!")
                    return []
                
                return products
        except FileNotFoundError:
            continue
        except json.JSONDecodeError as e:
            st.error(f"خطأ في قراءة ملف المنتجات (JSON غير صحيح): {str(e)}")
            return []
        except Exception as e:
            st.error(f"خطأ غير متوقع: {str(e)}")
            return []
    
    # إذا لم نجد الملف في أي مكان
    st.error("ملف المنتجات غير موجود! تأكد من وجود products_db.json في نفس مجلد app.py")
    return []

products = load_products()

# --- تصميم الواجهة ---
st.set_page_config(page_title="Skin Care Bot", layout="wide")
st.markdown("""
    <style>
    .main { background-color: #fff5f7; }
    .stButton>button { background-color: #ff4b6e; color: white; border-radius: 20px; }
    </style>
    """, unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### ✨ كوني جميلة، كوني أنتِ")
    st.image("https://cdn-icons-png.flaticon.com/512/3515/3515155.png", width=100)
    st.title("إعدادات الجمال")
    uploaded_file = st.file_uploader("📸 صور بشرتك للتحليل", type=['jpg', 'jpeg', 'png'])
    if st.button("تفريغ الشات"):
        st.session_state.messages = []

st.title("✨ Skin Care Bot - مساعدتك الذكية")

# --- منطق تحليل الصور ---
if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, caption="الصورة المرفوعة", width=300)
    if st.button("حلل صورتي"):
        with st.spinner(" SKIN Care Bot بتفحص الصورة..."):
            # هنا بنبعت الصورة للـ AI مع برومبت مخصص
            products = load_products()
            products_text = json.dumps(products, ensure_ascii=False)
            img_prompt = f"""
                أنت الآن خبير جلدية مصري متخصص. 
                أمامك صورة لبشرة مستخدم، وهذه هي قائمة المنتجات المتاحة لدينا فقط:
                {products_text}

                المطلوب منك:
                1. حلل الصورة بدقة وحدد نوع المشكلة (مثلاً: حبوب، آثار، جفاف).
                2. اقترح روتين (صباحي ومسائي) باستخدام المنتجات الموجودة في القائمة أعلاه "فقط".
                3. لو المشكلة مش موجود ليها حل في القائمة، قول للمستخدم "القائمة حالياً مفيش فيها اللي يناسبك بس ممكن تجرب..." وانصحه نصيحة عامة.
                4. اتكلم بلهجة مصرية ودودة جداً كأنك "بشرة خير".
                """

            response = model.generate_content(["حلل هذه الصورة للبشرة واذكر المشاكل المحتملة (جفاف، حبوب، الخ) بلهجة مصرية ودودة وانصح بمنتج من قائمة منتجاتنا.", image])
            st.info(response.text)


# تعريف "شخصية البوت" (System Instruction)
def get_system_prompt(products_data):
    """إنشاء System Prompt مع معلومات المنتجات"""
    products_info = "\n".join([
        f"- {p['brand']} {p['name']} ({p['type']}): للبشرة {p['skin_type']} | الفوائد: {p['benefits']} | السعر: {p['price_range']}"
        for p in products_data
    ])
    
    return f"""
أنت خبيرة عناية بالبشرة مصرية اسمك 'SkinCareBot'. 
وظيفتك مساعدة المستخدمين في فهم نوع بشرتهم واختيار الروتين المناسب.

المنتجات المتوفرة:
{products_info}

التعليمات:
- اتكلم بلهجة مصرية خفيفة وودودة.
- لو حد سأل عن منتجات، اقترح حاجات من القائمة اللي فوق واذكر التفاصيل بتاعتها (البراند، النوع، الفوائد، السعر).
- لازم تحذر المستخدم إنه لو فيه التهاب شديد لازم يروح لدكتور.
- اسأل المستخدم عن نوع بشرته لو مقالهاش.
- لما ترشح منتج، استخدم المعلومات اللي من القائمة وحاول تطابق نوع البشرة مع المنتج المناسب.
- اتكلم دايما مع المستخدم بصيغة الانثى.
"""

system_prompt = get_system_prompt(products)

# إدارة الشات في الـ Session
if "messages" not in st.session_state:
    st.session_state.messages = []

# عرض الرسائل القديمة
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# استقبال سؤال المستخدم
if prompt := st.chat_input("بشرتك محتاجة إيه النهاردة؟"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # إرسال السؤال لـ Gemini
    with st.chat_message("assistant"):
        try:
            # بناء السياق من الرسائل السابقة
            conversation_context = system_prompt + "\n\n"
            
            # إضافة الرسائل السابقة للسياق
            for msg in st.session_state.messages[:-1]:
                if msg["role"] == "user":
                    conversation_context += f"المستخدم: {msg['content']}\n\n"
                else:
                    conversation_context += f"المساعد: {msg['content']}\n\n"
            
            # إضافة الرسالة الحالية
            conversation_context += f"المستخدم: {prompt}\n\nالمساعد:"
            
            # إرسال الرسالة
            response = model.generate_content(conversation_context)
            
            response_text = response.text
            st.markdown(response_text)
            st.session_state.messages.append({"role": "assistant", "content": response_text})
        except Exception as e:
            error_msg = str(e)
            # إذا كان الخطأ متعلق بالموديل
            if "not found" in error_msg.lower() or "not supported" in error_msg.lower():
                st.error(f"الموديل غير متاح. الخطأ: {error_msg}")
                st.info("""
                **الحلول المقترحة:**
                1. تأكد من أن API Key صحيح ومن Google AI Studio
                2. جرب إنشاء API Key جديد من: https://makersuite.google.com/app/apikey
                3. تأكد من تفعيل Gemini API في Google Cloud Console
                4. جرب تحديث الصفحة
                """)
            else:
                st.error(f"حدث خطأ: {error_msg}")
            st.session_state.messages.append({"role": "assistant", "content": f"حدث خطأ: {error_msg}"})

