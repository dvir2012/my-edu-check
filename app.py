import streamlit as st
import google.generativeai as genai
from PIL import Image
import os

# 1. הגדרות דף בסיסיות
st.set_page_config(page_title="EduCheck Pro", layout="wide")

# 2. חיבור ל-API של גוגל
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("Missing GOOGLE_API_KEY in Secrets!")
    st.stop()

# 3. מערכת כניסה למורים (הפרדת מאגרים)
st.sidebar.title("🔐 כניסת מורה")
teacher_id = st.sidebar.text_input("הכנס קוד מורה (למשל מספר טלפון):", type="password")

if not teacher_id:
    st.title("ברוכים הבאים ל-EduCheck Pro")
    st.info("אנא הכנס קוד מורה בסרגל הצדי כדי להתחיל.")
    st.stop()

# יצירת תיקייה אישית למורה
teacher_folder = f"data_{teacher_id}"
if not os.path.exists(teacher_folder):
    os.makedirs(teacher_folder)

# 4. הגדרת שפה ומילון ממשק
lang = st.sidebar.selectbox("שפה / Language", ["עברית", "English"])
if lang == "עברית":
    t = {
        "main_title": "📝 EduCheck - בודק מבחנים חכם",
        "sidebar_head": "👥 ניהול תלמידים",
        "new_stud": "רישום תלמיד חדש",
        "old_stud": "בחירת תלמיד קיים",
        "btn_save": "שמור תלמיד במאגר",
        "btn_check": "בדוק מבחן 🚀",
        "loading": "לומד את הכתב ומנתח...",
        "success": "הפענוח הושלם!"
    }
else:
    t = {
        "main_title": "📝 EduCheck Pro - Smart Grader",
        "sidebar_head": "👥 Students Management",
        "new_stud": "New Student",
        "old_stud": "Existing Student",
        "btn_save": "Save Student",
        "btn_check": "Analyze Exam 🚀",
        "loading": "Learning and Analyzing...",
        "success": "Analysis Done!"
    }

st.title(t["main_title"])

# 5. ניהול מאגר התלמידים (בתוך התיקייה של המורה)
st.sidebar.divider()
st.sidebar.header(t["sidebar_head"])
action = st.sidebar.radio("פעולה:", [t["old_stud"], t["new_stud"]])

existing_students = os.listdir(teacher_folder)
selected_student = None
sample_images = []

if action == t["new_stud"]:
    new_name = st.sidebar.text_input("שם התלמיד:")
    s1 = st.sidebar.file_uploader("דגימת כתב 1 (א-ח)", type=['png', 'jpg', 'jpeg'], key="s1")
    s2 = st.sidebar.file_uploader("דגימת כתב 2 (ט-ע)", type=['png', 'jpg', 'jpeg'], key="s2")
    s3 = st.sidebar.file_uploader("דגימת כתב 3 (פ-ת)", type=['png', 'jpg', 'jpeg'], key="s3")
    
    if st.sidebar.button(t["btn_save"]):
        if new_name and s1 and s2 and s3:
            s_path = os.path.join(teacher_folder, new_name)
            if not os.path.exists(s_path): os.makedirs(s_path)
            for i, s in enumerate([s1, s2, s3]):
                with open(os.path.join(s_path, f"sample_{i}.png"), "wb") as f:
                    f.write(s.getbuffer())
            st.sidebar.success(f"התלמיד {new_name} נשמר!")
            st.rerun()
else:
    if existing_students:
        selected_student = st.sidebar.selectbox("בחר תלמיד:", existing_students)
        s_path = os.path.join(teacher_folder, selected_student)
        for i in range(3):
            img_p = os.path.join(s_path, f"sample_{i}.png")
            if os.path.exists(img_p):
                sample_images.append(Image.open(img_p))
    else:
        st.sidebar.warning("אין תלמידים רשומים במאגר שלך.")

# 6. אזור בדיקת המבחן
st.divider()
col1, col2 = st.columns(2)
with col1:
    exam_file = st.file_uploader("העלה צילום מבחן (פתוח או אמריקאי):", type=['png', 'jpg', 'jpeg'])
with col2:
    rubric = st.text_area("מחוון תשובות (מה התשובה הנכונה):", height=150)

if st.button(t["btn_check"]):
    if selected_student and sample_images and exam_file and rubric:
        with st.spinner(t["loading"]):
            try:
                # שימוש במודל המאוזן ביותר
                model = genai.GenerativeModel('gemini-1.5-flash')
                img_exam = Image.open(exam_file)
                
                # בניית הפרומפט המסונכרן
                prompt = f"""
                You are a teaching assistant checking an exam for the student: {selected_student}.
                
                1. Look at the first 3 images. They are the 'Handwriting Key' for this specific student.
                2. Analyze the last image (the exam).
                3. If it's a written answer, use the 'Key' to read it.
                4. If it's a multiple-choice exam, identify which answer is circled or marked.
                
                Compare the student's answer to this rubric: {rubric}
                
                Answer in Hebrew:
                - What did the student write/mark?
                - Is it correct?
                - Final score.
                """
                
                response = model.generate_content([prompt] + sample_images + [img_exam])
                st.success(t["success"])
                st.write(response.text)
            except Exception as e:
                st.error(f"Error: {e}")
    else:
        st.warning("נא לוודא: 1. בחרת תלמיד 2. העלית מבחן 3. כתבת מחוון.")
