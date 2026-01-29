import streamlit as st
import google.generativeai as genai
from PIL import Image
import os

# --- 1. הגדרות שפה ומילון ---
LANG_DICT = {
    "עברית": {
        "dir": "rtl", "align": "right", "title": "EduCheck Summer ☀️", 
        "sub": "בדיקת מבחנים בכיף ובקלות", "teacher_zone": "🍹 מרחב המורה",
        "id_label": "קוד גישה:", "student_reg": "📝 רישום תלמיד",
        "student_name_label": "שם התלמיד:", "upload_samples": "העלה 3 דגימות כתב יד:",
        "save_btn": "שמור מאגר אותיות", "select_student": "בחר תלמיד:",
        "exam_type": "סוג המבחן:", "types": ["מבחן רגיל (פתוח)", "מבחן אמריקאי"],
        "exam_upload": "📸 העלאת המבחן", "rubric_label": "🎯 מחוון / תשובות נכונות",
        "btn_check": "התחל בדיקה חכמה 🚀", "scan_msg": "מבצע סריקה עמוקה וחידוד ראייה...",
        "error_api": "חסר מפתח API!"
    },
    "English": {
        "dir": "ltr", "align": "left", "title": "EduCheck Summer ☀️", 
        "sub": "Easy & Breezy Grading", "teacher_zone": "🍹 Teacher Lounge",
        "id_label": "Access Code:", "student_reg": "📝 Student Registry",
        "student_name_label": "Student Name:", "upload_samples": "Upload 3 Samples:",
        "save_btn": "Save Handwriting", "select_student": "Select Student:",
        "exam_type": "Exam Type:", "types": ["Open Questions", "Multiple Choice"],
        "exam_upload": "📸 Upload Exam", "rubric_label": "🎯 Rubric",
        "btn_check": "Start Smart Analysis 🚀", "scan_msg": "Deep scanning...",
        "error_api": "Missing API Key!"
    },
    "العربية": {
        "dir": "rtl", "align": "right", "title": "إيدوشيك صيف ☀️", 
        "sub": "تصحيح الامتحانات بكل سهولة ومتعة", "teacher_zone": "🍹 منطقة المعلم",
        "id_label": "رمز الدخول:", "student_reg": "📝 تسجيل طالب جديد",
        "student_name_label": "اسم الطالب:", "upload_samples": "تحميل 3 نماذج للخط:",
        "save_btn": "حفظ قاعدة البيانات", "select_student": "اختر الطالب:",
        "exam_type": "نوع الامتحان:", "types": ["امتحان عادي", "امتحان أمريكي"],
        "exam_upload": "📸 تحميل الامتحان", "rubric_label": "🎯 نموذج الإجابة",
        "btn_check": "ابدأ التصحيح 🚀", "scan_msg": "جاري التحليل...",
        "error_api": "رمز API مفقود!"
    }
}

st.set_page_config(page_title="EduCheck Summer", layout="wide", page_icon="☀️")

# בחירת שפה
selected_lang = st.sidebar.selectbox("🌐 Language", ["עברית", "English", "العربية"])
L = LANG_DICT[selected_lang]

# --- 2. עיצוב קיצי מלוטש (CSS) ---
st.markdown(f"""
<style>
    .stApp {{
        background: linear-gradient(180deg, #FFEFBA 0%, #FFFFFF 100%);
        direction: {L['dir']};
        text-align: {L['align']};
    }}
    .main-header {{
        background: linear-gradient(90deg, #FF8C00 0%, #FAD02E 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3.5rem;
        font-weight: 800;
        text-align: center;
    }}
    div.stButton > button {{
        background: linear-gradient(45deg, #FF8C00, #FAD02E);
        border-radius: 20px;
        color: white;
        border: none;
        height: 3.5em;
        font-weight: bold;
        width: 100%;
    }}
    [data-testid="stSidebar"] {{
        direction: {L['dir']};
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

# --- 4. סיידבר: ניהול מורים ותלמידים ---
st.sidebar.title(L["teacher_zone"])
teacher_id = st.sidebar.text_input(L["id_label"], type="password")

if not teacher_id:
    st.sidebar.info("נא להזין קוד גישה")
    st.stop()

base_path = f"data_{teacher_id}"
if not os.path.exists(base_path): os.makedirs(base_path)

with st.sidebar.expander(L["student_reg"]):
    reg_name = st.text_input(L["student_name_label"])
    s1 = st.file_uploader("דגימה 1", type=['png', 'jpg', 'jpeg'], key="s1")
    s2 = st.file_uploader("דגימה 2", type=['png', 'jpg', 'jpeg'], key="s2")
    s3 = st.file_uploader("דגימה 3", type=['png', 'jpg', 'jpeg'], key="s3")
    
    if st.button(L["save_btn"]):
        if reg_name and s1 and s2 and s3:
            path = os.path.join(base_path, reg_name)
            if not os.path.exists(path): os.makedirs(path)
            for i, s in enumerate([s1, s2, s3]):
                Image.open(s).save(os.path.join(path, f"{i}.png"))
            st.success("✅ נרשם!")
            st.rerun()

# --- 5. ממשק בדיקה מרכזי ---
st.divider()
students = sorted(os.listdir(base_path))
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(f"### {L['select_student']}")
    student_name = st.selectbox("", [""] + students, label_visibility="collapsed")
    st.markdown(f"**{L['exam_type']}**")
    e_type = st.radio("", L["types"], label_visibility="collapsed")

with col2:
    st.markdown(f"### {L['exam_upload']}")
    exam_file = st.file_uploader("", type=['png', 'jpg', 'jpeg'], key="exam")

with col3:
    st.markdown(f"### {L['rubric_label']}")
    rubric = st.text_area("", placeholder="הכנס מחוון תשובות...", height=150)

if st.button(L["btn_check"]):
    if student_name and exam_file and rubric:
        with st.status(L["scan_msg"]):
            try:
                # טעינת 3 דגימות כתב יד
                student_dir = os.path.join(base_path, student_name)
                samples = [Image.open(os.path.join(student_dir, f)) for f in os.listdir(student_dir)]
                
                # הגדרת ה-AI
                model = genai.GenerativeModel('gemini-1.5-flash')
                exam_img = Image.open(exam_file)
                
                # פרומפט משוכלל לדיוק מקסימלי
                prompt = f"""
                You are an expert teacher grading a {e_type}.
                1. Use the provided 3 handwriting samples of {student_name} to calibrate your OCR.
                2. Read the handwritten exam image carefully.
                3. Compare the answers to this rubric: {rubric}.
                4. Provide a grade and detailed feedback.
                5. Respond ONLY in {selected_lang}.
                """
                
                response = model.generate_content([prompt] + samples + [exam_img])
                st.balloons()
                st.markdown(f"## תוצאות עבור {student_name}")
                st.success(response.text)
            except Exception as e:
                st.error(f"שגיאה: {e}")
    else:
        st.warning("נא למלא את כל הפרטים!")
