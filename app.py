import streamlit as st
import google.generativeai as genai
from PIL import Image
import os

# --- 1. הגדרות שפה ותפריטים ---
LANG_DICT = {
    "עברית": {
        "dir": "rtl", "align": "right", "title": "EduCheck Sunset 🌅", 
        "sub": "מערכת בדיקה חכמה באווירת שקיעה", "teacher_zone": "🔑 מרחב המורה",
        "id_label": "קוד גישה:", "student_reg": "📝 רישום תלמיד חדש",
        "student_name_label": "שם התלמיד:", "upload_samples": "העלה 3 דגימות כתב יד:",
        "save_btn": "שמור מאגר", "select_student": "👤 בחר תלמיד:",
        "exam_type": "📝 סוג המבחן:", 
        "types": ["מבחן פתוח", "מבחן אמריקאי", "השלמת משפטים", "נכון/לא נכון", "חישובים ומתמטיקה"],
        "exam_upload": "📸 העלאת המבחן", "rubric_label": "🎯 מחוון תשובות",
        "btn_check": "התחל בדיקת מומחה 🚀", "scan_msg": "מנתח נתונים באווירת בין הערביים...",
        "error_api": "מפתח API חסר!"
    },
    "English": {
        "dir": "ltr", "align": "left", "title": "EduCheck Sunset 🌅", 
        "sub": "Smart Grading in Sunset Vibes", "teacher_zone": "🔑 Teacher Zone",
        "id_label": "Access Code:", "student_reg": "📝 Student Registry",
        "student_name_label": "Student Name:", "upload_samples": "Upload 3 Samples:",
        "save_btn": "Save Database", "select_student": "👤 Select Student:",
        "exam_type": "📝 Exam Type:", 
        "types": ["Open Questions", "Multiple Choice", "Fill in Blanks", "True/False", "Math"],
        "exam_upload": "📸 Upload Exam", "rubric_label": "🎯 Rubric",
        "btn_check": "Start Expert Check 🚀", "scan_msg": "Analyzing data...",
        "error_api": "API Key Missing!"
    },
    "العربية": {
        "dir": "rtl", "align": "right", "title": "إيدوشيك الغروب 🌅", 
        "sub": "تصحيح ذكي بأجواء هادئة", "teacher_zone": "🔑 منطقة المعلم",
        "id_label": "رمز الدخول:", "student_reg": "📝 تسجيل طالب جديد",
        "student_name_label": "اسم الطالب:", "upload_samples": "تحميل 3 نماذج للخط:",
        "save_btn": "حفظ القاعدة", "select_student": "👤 اختر الطالب:",
        "exam_type": "📝 نوع الامتحان:", 
        "types": ["امتحان مفتوح", "امتحان أمريكي", "إكمال الجمل", "صح/خطأ", "رياضيات"],
        "exam_upload": "📸 تحميل الامتحان", "rubric_label": "🎯 نموذج الإجابة",
        "btn_check": "ابدأ التصحيح 🚀", "scan_msg": "جاري التحليل...",
        "error_api": "رمز API مفقود!"
    }
}

st.set_page_config(page_title="EduCheck Sunset", layout="wide", page_icon="🌅")
selected_lang = st.sidebar.selectbox("🌐 שפה / Language", ["עברית", "English", "العربية"])
L = LANG_DICT[selected_lang]

# --- 2. עיצוב Sunset Edition (CSS) ---
st.markdown(f"""
<style>
    .stApp {{
        background: linear-gradient(135deg, #2C3E50 0%, #FD746C 100%);
        color: white;
        direction: {L['dir']};
        text-align: {L['align']};
    }}
    .main-header {{
        background: linear-gradient(90deg, #FFD194 0%, #D1913C 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3.5rem;
        font-weight: 900;
        text-align: center;
        padding: 20px;
    }}
    div.stButton > button {{
        background: linear-gradient(45deg, #FD746C, #FF9068);
        border-radius: 12px;
        color: white;
        border: none;
        height: 3.5em;
        font-weight: bold;
        width: 100%;
        box-shadow: 0px 4px 10px rgba(0,0,0,0.2);
    }}
    [data-testid="stSidebar"] {{ background-color: rgba(44, 62, 80, 0.8); }}
    .stTextArea textarea, .stTextInput input, .stSelectbox select {{
        background-color: rgba(255, 255, 255, 0.1) !important;
        color: white !important;
        border: 1px solid #FD746C !important;
    }}
</style>
""", unsafe_allow_html=True)

# --- 3. חיבור ל-API ---
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error(L["error_api"])
    st.stop()

st.markdown(f"<h1 class='main-header'>{L['title']}</h1>", unsafe_allow_html=True)

# --- 4. ניהול נתונים (סיידבר) ---
st.sidebar.title(L["teacher_zone"])
teacher_id = st.sidebar.text_input(L["id_label"], type="password")

if not teacher_id:
    st.stop()

base_path = f"data_{teacher_id}"
if not os.path.exists(base_path): os.makedirs(base_path)

with st.sidebar.expander(L["student_reg"]):
    reg_name = st.text_input(L["student_name_label"], key="reg_name_input")
    s1 = st.file_uploader("דגימה 1", type=['png', 'jpg', 'jpeg'], key="s1")
    s2 = st.file_uploader("דגימה 2", type=['png', 'jpg', 'jpeg'], key="s2")
    s3 = st.file_uploader("דגימה 3", type=['png', 'jpg', 'jpeg'], key="s3")
    if st.button(L["save_btn"]):
        if reg_name and s1 and s2 and s3:
            path = os.path.join(base_path, reg_name)
            if not os.path.exists(path): os.makedirs(path)
            for i, s in enumerate([s1, s2, s3]):
                Image.open(s).save(os.path.join(path, f"{i}.png"))
            st.success("✅ נשמר")
            st.rerun()

# --- 5. מסך העבודה הראשי ---
st.divider()
students = sorted(os.listdir(base_path))
col1, col2, col3 = st.columns(3)

with col1:
    st.subheader(L["select_student"])
    student_name = st.selectbox("", [""] + students, label_visibility="collapsed")
    st.write(L["exam_type"])
    e_type = st.radio("", L["types"], label_visibility="collapsed")

with col2:
    st.subheader(L["exam_upload"])
    exam_file = st.file_uploader("", type=['png', 'jpg', 'jpeg'], key="main_exam_up")

with col3:
    st.subheader(L["rubric_label"])
    rubric = st.text_area("", placeholder="הכנס מחוון תשובות...", height=150)

if st.button(L["btn_check"]):
    if student_name and exam_file and rubric:
        with st.status(L["scan_msg"]):
            try:
                student_dir = os.path.join(base_path, student_name)
                samples = [Image.open(os.path.join(student_dir, f)) for f in os.listdir(student_dir)]
                
                model = genai.GenerativeModel('gemini-1.5-flash')
                exam_img = Image.open(exam_file)
                
                prompt = f"""
                You are a professional teacher. 
                Task: Grade a {e_type} exam for the student {student_name}.
                1. Reference the 3 handwriting samples provided to accurately read the student's script.
                2. Evaluate the exam image based on this rubric: {rubric}.
                3. Special Instruction for {e_type}: Ensure high accuracy for this specific format.
                4. Respond ONLY in {selected_lang}. Include a final score and constructive feedback.
                """
                
                response = model.generate_content([prompt] + samples + [exam_img])
                st.balloons()
                st.markdown(f"### 📋 תוצאות עבור {student_name}")
                st.write(response.text)
            except Exception as e:
                st.error(f"Error: {e}")
    else:
        st.warning("נא למלא את כל השדות!")
