import streamlit as st
import google.generativeai as genai
from PIL import Image
import os

# --- 1. הגדרות שפה ומילון (כולל ערבית) ---
LANG_DICT = {
    "עברית": {
        "dir": "rtl", "align": "right", "title": "EduCheck Summer ☀️", 
        "sub": "בדיקת מבחנים בכיף ובקלות", "teacher_zone": "🍹 מרחב המורה",
        "id_label": "קוד גישה:", "student_reg": "📝 רישום תלמיד",
        "student_name_label": "שם התלמיד:", "upload_samples": "העלה 3 דגימות כתב יד:",
        "save_btn": "שמור מאגר אותיות", "select_student": "בחר תלמיד:",
        "exam_upload": "📸 העלאת המבחן", "rubric_label": "🎯 מחוון",
        "btn_check": "התחל בדיקה חכמה 🚀", "scan_msg": "מנתח את המבחן...",
        "error_api": "חסר מפתח API!"
    },
    "English": {
        "dir": "ltr", "align": "left", "title": "EduCheck Summer ☀️", 
        "sub": "Easy & Breezy Grading", "teacher_zone": "🍹 Teacher Zone",
        "id_label": "Access Code:", "student_reg": "📝 Student Registry",
        "student_name_label": "Student Name:", "upload_samples": "Upload 3 Samples:",
        "save_btn": "Save Handwriting", "select_student": "Select Student:",
        "exam_upload": "📸 Upload Exam", "rubric_label": "🎯 Rubric",
        "btn_check": "Start AI Analysis 🚀", "scan_msg": "Analyzing Exam...",
        "error_api": "Missing API Key!"
    },
    "العربية": {
        "dir": "rtl", "align": "right", "title": "إيدوشيك صيف ☀️", 
        "sub": "تصحيح الامتحانات بكل سهولة ومتعة", "teacher_zone": "🍹 منطقة المعلم",
        "id_label": "رمز الدخول:", "student_reg": "📝 تسجيل طالب جديد",
        "student_name_label": "اسم الطالب:", "upload_samples": "تحميل 3 نماذج للخط:",
        "save_btn": "حفظ قاعدة بيانات الخط", "select_student": "اختر الطالب:",
        "exam_upload": "📸 تحميل الامتحان", "rubric_label": "🎯 نموذج الإجابة",
        "btn_check": "ابدأ التصحيح الذكي 🚀", "scan_msg": "جاري تحليل الامتحان...",
        "error_api": "رمز API مفقود!"
    }
}

st.set_page_config(page_title="EduCheck Summer", layout="wide")

# בחירת שפה בסיידבר
selected_lang = st.sidebar.selectbox("🌐 שפה / Language / اللغة", ["עברית", "English", "العربية"])
L = LANG_DICT[selected_lang]

# --- 2. עיצוב ויישור (CSS) ---
st.markdown(f"""
    <style>
    .stApp {{
        background: linear-gradient(180deg, #FFEFBA 0%, #FFFFFF 100%);
        direction: {L['dir']};
        text-align: {L['align']};
    }}
    
    [data-testid="stSidebar"], .stTextArea, .stTextInput, .stSelectbox {{
        direction: {L['dir']} !important;
        text-align: {L['align']} !important;
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
        width: 100%;
        height: 3em;
        font-size: 1.2rem;
        font-weight: bold;
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
st.markdown(f"<p style='text-align: center; color: #E67E22; font-size: 1.2rem;'>{L['sub']}</p>", unsafe_allow_html=True)

# סיידבר
st.sidebar.title(L["teacher_zone"])
teacher_id = st.sidebar.text_input(L["id_label"], type="password")

if not teacher_id:
    st.stop()

base_path = f"data_{teacher_id}"
if not os.path.exists(base_path): os.makedirs(base_path)

# רישום תלמיד עם 3 דגימות נפרדות
with st.sidebar.expander(L["student_reg"]):
    reg_name = st.text_input(L["student_name_label"], key="reg_name")
    st.write(L["upload_samples"])
    s1 = st.file_uploader("Sample 1", type=['png', 'jpg', 'jpeg'], key="s1")
    s2 = st.file_uploader("Sample 2", type=['png', 'jpg', 'jpeg'], key="s2")
    s3 = st.file_uploader("Sample 3", type=['png', 'jpg', 'jpeg'], key="s3")
    
    if st.button(L["save_btn"]):
        if reg_name and s1 and s2 and s3:
            student_path = os.path.join(base_path, reg_name)
            if not os.path.exists(student_path): os.makedirs(student_path)
            for i, s in enumerate([s1, s2, s3]):
                with open(os.path.join(student_path, f"sample_{i}.png"), "wb") as f:
                    f.write(s.getbuffer())
            st.success("✅ Student Saved!")
            st.rerun()

# --- 4. ממשק עבודה מרכזי ---
st.markdown("---")
existing_students = os.listdir(base_path)
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(f"### 👤 {L['select_student']}")
    student_name = st.selectbox("", [""] + existing_students, label_visibility="collapsed")
    
with col2:
    st.markdown(f"### {L['exam_upload']}")
    exam_file = st.file_uploader("", type=['png', 'jpg', 'jpeg'], key="exam", label_visibility="collapsed")

with col3:
    st.markdown(f"### {L['rubric_label']}")
    rubric = st.text_area("", placeholder="...", height=150, key="rubric", label_visibility="collapsed")

if st.button(L["btn_check"]):
    if student_name and exam_file and rubric:
        with st.status(L["scan_msg"], expanded=True) as status:
            try:
                # טעינת 3 הדגימות מהתיקייה
                sample_images = []
                student_path = os.path.join(base_path, student_name)
                for img_name in os.listdir(student_path):
                    sample_images.append(Image.open(os.path.join(student_path, img_name)))
                
                model = genai.GenerativeModel('gemini-1.5-flash')
                exam_img = Image.open(exam_file)
                
                # הנחיה ל-AI הכוללת דרישה לשפה שנבחרה
                prompt = f"""
                You are a professional teacher.
                1. Look at the 3 handwriting samples for {student_name} to learn their script.
                2. Grade the exam image according to this rubric: {rubric}.
                3. Your entire response must be in {selected_lang}.
                """
                
                response = model.generate_content([prompt] + sample_images + [exam_img])
                
                status.update(label="✅ Analysis Complete!", state="complete")
                st.balloons()
                st.success(response.text)
            except Exception as e:
                st.error(f"Error: {e}")
