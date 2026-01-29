import streamlit as st
import google.generativeai as genai
from PIL import Image
import os

# --- 1. הגדרות תצורה ושפה ---
st.set_page_config(page_title="EduCheck Sunset", layout="wide", page_icon="🌅")

LANG_DICT = {
    "עברית": {
        "dir": "rtl", "align": "right", "welcome": "ברוכים הבאים ל-EduCheck",
        "enter_code": "אנא הזן קוד גישה כדי להתחיל:", "login_btn": "כניסה למערכת 🔑",
        "title": "EduCheck Sunset 🌅", "teacher_zone": "🔑 מרחב המורה",
        "id_label": "קוד גישה:", "student_reg": "📝 רישום תלמיד חדש",
        "student_name_label": "שם התלמיד:", "save_btn": "שמור מאגר",
        "select_student": "👤 בחר תלמיד:", "exam_type": "📝 סוג המבחן:", 
        "types": ["מבחן פתוח", "מבחן אמריקאי", "השלמת משפטים", "נכון/לא נכון", "חישובים ומתמטיקה"],
        "exam_upload": "📸 העלאת המבחן", "rubric_label": "🎯 מחוון תשובות",
        "btn_check": "התחל בדיקת מומחה 🚀", "scan_msg": "מנתח נתונים באווירת בין הערביים...",
        "error_api": "מפתח API חסר!", "success_reg": "✅ התלמיד נרשם בהצלחה!"
    },
    "English": {
        "dir": "ltr", "align": "left", "welcome": "Welcome to EduCheck",
        "enter_code": "Please enter access code to start:", "login_btn": "Login 🔑",
        "title": "EduCheck Sunset 🌅", "teacher_zone": "🔑 Teacher Zone",
        "id_label": "Access Code:", "student_reg": "📝 Student Registry",
        "student_name_label": "Student Name:", "save_btn": "Save Database",
        "select_student": "👤 Select Student:", "exam_type": "📝 Exam Type:", 
        "types": ["Open Questions", "Multiple Choice", "Fill in Blanks", "True/False", "Math"],
        "exam_upload": "📸 Upload Exam", "rubric_label": "🎯 Rubric",
        "btn_check": "Start Expert Check 🚀", "scan_msg": "Analyzing data...",
        "error_api": "API Key Missing!", "success_reg": "✅ Student registered!"
    },
    "العربية": {
        "dir": "rtl", "align": "right", "welcome": "مرحباً بكم في إيدوشيك",
        "enter_code": "يرجى إدخال رمز الدخول للبدء:", "login_btn": "دخول 🔑",
        "title": "إيدوشيك الغروب 🌅", "teacher_zone": "🔑 منطقة المعلم",
        "id_label": "رمز الدخول:", "student_reg": "📝 تسجيل طالب جديد",
        "student_name_label": "اسم الطالب:", "save_btn": "حفظ القاعدة",
        "select_student": "👤 اختر الطالب:", "exam_type": "📝 نوع الامتحان:", 
        "types": ["امتحان مفتوح", "امتحان أمريكي", "إكمال الجمل", "صح/خطأ", "رياضيات"],
        "exam_upload": "📸 تحميل الامتحان", "rubric_label": "🎯 نموذج الإجابة",
        "btn_check": "ابدأ التصحيح 🚀", "scan_msg": "جاري التحليل...",
        "error_api": "رمز API مفقود!", "success_reg": "✅ تم تسجيل الطالب بنجاح!"
    }
}

# --- 2. ניהול מצב כניסה (Session State) ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "teacher_id" not in st.session_state:
    st.session_state.teacher_id = ""

