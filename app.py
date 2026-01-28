import streamlit as st
import google.generativeai as genai
from PIL import Image
import os

st.set_page_config(page_title="EduCheck Pro - OCR & Quiz", layout="wide")

if not os.path.exists("students_data"):
    os.makedirs("students_data")

if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("Missing API Key!")

# בחירת שפה
lang = st.sidebar.selectbox("Language", ["עברית", "English"])
t_check = "בדוק מבחן (פתוח/אמריקאי) 🚀" if lang == "עברית" else "Analyze Exam 🚀"

st.title("📝 EduCheck Pro - בודק מבחנים חכם")

# ניהול מאגר תלמידים
st.sidebar.header("מאגר תלמידים")
action = st.sidebar.radio("פעולה:", ["תלמיד קיים", "רישום חדש"])

existing_students = os.listdir("students_data")
selected_student = None
sample_files = []

if action == "רישום חדש":
    new_name = st.sidebar.text_input("שם התלמיד:")
    s1 = st.sidebar.file_uploader("חלק 1 (א-ח)", type=['png', 'jpg', 'jpeg'], key="s1")
    s2 = st.sidebar.file_uploader("חלק 2 (ט-ע)", type=['png', 'jpg', 'jpeg'], key="s2")
    s3 = st.sidebar.file_uploader("חלק 3 (פ-ת)", type=['png', 'jpg', 'jpeg'], key="s3")
    
    if st.sidebar.button("שמור"):
        if new_name and s1 and s2 and s3:
            path = os.path.join("students_data", new_name)
            if not os.path.exists(path): os.makedirs(path)
            for i, s in enumerate([s1, s2, s3]):
                with open(os.path.join(path, f"sample_{i}.png"), "wb") as f:
                    f.write(s.getbuffer())
            st.sidebar.success("נשמר!")
            st.rerun()
else:
    if existing_students:
        selected_student = st.sidebar.selectbox("בחר תלמיד:", existing_students)
        path = os.path.join("students_data", selected_student)
        for i in range(3):
            img_path = os.path.join(path, f"sample_{i}.png")
            if os.path.exists(img_path):
                sample_images = Image.open(img_path)
                sample_files.append(sample_images)

st.divider()
col1, col2 = st.columns(2)
with col1:
    exam_file = st.file_uploader("העלה את המבחן (כתב יד או אמריקאי):", type=['png', 'jpg', 'jpeg'])
with col2:
    rubric = st.text_area("מחוון (למבחן אמריקאי: רשום 1.א, 2.ג וכו'):", height=150)

if st.button(t_check):
    if selected_student and sample_files and exam_file and rubric:
        with st.spinner("מנתח מבחן ומסנכרן אותיות..."):
            try:
                # ניסיון להשתמש בשם מודל הכי נפוץ
                model = genai.GenerativeModel('gemini-1.5-flash')
                img_exam = Image.open(exam_file)
                
                prompt = f"""
                You are an expert teacher's assistant.
                
                STEP 1: Learn this student's ({selected_student}) handwriting from the first 3 reference images.
                STEP 2: Analyze the last image (the exam). 
                - If it's a written answer: use the reference to decode the handwriting.
                - If it's a Multiple Choice (American) exam: detect which option is circled or marked with X.
                
                RUBRIC: {rubric}
                
                OUTPUT IN HEBREW:
                1. Transcription of what the student wrote or marked.
                2. Check accuracy against the rubric.
                3. Final Grade.
                """
                
                response = model.generate_content([prompt] + sample_files + [img_exam])
                st.success("הבדיקה הושלמה!")
                st.markdown("### תוצאות:")
                st.write(response.text)
                
            except Exception as e:
                st.error(f"שגיאה: {e}. וודא שמפתח ה-API תקין.")
    else:
        st.warning("אנא וודא שבחרת תלמיד, העלית את המבחן והזנת מחוון.")
