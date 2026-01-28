import streamlit as st
import google.generativeai as genai
from PIL import Image
import os

# --- 1. עיצוב האפליקציה (CSS) ---
st.set_page_config(page_title="EduCheck Pro", layout="wide")

st.markdown("""
    <style>
    .stApp {
        background-color: #f0f2f6;
    }
    .main-title {
        color: #2e4a7d;
        text-align: center;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    .stButton>button {
        background-color: #4CAF50;
        color: white;
        border-radius: 12px;
        padding: 10px 24px;
        border: none;
        width: 100%;
    }
    .stTextArea textarea {
        border-radius: 10px;
        border: 1px solid #2e4a7d;
    }
    .sidebar .sidebar-content {
        background-color: #ffffff;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. לוגיקה וחיבורים ---
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("Missing API Key!")
    st.stop()

st.markdown("<h1 class='main-title'>📝 EduCheck Pro</h1>", unsafe_allow_html=True)

# כניסת מורה
st.sidebar.title("🔐 כניסת מורה")
teacher_id = st.sidebar.text_input("הכנס קוד מורה:", type="password")

if not teacher_id:
    st.info("שלום! אנא הכנס קוד מורה בסרגל הצדי כדי להתחבר למאגר האישי שלך.")
    st.stop()

teacher_folder = f"data_{teacher_id}"
if not os.path.exists(teacher_folder):
    os.makedirs(teacher_folder)

# --- 3. הגדרת סגנון בדיקה אישי ---
st.sidebar.divider()
st.sidebar.subheader("⚙️ סגנון הבדיקה שלך")
grading_style = st.sidebar.text_area("איך תרצה שה-AI יבדוק? (למשל: 'היה סלחן על שגיאות כתיב', 'היה קשוח בניסוח מדעי'):", 
                                   placeholder="כתוב כאן הנחיות כלליות שיוחלו על כל המבחנים...")

# --- 4. ניהול תלמידים ---
st.sidebar.header("👥 ניהול תלמידים")
action = st.sidebar.radio("פעולה:", ["תלמיד קיים", "רישום חדש"])
existing_students = os.listdir(teacher_folder)
selected_student = None
sample_images = []

if action == "רישום חדש":
    new_name = st.sidebar.text_input("שם התלמיד:")
    s1 = st.sidebar.file_uploader("חלק 1", type=['png', 'jpg', 'jpeg'], key="s1")
    s2 = st.sidebar.file_uploader("חלק 2", type=['png', 'jpg', 'jpeg'], key="s2")
    s3 = st.sidebar.file_uploader("חלק 3", type=['png', 'jpg', 'jpeg'], key="s3")
    if st.sidebar.button("שמור תלמיד"):
        if new_name and s1 and s2 and s3:
            s_path = os.path.join(teacher_folder, new_name)
            if not os.path.exists(s_path): os.makedirs(s_path)
            for i, s in enumerate([s1, s2, s3]):
                with open(os.path.join(s_path, f"sample_{i}.png"), "wb") as f:
                    f.write(s.getbuffer())
            st.sidebar.success("נשמר!")
            st.rerun()
else:
    if existing_students:
        selected_student = st.sidebar.selectbox("בחר תלמיד:", existing_students)
        s_path = os.path.join(teacher_folder, selected_student)
        for i in range(3):
            img_p = os.path.join(s_path, f"sample_{i}.png")
            if os.path.exists(img_p):
                sample_images.append(Image.open(img_p))

# --- 5. אזור הבדיקה ---
col1, col2 = st.columns(2)
with col1:
    st.subheader("📸 העלאת המבחן")
    exam_file = st.file_uploader("", type=['png', 'jpg', 'jpeg'])
with col2:
    st.subheader("🎯 מחוון תשובות")
    rubric = st.text_area("מה התשובה הנכונה?", height=100)

if st.button("בדוק מבחן 🚀"):
    if selected_student and sample_images and exam_file and rubric:
        with st.spinner("מנתח לפי הסגנון האישי שלך..."):
            try:
                model = genai.GenerativeModel('gemini-1.5-flash')
                img_exam = Image.open(exam_file)
                
                # שילוב סגנון המורה בתוך הפרומפט
                prompt = f"""
                You are a teaching assistant working for a teacher with a specific grading style.
                
                TEACHER'S PERSONAL STYLE: {grading_style if grading_style else "Standard and professional."}
                
                STUDENT: {selected_student}
                TASK:
                1. Use the first 3 images to learn the student's handwriting.
                2. Grade the last image based on this rubric: {rubric}
                
                Answer in Hebrew. Be sure to follow the teacher's personal style in your feedback and grading.
                """
                
                response = model.generate_content([prompt] + sample_images + [img_exam])
                st.markdown("### 📝 תוצאות הבדיקה")
                st.success("הפענוח הושלם!")
                st.write(response.text)
            except Exception as e:
                st.error(f"Error: {e}")
    else:
        st.warning("וודא שמילאת את כל השדות.")