# --- 3. עיצוב Sunset Edition ---
def apply_style(dir, align):
    st.markdown(f"""
    <style>
        .stApp {{
            background: linear-gradient(135deg, #1a2a6c, #b21f1f, #fdbb2d);
            color: white; direction: {dir}; text-align: {align};
        }}
        .main-header {{
            background: linear-gradient(90deg, #FFD194, #D1913C);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
            font-size: 3.5rem; font-weight: 900; text-align: center; padding: 20px;
        }}
        div.stButton > button {{
            background: linear-gradient(45deg, #FD746C, #FF9068);
            border-radius: 12px; color: white; border: none; height: 3.5em; font-weight: bold; width: 100%;
        }}
        .stTextArea textarea, .stTextInput input {{
            background-color: rgba(255, 255, 255, 0.1) !important; color: white !important;
            border: 1px solid #FD746C !important;
        }}
        [data-testid="stSidebar"] {{ background-color: rgba(0, 0, 0, 0.5); }}
    </style>
    """, unsafe_allow_html=True)

# --- 4. מסך כניסה (Login Screen) ---
if not st.session_state.logged_in:
    apply_style("rtl", "center")
    st.markdown("<h1 class='main-header'>EduCheck Sunset 🌅</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("### Welcome | ברוכים הבאים | مرحباً")
        input_id = st.text_input("Access Code / קוד גישה / رمز الدخول", type="password")
        if st.button("Enter 🚀"):
            if input_id:
                st.session_state.logged_in = True
                st.session_state.teacher_id = input_id
                st.rerun()
            else:
                st.warning("Please enter a code")
    st.stop()

# --- 5. האפליקציה הראשית (אחרי כניסה) ---
selected_lang = st.sidebar.selectbox("🌐 Language", ["עברית", "English", "العربية"])
L = LANG_DICT[selected_lang]
apply_style(L["dir"], L["align"])

# חיבור ל-API
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error(L["error_api"])
    st.stop()

st.markdown(f"<h1 class='main-header'>{L['title']}</h1>", unsafe_allow_html=True)

# ניהול נתונים בסיידבר
base_path = f"data_{st.session_state.teacher_id}"
if not os.path.exists(base_path): os.makedirs(base_path)

with st.sidebar.expander(L["student_reg"]):
    reg_name = st.text_input(L["student_name_label"], key="reg_name")
    s1 = st.file_uploader("1", type=['png', 'jpg', 'jpeg'], key="s1")
    s2 = st.file_uploader("2", type=['png', 'jpg', 'jpeg'], key="s2")
    s3 = st.file_uploader("3", type=['png', 'jpg', 'jpeg'], key="s3")
    if st.button(L["save_btn"]):
        if reg_name and s1 and s2 and s3:
            path = os.path.join(base_path, reg_name)
            if not os.path.exists(path): os.makedirs(path)
            for i, s in enumerate([s1, s2, s3]):
                Image.open(s).save(os.path.join(path, f"{i}.png"))
            st.success(L["success_reg"])
            st.rerun()

# ממשק בדיקה
st.divider()
students = sorted(os.listdir(base_path))
c1, c2, c3 = st.columns(3)

with c1:
    st.subheader(L["select_student"])
    student_name = st.selectbox("", [""] + students, label_visibility="collapsed")
    st.write(L["exam_type"])
    e_type = st.radio("", L["types"], label_visibility="collapsed")

with c2:
    st.subheader(L["exam_upload"])
    exam_file = st.file_uploader("", type=['png', 'jpg', 'jpeg'], key="exam_up")

with c3:
    st.subheader(L["rubric_label"])
    rubric = st.text_area("", placeholder="מחוון...", height=150)

if st.button(L["btn_check"]):
    if student_name and exam_file and rubric:
        with st.status(L["scan_msg"]):
            try:
                student_dir = os.path.join(base_path, student_name)
                samples = [Image.open(os.path.join(student_dir, f)) for f in os.listdir(student_dir)]
                model = genai.GenerativeModel('gemini-1.5-flash')
                exam_img = Image.open(exam_file)
                prompt = f"Grade {e_type} for {student_name}. Rubric: {rubric}. calibrate OCR with 3 samples. Respond in {selected_lang}."
                response = model.generate_content([prompt] + samples + [exam_img])
                st.balloons()
                st.markdown(f"### 📋 תוצאות עבור {student_name}")
                st.write(response.text)
            except Exception as e:
                st.error(f"Error: {e}")
