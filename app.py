import streamlit as st
import google.generativeai as genai
from PIL import Image
import os

# --- 1. הגדרות שפה ותרגומים ---
LANG_DICT = {
    "עברית": {
        "dir": "rtl", "align": "right", "title": "EduCheck Summer ☀️", "sub": "בדיקת מבחנים בכיף ובקלות",
        "teacher_zone": "🍹 מרחב המורה", "id_label": "קוד גישה:", "student_new": "+ תלמיד חדש",
        "student_list": "מי התלמיד?", "exam_upload": "📸 צילום המבחן", "rubric_label": "🎯 מה התשובות?",
        "btn_check": "בדוק לי את זה! 🌊", "style_label": "איך לבדוק?", "error_api": "חסר מפתח API!"
    },
    "English": {
        "dir": "ltr", "align": "left", "title": "EduCheck Summer ☀️", "sub": "Easy & Breezy Grading",
        "teacher_zone": "🍹 Teacher Lounge", "id_label": "Teacher ID:", "student_new": "+ New Student",
        "student_list": "Select Student:", "exam_upload": "📸 Upload Exam", "rubric_label": "🎯 Answer Key",
        "btn_check": "Grade it! 🌊", "style_label": "Grading Style:", "error_api": "Missing API Key!"
    },
    "العربية": {
        "dir": "rtl", "align": "right", "title": "إيدوشيك صيف ☀️", "sub": "تصحيح الامتحانات بكل سهولة",
        "teacher_zone": "🍹 منطقة المعلم", "id_label": "رمز الدخول:", "student_new": "+ طالب جديد",
        "student_list": "اختر طالب:", "exam_upload": "📸 تحميل الامتحان", "rubric_label": "🎯 نموذج الإجابة",
        "btn_check": "ابدأ التصحيح! 🌊", "style_label": "أسلوب التقييم:", "error_api": "رمز API مفقود!"
    }
}

st.set_page_config(page_title="EduCheck Summer", layout="wide", page_icon="☀️")

# בחירת שפה
selected_lang = st.sidebar.selectbox("🌐 Select Language / בחר שפה", ["עברית", "English", "العربية"])
L = LANG_DICT[selected_lang]

# --- 2. עיצוב קיצי ומרענן (CSS) ---
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Assistant:wght@400;700;800&family=Fredoka:wght@400;600&display=swap');
    
    .stApp {{
        background: linear-gradient(180deg, #FFEFBA 0%, #FFFFFF 100%);
        color: #2D3436;
        direction: {L['dir']};
        text-align: {L['align']};
        font-family: 'Fredoka', 'Assistant', sans-serif;
    }}
    
    /* כותרת קיצית */
    .main-header {{
        font-family: 'Fredoka', sans-serif;
        background: linear-gradient(90deg, #FF8C00 0%, #FAD02E 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 4rem;
        font-weight: 800;
        text-align: center;
        margin-bottom: 5px;
        filter: drop-shadow(2px 2px 4px rgba(0,0,0,0.1));
    }}
    
    /* עיצוב כפתור - צבעי ים */
    div.stButton > button {{
        background: linear-gradient(45deg, #00B4DB, #0083B0);
        border: none;
        color: white;
        padding: 15px 30px;
        border-radius: 30px;
        font-size: 20px;
        font-weight: bold;
        box-shadow: 0 4px 15px rgba(0,131,176,0.3);
        transition: 0.3s ease;
    }}
    
    div.stButton > button:hover {{
        transform: translateY(-3px);
        box-shadow: 0 6px 20px rgba(0,131,176,0.5);
    }}

    /* תיבות תוכן - לבן שקוף */
    [data-testid="stVerticalBlock"] > div {{
        background: rgba(255, 255, 255, 0.7);
        padding: 25px;
        border-radius: 25px;
        border: 2px solid #FFEAA7;
        box-shadow: 0 10px 30px rgba(0,0,0,0.05);
    }}
    
    /* סיידבר - צהוב בהיר */
    [data-testid="stSidebar"] {{
        background-color: #FFF9E3;
        border-{ 'left' if L['dir'] == 'rtl' else 'right' }: 3px solid #FAD02E;
    }}

    /* שינוי צבע לטקסט בסיידבר */
    .st-emotion-cache-1ky9p07 {{
        color: #2D3436;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 3. חיבור ל-API ---
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error(L["error_api"])
    st.stop()

# --- 4. מבנה האתר ---
st.markdown(f"<h1 class='main-header'>{L['title']}</h1>", unsafe_allow_html=True)
st.markdown(f"<p style='text-align: center; color: #E67E22; font-size: 1.4rem; font-weight: 600;'>{L['sub']}</p>", unsafe_allow_html=True)

# סיידבר
st.sidebar.markdown(f"## {L['teacher_zone']}")
teacher_id = st.sidebar.text_input(L["id_label"], type="password")

if not teacher_id:
    st.info("☀️ ברוכים הבאים! אנא הכניסו קוד כדי להתחיל")
    st.image("https://img.freepik.com/free-vector/summer-elements-collection_23-2148155255.jpg", use_column_width=True)
    st.stop()

teacher_folder = f"data_{teacher_id}"
if not os.path.exists(teacher_folder): os.makedirs(teacher_folder)

st.sidebar.divider()
grading_style = st.sidebar.text_area(L["style_label"], placeholder="למשל: תהיה נחמד במיוחד...")
existing_students = os.listdir(teacher_folder)
selected_student = st.sidebar.selectbox(L["student_list"], existing_students if existing_students else ["עדיין אין תלמידים"])

# --- 5. אזור העבודה ---
col1, col2 = st.columns(2, gap="large")

with col1:
    st.markdown(f"### {L['exam_upload']}")
    exam_file = st.file_uploader("", type=['png', 'jpg', 'jpeg'])

with col2:
    st.markdown(f"### {L['rubric_label']}")
    rubric = st.text_area("", placeholder="כתבו כאן את התשובות הנכונות..." , height=150)

st.markdown("<br>", unsafe_allow_html=True)

if st.button(L["btn_check"]):
    if exam_file and rubric:
        with st.status("🍦 מנתח את המבחן... רק רגע", expanded=True) as status:
            try:
                model = genai.GenerativeModel('gemini-1.5-flash')
                img_exam = Image.open(exam_file)
                
                prompt = f"""
                You are a friendly teacher at a summer school. 
                Task: Grade this handwritten exam.
                Student: {selected_student}
                Rubric: {rubric}
                Personal Style: {grading_style}
                
                Language: {selected_lang}. 
                Be very encouraging, use a positive summer-themed tone.
                Structure: Grade, Strengths, and Tips for next time.
                """
                
                response = model.generate_content([prompt, img_exam])
                status.update(label="✅ סיימנו!", state="complete")
                
                st.balloons() # חגיגה של בלונים בסיום
                st.markdown(f"## 📋 תוצאות הבדיקה עבור {selected_student}")
                st.success(response.text)
                
            except Exception as e:
                st.error(f"אופס, משהו השתבש: {e}")
    else:
        st.warning("אל תשכח להעלות מבחן ולכתוב מחוון!")
