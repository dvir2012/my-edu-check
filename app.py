import streamlit as st
import google.generativeai as genai
from PIL import Image
import os

# --- הגדרת המפתח האישי שלך ---
MY_API_KEY = "AIzaSyDJdiYe4VmudGKFQzoCI_MmngD26D4wm1Q" 
genai.configure(api_key=MY_API_KEY)

# --- ניהול מצב (Session State) ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "teacher_id" not in st.session_state:
    st.session_state.teacher_id = None

# --- מילון שפות מורחב (עברית, אנגלית, ערבית, צרפתית, ספרדית, סינית) ---
LANG_CONFIG = {
    "עברית": {"dir": "rtl", "align": "right", "title": "EDUCHECK AI 🚀", "login_msg": "הזן קוד מורה:", "login_btn": "התחבר", "reg_header": "🧬 רישום תלמיד חדש", "name_label": "שם תלמיד:", "sample_label": "דגימת אותיות", "save_btn": "שמור תלמיד", "check_header": "🔍 בדיקת מבחן חכמה", "select_student": "בחר תלמיד:", "rubric_label": "מחוון תשובות:", "upload_label": "העלאת מבחן:", "run_btn": "הפעל ניתוח ⚡", "no_student": "נא לרשום תלמיד בסרגל הצד כדי להתחיל."},
    "English": {"dir": "ltr", "align": "left", "title": "EDUCHECK AI 🚀", "login_msg": "Teacher Code:", "login_btn": "Login", "reg_header": "🧬 Student Registration", "name_label": "Student Name:", "sample_label": "Handwriting Sample", "save_btn": "Save Student", "check_header": "🔍 AI Analysis", "select_student": "Select Student:", "rubric_label": "Rubric:", "upload_label": "Upload Exam:", "run_btn": "Run AI ⚡", "no_student": "Please register a student in the sidebar to begin."},
    "العربية": {"dir": "rtl", "align": "right", "title": "EDUCHECK AI 🚀", "login_msg": "أدخل رمز المعلم:", "login_btn": "دخول", "reg_header": "🧬 تسجيل طالب جديد", "name_label": "اسم الطالب:", "sample_label": "عينة الخط", "save_btn": "حفظ الطالب", "check_header": "🔍 تحليل الامتحان", "select_student": "اختر طالب:", "rubric_label": "نموذج الإجابة:", "upload_label": "تحميل الامتحان:", "run_btn": "تشغيل ⚡", "no_student": "يرجى تسجيل طالب في الشريط الجانبي للبدء."},
    "Français": {"dir": "ltr", "align": "left", "title": "EDUCHECK AI 🚀", "login_msg": "Code Enseignant:", "login_btn": "Connexion", "reg_header": "🧬 Inscription Étudiant", "name_label": "Nom:", "sample_label": "Échantillon d'écriture", "save_btn": "Enregistrer", "check_header": "🔍 Analyse IA", "select_student": "Choisir Étudiant:", "rubric_label": "Corrigé:", "upload_label": "Charger Examen:", "run_btn": "Lancer ⚡", "no_student": "Veuillez inscrire un étudiant pour commencer."},
    "Español": {"dir": "ltr", "align": "left", "title": "EDUCHECK AI 🚀", "login_msg": "Código:", "login_btn": "Entrar", "reg_header": "🧬 Registro de Estudiante", "name_label": "Nombre:", "sample_label": "Muestra de letra", "save_btn": "Guardar", "check_header": "🔍 Análisis de IA", "select_student": "Elegir Estudiante:", "rubric_label": "Clave:", "upload_label": "Subir Examen:", "run_btn": "Analizar ⚡", "no_student": "Registre un estudiante para comenzar."},
    "中文": {"dir": "ltr", "align": "left", "title": "EDUCHECK AI 🚀", "login_msg": "教师代码:", "login_btn": "登录", "reg_header": "🧬 学生注册", "name_label": "姓名:", "sample_label": "手写样本", "save_btn": "保存学生", "check_header": "🔍 智能分析", "select_student": "选择学生:", "rubric_label": "评分标准:", "upload_label": "上传试卷:", "run_btn": "开始分析 ⚡", "no_student": "请先在侧边栏注册学生。"}
}

