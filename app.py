import streamlit as st
import google.generativeai as genai
from PIL import Image
import os

# --- הגדרת המפתח האישי שלך ---
MY_API_KEY = "AIzaSyDJdiYe4VmudGKFQzoCI_MmngD26D4wm1Q" 
genai.configure(api_key=MY_API_KEY)

# --- ניהול מצב כניסה (Session State) ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "teacher_id" not in st.session_state:
    st.session_state.teacher_id = None

# --- מילון שפות וכיווניות ---
LANG_CONFIG = {
    "עברית": {"dir": "rtl", "align": "right", "title": "EDUCHECK AI 🚀", "login_msg": "הזן קוד מורה לכניסה למערכת:", "login_btn": "התחבר", "reg": "רישום תלמיד", "check": "ניתוח מבחן", "rubric": "מחוון תשובות", "btn": "הפעל בינה מלאכותית"},
    "English": {"dir": "ltr", "align": "left", "title": "EDUCHECK AI 🚀", "login_msg": "Enter Teacher Code to access system:", "login_btn": "Login", "reg": "Register Student", "check": "Analyze Exam", "rubric": "Answer Rubric", "btn": "Run AI Analysis"},
    "العربية": {"dir": "rtl", "align": "right", "title": "EDUCHECK AI 🚀", "login_msg": "أدخل رمز المعلم للدخول:", "login_btn": "دخول", "reg": "تسجيل طالب", "check": "تحليل الامتحان", "rubric": "نموذج الإجابة", "btn": "تشغيل الذكاء الاصطناعي"},
    "Français": {"dir": "ltr", "align": "left", "title": "EDUCHECK AI 🚀", "login_msg": "Entrez le code enseignant:", "login_btn": "Connexion", "reg": "S'inscrire", "check": "Analyser", "rubric": "Corrigé", "btn": "Lancer l'IA"},
    "Español": {"dir": "ltr", "align": "left", "title": "EDUCHECK AI 🚀", "login_msg": "Ingrese código de profesor:", "login_btn": "Entrar", "reg": "Registro", "check": "Analizar", "rubric": "Clave", "btn": "Ejecutar IA"},
    "中文": {"dir": "ltr", "align": "left", "title": "EDUCHECK AI 🚀", "login_msg": "输入教师代码以进入系统:", "login_btn": "登录", "reg": "注册", "check": "分析", "rubric": "评分标准", "btn": "运行人工智能"}
}

st.set_page_config(page_title="EduCheck AI", layout="wide", page_icon="⚡")

# בחירת שפה (בסיידבר)
lang = st.sidebar.selectbox("🌐 System Language", list(LANG_CONFIG.keys()))
L = LANG_CONFIG[lang]

# --- עיצוב טכנולוגי מרהיב (Dark Tech Mode) ---
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Assistant:wght@300;600&display=swap');
    
    .stApp {{
        background: radial-gradient(circle, #0d1117 0%, #010409 100%);
        color: #e6edf3;
        direction: {L['dir']};
        text-align: {L['align']};
        font-family: 'Assistant', sans-serif;
    }}
    
    .main-header {{
        font-family: 'Orbitron', sans-serif;
        color: #58a6ff;
        text-shadow: 0px 0px 10px #58a6ff;
        text-align: center;
        font-size: 3rem;
        padding: 30px;
        border-bottom: 1px solid #30363d;
    }}
    
    .stButton > button {{
        background: linear-gradient(135deg, #1f6feb 0%, #114ea0 100%);
        color: white;
        border: 1px solid #388bfd;
        border-radius: 8px;
        padding: 12px 24px;
        width: 100%;
        font-weight: bold;
        transition: 0.2s ease-in-out;
    }}
    
    .stButton > button:hover {{
        background: #388bfd;
        box-shadow: 0px 0px 15px #388bfd;
        transform: translateY(-2px);
    }}

    .stTextInput input, .stTextArea textarea {{
        background-color: #0d1117 !important;
        border: 1px solid #30363d !important;
        color: #c9d1d9 !important;
        border-radius: 6px !important;
    }}
</style>
""", unsafe_allow_html=True)

# --- 1. מסך כניסה (Login Screen) ---
if not st.session_state.logged_in:
    st.markdown(f"<h1 class='main-header'>{L['title']}</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.write(f"### {L['login_msg']}")
        teacher_code = st.text_input("Access Key", type="password")
        if st.button(L['login_btn']):
            if teacher_code:
                st.session_state.logged_in = True
                st.session_state.teacher_id = teacher_code
                st.rerun()
            else:
                st.error("Please enter a valid code.")
    st.stop()

# --- 2. ממשק המערכת (אחרי התחברות) ---
st.markdown(f"<h1 class='main-header'>{L['title']}</h1>", unsafe_allow_html=True)

# יצירת תיקיית נתונים לפי קוד המורה
base_path = f"db_{st.session_state.teacher_id}"
if not os.path.exists(base_path): os.makedirs(base_path)

# תפריט צד
choice = st.sidebar.radio("SYSTEM MENU", [L['check'], L['reg']])
if st.sidebar.button("Logout / יציאה"):
    st.session_state.logged_in = False
    st.rerun()

if choice == L['reg']:
    st.markdown(f"### 🧬 {L['reg']}")
    name = st.text_input("Student Identity (Name):")
    files = st.file_uploader("Upload 3 Handwriting DNA Samples", type=['png', 'jpg', 'jpeg'], accept_multiple_files=True)
    
    if st.button("INITIALIZE STUDENT"):
        if name and len(files) >= 3:
            p = os.path.join(base_path, name)
            if not os.path.exists(p): os.makedirs(p)
            for i, f in enumerate(files[:3]):
                Image.open(f).save(os.path.join(p, f"sample_{i}.png"))
            st.success(f"STUDENT {name} SYNCED TO SECURE DATABASE.")
        else:
            st.error("Protocol Error: Minimum 3 handwriting samples required.")

else:
    students = sorted(os.listdir(base_path))
    if not students:
        st.warning("Database empty. Please register students first.")
    else:
        col1, col2 = st.columns([1, 1.5])
        with col1:
            target = st.selectbox("Select Target Subject:", students)
            rubric = st.text_area(L['rubric'], height=180)
        
        with col2:
            exam = st.file_uploader("Scan Exam Document", type=['png', 'jpg', 'jpeg'])
            cam = st.camera_input("Optical Scanner")
            
        if st.button(L['btn']):
            source = cam if cam else exam
            if source and rubric:
                with st.spinner("AI Neural Processing... Decoding Ink"):
                    try:
                        s_dir = os.path.join(base_path, target)
                        samples = [Image.open(os.path.join(s_dir, f)) for f in os.listdir(s_dir)]
                        model = genai.GenerativeModel('gemini-1.5-flash')
                        
                        prompt = f"""
                        Handwriting Calibration Protocol:
                        1. Use the provided handwriting samples of '{target}' to learn their specific stroke style.
                        2. Read the handwritten exam document based ONLY on that learned style.
                        3. Grade the work according to this rubric: {rubric}.
                        4. Output a detailed report in {lang}.
                        """
                        
                        response = model.generate_content([prompt] + samples + [Image.open(source)])
                        st.markdown("---")
                        st.markdown("### 📡 AI Analysis Report:")
                        st.info(response.text)
                    except Exception as e:
                        st.error(f"System Failure: {e}")
