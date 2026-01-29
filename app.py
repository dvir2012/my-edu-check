import streamlit as st
import google.generativeai as genai
from PIL import Image
import os

# 1. הגדרות שפה ומילון
LANG_DICT = {
    "עברית": {"dir": "rtl", "align": "right", "title": "EduCheck Summer ☀️", "select_student": "בחר תלמיד:", "exam_type": "סוג המבחן:", "types": ["מבחן רגיל (פתוח)", "מבחן אמריקאי"], "exam_upload": "📸 העלאת המבחן", "rubric_label": "🎯 מחוון / תשובות", "btn_check": "התחל בדיקה 🚀"},
    "English": {"dir": "ltr", "align": "left", "title": "EduCheck Summer ☀️", "select_student": "Select Student:", "exam_type": "Exam Type:", "types": ["Open Questions", "Multiple Choice"], "exam_upload": "📸 Upload Exam", "rubric_label": "🎯 Rubric", "btn_check": "Start Analysis 🚀"},
    "العربية": {"dir": "rtl", "align": "right", "title": "إيدوشيك صيف ☀️", "select_student": "اختر الطالب:", "exam_type": "نوع الامتحان:", "types": ["امتحان عادي", "امتحان أمريكي"], "exam_upload": "📸 تحميل الامتحان", "rubric_label": "🎯 نموذج الإجابة", "btn_check": "ابدأ التصحيح 🚀"}
}

st.set_page_config(page_title="EduCheck Summer", layout="wide")
selected_lang = st.sidebar.selectbox("🌐 Language", ["עברית", "English", "العربية"])
L = LANG_DICT[selected_lang]

# 2. עיצוב CSS פשוט (בלי מירכאות משולשות שיכולות להישבר)
st.markdown("<style> .stApp { direction: " + L['dir'] + "; text-align: " + L['align'] + "; } </style>", unsafe_allow_html=True)

# 3. חיבור ל-API
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("Missing API Key in Secrets!")
    st.stop()

st.title(L["title"])

# 4. סיידבר לניהול תלמידים
teacher_id = st.sidebar.text_input("Access Code / קוד גישה", type="password")
if not teacher_id:
    st.info("Please enter your Access Code in the sidebar")
    st.stop()

base_path = f"data_{teacher_id}"
if not os.path.exists(base_path): os.makedirs(base_path)

with st.sidebar.expander("📝 רישום תלמיד / Student Registry"):
    reg_name = st.text_input("שם התלמיד:")
    s1 = st.file_uploader("דגימה 1", type=['png', 'jpg', 'jpeg'], key="s1")
    s2 = st.file_uploader("דגימה 2", type=['png', 'jpg', 'jpeg'], key="s2")
    s3 = st.file_uploader("דגימה 3", type=['png', 'jpg', 'jpeg'], key="s3")
    if st.button("שמור תלמיד"):
        if reg_name and s1 and s2 and s3:
            path = os.path.join(base_path, reg_name)
            if not os.path.exists(path): os.makedirs(path)
            for i, s in enumerate([s1, s2, s3]):
                Image.open(s).save(os.path.join(path, f"{i}.png"))
            st.success("נשמר!")
            st.rerun()

# 5. ממשק בדיקה
st.divider()
students = sorted(os.listdir(base_path))
col1, col2, col3 = st.columns(3)

with col1:
    student_name = st.selectbox(L["select_student"], [""] + students)
    e_type = st.radio(L["exam_type"], L["types"])

with col2:
    exam_file = st.file_uploader(L["exam_upload"], type=['png', 'jpg', 'jpeg'])

with col3:
    rubric = st.text_area(L["rubric_label"], placeholder="הדבק כאן את המחוון...")

if st.button(L["btn_check"]):
    if student_name and exam_file and rubric:
        try:
            # טעינת דגימות
            samples = [Image.open(os.path.join(base_path, student_name, f)) for f in os.listdir(os.path.join(base_path, student_name))]
            
            # הפעלת Gemini
            model = genai.GenerativeModel('gemini-1.5-flash')
            exam_img = Image.open(exam_file)
            prompt = f"Grade this {e_type} for student {student_name} using this rubric: {rubric}. Use the handwriting samples to recognize the text. Respond in {selected_lang}."
            
            response = model.generate_content([prompt] + samples + [exam_img])
            st.balloons()
            st.success(response.text)
        except Exception as e:
            st.error(f"Error: {e}")
    else:
        st.warning("נא למלא את כל השדות!")
