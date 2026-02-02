import streamlit as st
import google.generativeai as genai
from PIL import Image
import os

# --- הגדרת המפתח האישי שלך ---
MY_API_KEY = "AIzaSyDJdiYe4VmudGKFQzoCI_MmngD26D4wm1Q" 
genai.configure(api_key=MY_API_KEY)

# --- מילון שפות וכיווניות ---
LANG_CONFIG = {
    "עברית": {"dir": "rtl", "align": "right", "title": "EDUCHECK AI 🚀", "reg": "רישום תלמיד", "check": "ניתוח מבחן", "rubric": "מחוון תשובות", "btn": "הפעל בינה מלאכותית"},
    "English": {"dir": "ltr", "align": "left", "title": "EDUCHECK AI 🚀", "reg": "Register Student", "check": "Analyze Exam", "rubric": "Answer Rubric", "btn": "Run AI Analysis"},
    "العربية": {"dir": "rtl", "align": "right", "title": "EDUCHECK AI 🚀", "reg": "تسجيل طالب", "check": "تحليل الامتحان", "rubric": "نموذج الإجابة", "btn": "تشغيل الذكاء الاصطناعي"},
    "Français": {"dir": "ltr", "align": "left", "title": "EDUCHECK AI 🚀", "reg": "S'inscrire", "check": "Analyser", "rubric": "Corrigé", "btn": "Lancer l'IA"},
    "Español": {"dir": "ltr", "align": "left", "title": "EDUCHECK AI 🚀", "reg": "Registro", "check": "Analizar", "rubric": "Clave", "btn": "Ejecutar IA"},
    "中文": {"dir": "ltr", "align": "left", "title": "EDUCHECK AI 🚀", "reg": "注册", "check": "分析", "rubric": "评分标准", "btn": "运行人工智能"}
}

st.set_page_config(page_title="EduCheck AI", layout="wide", page_icon="⚡")

# בחירת שפה
lang = st.sidebar.selectbox("🌐 System Language", list(LANG_CONFIG.keys()))
L = LANG_CONFIG[lang]

# --- עיצוב טכנולוגי (Dark Tech Mode) ---
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Assistant:wght@300;600&display=swap');
    
    .stApp {{
        background: radial-gradient(circle, #101820 0%, #0b0e14 100%);
        color: #e0e0e0;
        direction: {L['dir']};
        text-align: {L['align']};
        font-family: 'Assistant', sans-serif;
    }}
    
    .main-header {{
        font-family: 'Orbitron', sans-serif;
        color: #00d4ff;
        text-shadow: 0px 0px 15px #00d4ff;
        text-align: center;
        font-size: 3.5rem;
        padding: 20px;
        border-bottom: 1px solid #00d4ff33;
    }}
    
    [data-testid="stSidebar"] {{
        background-color: #0b0e14;
        border-{'right' if L['dir']=='ltr' else 'left'}: 1px solid #00d4ff33;
    }}
    
    .stButton > button {{
        background: linear-gradient(90deg, #00d4ff 0%, #0072ff 100%);
        color: white;
        border: none;
        border-radius: 50px;
        padding: 10px 25px;
        font-weight: bold;
        transition: 0.3s;
        box-shadow: 0px 4px 15px rgba(0, 212, 255, 0.3);
        width: 100%;
    }}
    
    .stButton > button:hover {{
        box-shadow: 0px 0px 25px #00d4ff;
        transform: scale(1.02);
    }}
    
    .stTextInput input, .stTextArea textarea {{
        background-color: #1a1f26 !important;
        color: #00d4ff !important;
        border: 1px solid #00d4ff33 !important;
        border-radius: 10px !important;
    }}
</style>
""", unsafe_allow_html=True)

st.markdown(f"<h1 class='main-header'>{L['title']}</h1>", unsafe_allow_html=True)

# יצירת בסיס נתונים
base_path = "tech_students_db"
if not os.path.exists(base_path): os.makedirs(base_path)

# תפריט ניווט
choice = st.sidebar.radio("NAVIGATE", [L['check'], L['reg']])

if choice == L['reg']:
    st.markdown(f"### 🧬 {L['reg']}")
    name = st.text_input("Student Identity:")
    files = st.file_uploader("Upload 3 Handwriting DNA Samples", type=['png', 'jpg', 'jpeg'], accept_multiple_files=True)
    
    if st.button("INITIALIZE STUDENT"):
        if name and len(files) >= 3:
            p = os.path.join(base_path, name)
            if not os.path.exists(p): os.makedirs(p)
            for i, f in enumerate(files[:3]):
                Image.open(f).save(os.path.join(p, f"sample_{i}.png"))
            st.success("STUDENT SYNCED TO DATABASE.")
        else:
            st.error("Error: Minimum 3 samples required.")

else:
    students = sorted(os.listdir(base_path))
    if not students:
        st.info("System Empty. Please register a student.")
    else:
        col1, col2 = st.columns([1, 1.5])
        with col1:
            target = st.selectbox("Select Target:", students)
            rubric = st.text_area(L['rubric'], height=200)
        
        with col2:
            exam = st.file_uploader("Scan Document", type=['png', 'jpg', 'jpeg', 'pdf'])
            cam = st.camera_input("Live Scanner")
            
        if st.button(L['btn']):
            source = cam if cam else exam
            if source and rubric:
                with st.spinner("AI Processing... Decoding Neural Ink Patterns"):
                    try:
                        s_dir = os.path.join(base_path, target)
                        samples = [Image.open(os.path.join(s_dir, f)) for f in os.listdir(s_dir)]
                        model = genai.GenerativeModel('gemini-1.5-flash')
                        
                        prompt = f"""
                        Handwriting Recognition Protocol:
                        1. Analyze the exam image.
                        2. Use ONLY the provided sample images of '{target}' to decode their specific handwriting style.
                        3. Compare identified text against this rubric: {rubric}.
                        4. Output results clearly in {lang}.
                        """
                        
                        response = model.generate_content([prompt] + samples + [Image.open(source)])
                        st.markdown("---")
                        st.markdown("### 📡 AI Analysis Result:")
                        st.info(response.text)
                    except Exception as e:
                        st.error(f"System Failure: {e}")
