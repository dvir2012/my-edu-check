import streamlit as st
import google.generativeai as genai
from PIL import Image
import os

# הגדרות דף
st.set_page_config(page_title="EduCheck Pro - MultiLang", layout="wide")

# יצירת תיקייה לאחסון אם לא קיימת
if not os.path.exists("students_data"):
    os.makedirs("students_data")

# הגדרת ה-API
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("Missing API Key in Secrets!")

# --- בחירת שפת ממשק (בצד ימין/למעלה) ---
lang = st.sidebar.selectbox("בחר שפת ממשק / Select Interface Language", ["עברית", "English"])

# מילון תרגומים לממשק
if lang == "עברית":
    t = {
        "title": "📝 EduCheck Pro - מאגר תלמידים",
        "manage": "👥 ניהול תלמידים",
        "action": "בחר פעולה:",
        "exist": "בחירת תלמיד קיים",
        "new": "רישום תלמיד חדש",
        "name_label": "שם התלמיד החדש:",
        "upload_samples": "העלה 3 תמונות לימוד (א-ת, A-Z):",
        "save_btn": "שמור תלמיד במערכת",
        "select_student": "בחר תלמיד:",
        "exam_header": "📸 העלאת המבחן",
        "rubric_header": "🎯 המחוון",
        "check_btn": "בדוק מבחן עבור התלמיד 🚀",
        "sample": "תמונה",
        "exam_label": "צילום המבחן:",
        "rubric_label": "התשובה המצופה:",
        "loading": "מנתח נתונים...",
        "success": "הבדיקה הושלמה!"
    }
else:
    t = {
        "title": "📝 EduCheck Pro - Student Database",
        "manage": "👥 Student Management",
        "action": "Select Action:",
        "exist": "Existing Student",
        "new": "Register New Student",
        "name_label": "New Student Name:",
        "upload_samples": "Upload 3 Sample Images (A-Z, Aleph-Tav):",
        "save_btn": "Save Student to Database",
        "select_student": "Select Student:",
        "exam_header": "📸 Upload Exam",
        "rubric_header": "🎯 Answer Key",
        "check_btn": "Check Student's Exam 🚀",
        "sample": "Image",
        "exam_label": "Upload Exam Photo:",
        "rubric_label": "Expected Answer:",
        "loading": "Analyzing...",
        "success": "Analysis Complete!"
    }

st.title(t["title"])

# סרגל צדי
st.sidebar.header(t["manage"])
action = st.sidebar.radio(t["action"], [t["exist"], t["new"]])

existing_students = os.listdir("students_data")
selected_student = None
sample_images = []

if action == t["new"]:
    new_student_name = st.sidebar.text_input(t["name_label"])
    st.sidebar.write(t["upload_samples"])
    s1 = st.sidebar.file_uploader(f"{t['sample']} 1:", type=['png', 'jpg', 'jpeg'], key="new_s1")
    s2 = st.sidebar.file_uploader(f"{t['sample']} 2:", type=['png', 'jpg', 'jpeg'], key="new_s2")
    s3 = st.sidebar.file_uploader(f"{t['sample']} 3:", type=['png', 'jpg', 'jpeg'], key="new_s3")
    
    if st.sidebar.button(t["save_btn"]):
        if new_student_name and s1 and s2 and s3:
            path = os.path.join("students_data", new_student_name)
            if not os.path.exists(path): os.makedirs(path)
            for i, s in enumerate([s1, s2, s3]):
                with open(os.path.join(path, f"sample_{i}.png"), "wb") as f:
                    f.write(s.getbuffer())
            st.sidebar.success(f"Saved {new_student_name}!")
            st.rerun()

else:
    if existing_students:
        selected_student = st.sidebar.selectbox(t["select_student"], existing_students)
        path = os.path.join("students_data", selected_student)
        for i in range(3):
            img_path = os.path.join(path, f"sample_{i}.png")
            if os.path.exists(img_path):
                sample_images.append(Image.open(img_path))
    else:
        st.sidebar.warning("No students in DB.")

# מסך ראשי
st.divider()
col1, col2 = st.columns(2)

with col1:
    st.header(t["exam_header"])
    exam_file = st.file_uploader(t["exam_label"], type=['png', 'jpg', 'jpeg'])

with col2:
    st.header(t["rubric_header"])
    rubric = st.text_area(t["rubric_label"], height=150)

if st.button(t["check_btn"]):
    if selected_student and sample_images and exam_file and rubric:
        with st.spinner(t["loading"]):
            try:
                model = genai.GenerativeModel('gemini-1.5-pro')
                img_exam = Image.open(exam_file)
                inputs = sample_images + [img_exam]