st.set_page_config(page_title="EduCheck AI", layout="wide", page_icon="⚡")

# בחירת שפה בסיידבר
lang_choice = st.sidebar.selectbox("🌐 Language / שפה", list(LANG_CONFIG.keys()))
L = LANG_CONFIG[lang_choice]

# --- עיצוב טכנולוגי (Dark Mode UI) ---
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Assistant:wght@300;600&display=swap');
    .stApp {{ background: #0b0e14; color: #e0e0e0; direction: {L['dir']}; text-align: {L['align']}; font-family: 'Assistant', sans-serif; }}
    .main-header {{ font-family: 'Orbitron', sans-serif; color: #00d4ff; text-shadow: 0px 0px 10px #00d4ff; text-align: center; font-size: 2.5rem; padding: 20px; border-bottom: 1px solid #00d4ff33; }}
    [data-testid="stSidebar"] {{ background-color: #010409; border-{'right' if L['dir']=='ltr' else 'left'}: 1px solid #00d4ff33; direction: {L['dir']}; }}
    .stButton > button {{ background: linear-gradient(90deg, #00d4ff 0%, #0072ff 100%); color: white; border-radius: 8px; font-weight: bold; width: 100%; border: none; }}
</style>
""", unsafe_allow_html=True)

# --- 1. מסך כניסה ---
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

# --- 2. הגדרת בסיס נתונים ---
base_path = f"data_{st.session_state.teacher_id}"
if not os.path.exists(base_path): os.makedirs(base_path)

# --- 3. סרגל צד: רישום תלמיד ---
with st.sidebar:
    st.markdown(f"## {L['reg_header']}")
    new_student = st.text_input(L['name_label'])
    s1 = st.file_uploader(f"{L['sample_label']} 1", type=['png', 'jpg', 'jpeg'], key="s1")
    s2 = st.file_uploader(f"{L['sample_label']} 2", type=['png', 'jpg', 'jpeg'], key="s2")
    s3 = st.file_uploader(f"{L['sample_label']} 3", type=['png', 'jpg', 'jpeg'], key="s3")
    
    if st.button(L['save_btn']):
        if new_student and s1 and s2 and s3:
            path = os.path.join(base_path, new_student)
            if not os.path.exists(path): os.makedirs(path)
            for i, f in enumerate([s1, s2, s3]):
                Image.open(f).save(os.path.join(path, f"sample_{i}.png"))
            st.success("SYNCED ✅")
            st.rerun()
    
    st.markdown("---")
    if st.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()

# --- 4. מסך ראשי: בדיקת מבחן (מותנה בקיום תלמידים) ---
st.markdown(f"<h1 class='main-header'>{L['title']}</h1>", unsafe_allow_html=True)
students = sorted(os.listdir(base_path))

if not students:
    st.warning(f"⚠️ {L['no_student']}")
else:
    st.markdown(f"### {L['check_header']}")
    c1, c2 = st.columns([1, 1.5])
    
    with c1:
        selected = st.selectbox(L['select_student'], students)
        rubric = st.text_area(L['rubric_label'], height=200)
    
    with c2:
        st.write(L['upload_label'])
        exam_file = st.file_uploader("", type=['png', 'jpg', 'jpeg'])
        exam_cam = st.camera_input("")

    if st.button(L['run_btn']):
        source = exam_cam if exam_cam else exam_file
        if source and rubric:
            with st.spinner("Analyzing handwriting..."):
                try:
                    s_dir = os.path.join(base_path, selected)
                    samples = [Image.open(os.path.join(s_dir, f)) for f in os.listdir(s_dir)]
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    prompt = f"Use ONLY the handwriting samples of '{selected}' to identify their style. Grade the exam using this rubric: {rubric}. Respond in {lang_choice}."
                    response = model.generate_content([prompt] + samples + [Image.open(source)])
                    st.success("DONE ✅")
                    st.write(response.text)
                except Exception as e:
                    st.error(f"Error: {e}")
