import streamlit as st
import google.generativeai as genai
from PIL import Image
import os

# ניסיון ייבוא ספריות (מניעת שגיאת ModuleNotFound)
try:
    from docx import Document
    from PyPDF2 import PdfReader
    LIB_READY = True
except ImportError:
    LIB_READY = False

# --- הגדרות שפה וכיווניות ---
LANG_CONFIG = {
    "עברית": {"dir": "rtl", "align": "right", "title": "EduCheck Smart 🌅", "login": "הזן קוד:", "btn": "התחבר", "reg": "רישום תלמיד", "save": "שמור", "types": ["פתוח", "אמריקאי", "השלמה", "מתמטיקה"]},
    "English": {"dir": "ltr", "align": "left", "title": "EduCheck Smart 🌅", "login": "Enter Code:", "btn": "Login", "reg": "Register", "save": "Save", "types": ["Open", "MCQ", "Blanks", "Math"]},
    "العربية": {"dir": "rtl", "align": "right", "title": "EduCheck Smart 🌅", "login": "أدخل الرمز:", "btn": "دخول", "reg": "تسجيل طالب", "save": "حفظ", "types": ["مفتوح", "اختيار", "إكمال", "رياضيات"]},
    "Français": {"dir": "ltr", "align": "left", "title": "EduCheck Smart 🌅", "login": "Code:", "btn": "Entrer", "reg": "S'inscrire", "save": "Sauver", "types": ["Ouvert", "QCM", "Trous", "Maths"]},
    "Español": {"dir": "ltr", "align": "left", "title": "EduCheck Smart 🌅", "login": "Código:", "btn": "Entrar", "reg": "Registro", "save": "Guardar", "types": ["Abierto", "Test", "Completar", "Mates"]},
    "中文": {"dir": "ltr", "align": "left", "title": "EduCheck Smart 🌅", "login": "代码:", "btn": "登录", "reg": "注册", "save": "保存", "types": ["问答", "选择", "填空", "数学"]}
}

st.set_page_config(page_title="EduCheck Smart", layout="wide")

if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "teacher_id" not in st.session_state: st.session_state.teacher_id = None

lang = st.sidebar.selectbox("🌐 Language", list(LANG_CONFIG.keys()))
L = LANG_CONFIG[lang]

# עיצוב בהיר קריא
st.markdown(f"""
<style>
    .stApp {{ background-color: white; color: black; direction: {L['dir']}; text-align: {L['align']}; }}
    [data-testid="stSidebar"] {{ direction: {L['dir']}; }}
    .main-header {{ text-align: center; color: #2c3e50; font-size: 2.5rem; font-weight: bold; border-bottom: 2px solid #eee; padding: 10px; }}
</style>
""", unsafe_allow_html=True)

if not LIB_READY:
    st.error("Missing Libraries! Please add requirements.txt to GitHub.")
    st.stop()

# --- מסך כניסה ---
if not st.session_state.logged_in:
    st.markdown(f"<h1 class='main-header'>{L['title']}</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        code = st.text_input(L['login'], type="password")
        if st.button(L['btn']):
            st.session_state.logged_in = True
            st.session_state.teacher_id = code
            st.rerun()
    st.stop()

# --- אפליקציה ראשית ---
st.markdown(f"<h1 class='main-header'>{L['title']}</h1>", unsafe_allow_html=True)

if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("Missing Google API Key!")
    st.stop()

base_path = f"data_{st.session_state.teacher_id}"
if not os.path.exists(base_path): os.makedirs(base_path)

# רישום תלמיד
with st.sidebar.expander(f"➕ {L['reg']}"):
    name = st.text_input("Name:")
    files = st.file_uploader("3 Samples", type=['png', 'jpg', 'jpeg'], accept_multiple_files=True)
    if st.button(L['save']):
        if name and len(files) >= 3:
            p = os.path.join(base_path, name)
            if not os.path.exists(p): os.makedirs(p)
            for i, f in enumerate(files[:3]):
                Image.open(f).save(os.path.join(p, f"sample_{i}.png"))
            st.success("Saved!")
            st.rerun()

# בדיקת מבחן
students = sorted(os.listdir(base_path))
if students:
    c1, c2 = st.columns([1, 1.5])
    with c1:
        s_target = st.selectbox("Student:", students)
        e_type = st.radio("Type:", L['types'])
        rubric = st.text_area("Rubric:", height=150)
    with c2:
        exam = st.file_uploader("Upload Exam", type=['png', 'jpg', 'jpeg', 'pdf', 'docx'])
        cam = st.camera_input("Scan")
    
    if st.button("Check 🚀"):
        src = cam if cam else exam
        if src and rubric:
            with st.spinner("Analyzing handwriting..."):
                s_dir = os.path.join(base_path, s_target)
                samples = [Image.open(os.path.join(s_dir, f)) for f in os.listdir(s_dir) if f.startswith("sample_")]
                
                model = genai.GenerativeModel('gemini-1.5-flash')
                prompt = f"Grade this {e_type} for {s_target}. IMPORTANT: Use ONLY the 3 handwriting samples to identify the student's letters. Match the strokes. Rubric: {rubric}. Answer in {lang}."
                
                response = model.generate_content([prompt] + samples + [Image.open(src)])
                st.balloons()
                st.write(response.text)
