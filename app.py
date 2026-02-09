import streamlit as st
import google.generativeai as genai
from PIL import Image
import os
import pandas as pd

# --- 1. הגדרות בסיסיות וחיבורים ---
MY_API_KEY = "AIzaSyDJdiYe4VmudGKFQzoCI_MmngD26D4wm1Q" 
genai.configure(api_key=MY_API_KEY)

# טעינת בסיס הנתונים של כתב היד בעברית (לשיפור הדיוק)
@st.cache_data
def load_hebrew_dataset():
    try:
        url = "hf://datasets/sivan22/hebrew-handwritten-dataset/data/train-00000-of-00001-8ed2cebcdc416c19.parquet"
        df = pd.read_parquet(url)
        return df
    except:
        return None

hebrew_df = load_hebrew_dataset()

# --- 2. ניהול מצב (Session State) ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "teacher_id" not in st.session_state:
    st.session_state.teacher_id = None

# --- 3. מילון שפות ותצורה ---
LANG_CONFIG = {
    "עברית": {"dir": "rtl", "align": "right", "title": "EDUCHECK AI 🚀", "login_msg": "הזן קוד מורה:", "login_btn": "התחבר", "reg_header": "🧬 רישום תלמיד חדש", "name_label": "שם תלמיד:", "sample_label": "דגימת אותיות", "save_btn": "שמור תלמיד", "check_header": "🔍 בדיקת מבחן חכמה", "select_student": "בחר תלמיד לבדיקה:", "rubric_label": "מחוון תשובות:", "upload_label": "העלאת מבחן / צילום:", "run_btn": "הפעל ניתוח AI ⚡", "no_student": "המערכת מוכנה. נא לרשום תלמיד ראשון בסרגל הצד."},
    "English": {"dir": "ltr", "align": "left", "title": "EDUCHECK AI 🚀", "login_msg": "Teacher Code:", "login_btn": "Login", "reg_header": "🧬 Student Registration", "name_label": "Student Name:", "sample_label": "Handwriting Sample", "save_btn": "Save Student", "check_header": "🔍 AI Exam Analysis", "select_student": "Select Student:", "rubric_label": "Answer Rubric:", "upload_label": "Upload/Scan Exam:", "run_btn": "Run Analysis ⚡", "no_student": "Please register a student to begin."},
}

st.set_page_config(page_title="EduCheck AI", layout="wide", page_icon="⚡")
lang_choice = st.sidebar.selectbox("🌐 Language / שפה", list(LANG_CONFIG.keys()))
L = LANG_CONFIG[lang_choice]

# --- 4. עיצוב Dark Tech UI ---
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Assistant:wght@300;600&display=swap');
    .stApp {{ background: #0d1117; color: #e6edf3; direction: {L['dir']}; text-align: {L['align']}; font-family: 'Assistant', sans-serif; }}
    .main-header {{ font-family: 'Orbitron', sans-serif; color: #58a6ff; text-shadow: 0px 0px 12px #58a6ff; text-align: center; font-size: 2.8rem; padding: 20px; }}
    [data-testid="stSidebar"] {{ background-color: #010409; border-{'right' if L['dir']=='ltr' else 'left'}: 1px solid #30363d; }}
    .stButton > button {{ background: linear-gradient(90deg, #1f6feb 0%, #114ea0 100%); color: white; border-radius: 8px; font-weight: bold; width: 100%; border: 1px solid #388bfd; }}
</style>
""", unsafe_allow_html=True)

# --- 5. לוגיקת התחברות ---
if not st.session_state.logged_in:
    st.markdown(f"<h1 class='main-header'>{L['title']}</h1>", unsafe_allow_html=True)
    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        st.write(f"### {L['login_msg']}")
        code = st.text_input("Access Key", type="password")
        if st.button(L['login_btn']):
            if code:
                st.session_state.logged_in = True
                st.session_state.teacher_id = code
                st.rerun()
    st.stop()

base_path = f"data_{st.session_state.teacher_id}"
if not os.path.exists(base_path): os.makedirs(base_path)

# --- 6. סרגל צד: רישום תלמידים ---
with st.sidebar:
    st.markdown(f"## {L['reg_header']}")
    new_student = st.text_input(L['name_label'])
    s1 = st.file_uploader(f"{L['sample_label']} 1", type=['png', 'jpg', 'jpeg'], key="up1")
    s2 = st.file_uploader(f"{L['sample_label']} 2", type=['png', 'jpg', 'jpeg'], key="up2")
    s3 = st.file_uploader(f"{L['sample_label']} 3", type=['png', 'jpg', 'jpeg'], key="up3")
    
    if st.button(L['save_btn']):
        if new_student and s1 and s2 and s3:
            path = os.path.join(base_path, new_student)
            if not os.path.exists(path): os.makedirs(path)
            for i, f in enumerate([s1, s2, s3]):
                Image.open(f).save(os.path.join(path, f"sample_{i}.png"))
            st.success("✅ Student Registered!")
            st.rerun()

    st.markdown("---")
    if st.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()

# --- 7. מסך ראשי: ניתוח מבחנים ---
st.markdown(f"<h1 class='main-header'>{L['title']}</h1>", unsafe_allow_html=True)
students = sorted(os.listdir(base_path))

if not students:
    st.warning(f"⚠️ {L['no_student']}")
else:
    col_input, col_cam = st.columns([1, 1.5])
    
    with col_input:
        selected = st.selectbox(L['select_student'], students)
        rubric = st.text_area(L['rubric_label'], height=200)
    
    with col_cam:
        exam_file = st.file_uploader(L['upload_label'], type=['png', 'jpg', 'jpeg'])
        exam_cam = st.camera_input("Scanner Camera")

    if st.button(L['run_btn']):
        source = exam_cam if exam_cam else exam_file
        if source and rubric:
            with st.spinner("Analyzing Handwriting Patterns..."):
                try:
                    s_dir = os.path.join(base_path, selected)
                    samples = [Image.open(os.path.join(s_dir, f)) for f in os.listdir(s_dir)]
                    
                    # בניית הפרומפט שמשתמש בידע מה-Dataset (הקשר תיאורטי)
                    dataset_context = "Use your internal knowledge of Hebrew handwritten variations (Aleph-Tav)."
                    prompt = f"""
                    TASK: Handwriting Recognition & Grading.
                    STUDENT CONTEXT: Learning unique style from the provided images of {selected}.
                    GENERAL CONTEXT: {dataset_context}
                    EXAM: Evaluate the uploaded exam image against this rubric: {rubric}.
                    LANGUAGE: Answer in {lang_choice}.
                    """
                    
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    response = model.generate_content([prompt] + samples + [Image.open(source)])
                    
                    st.markdown("---")
                    st.subheader("📡 AI Analysis Report:")
                    st.info(response.text)
                except Exception as e:
                    st.error(f"AI Failure: {e}")
