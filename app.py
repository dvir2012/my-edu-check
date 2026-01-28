import streamlit as st
import google.generativeai as genai
from PIL import Image
import os

# הגדרות דף
st.set_page_config(page_title="EduCheck Pro", layout="wide")

# יצירת תיקייה לאחסון תלמידים
if not os.path.exists("students_data"):
    os.makedirs("students_data")

# חיבור ל-API
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("Missing API Key in Secrets!")

# בחירת שפת ממשק
lang = st.sidebar.selectbox("בחר שפת ממשק / Language", ["עברית", "English"])

if lang == "עברית":
    t = {
        "title": "📝 EduCheck Pro - מאגר תלמידים",
        "manage": "👥 ניהול תלמידים",
        "action": "בחר פעולה:",
        "exist": "תלמיד קיים",
        "new": "רישום תלמיד חדש",
        "name": "שם התלמיד:",
        "upload": "העלה 3 תמונות לימוד:",
        "save": "שמור תלמיד",
        "select": "בחר תלמיד:",
        "exam": "📸 העלאת המבחן",
        "rubric": "🎯 מחוון תשובות",
        "check": "בדוק מבחן 🚀",
        "success": "הבדיקה הושלמה!",
        "error": "קרתה שגיאה:"
    }
else:
    t = {
        "title": "📝 EduCheck Pro - Database",
        "manage": "👥 Management",
        "action": "Select Action:",
        "exist": "Existing Student",
        "new": "New Student",
        "name": "Student Name:",
        "upload": "Upload 3 samples:",
        "save": "Save Student",
        "select": "Select Student:",
        "exam": "📸 Upload Exam",
        "rubric": "🎯 Answer Key",
        "check": "Check Exam 🚀",
        "success": "Analysis Complete!",
        "error": "Error occurred:"
    }

st.title(t["title"])

# סרגל צדי
st.sidebar.header(t["manage"])
action = st.sidebar.radio(t["action"], [t["exist"], t["new"]])

existing_students = os.listdir("students_data")
selected_student = None
sample_images = []

if action == t["new"]:
    new_name = st.sidebar.text_input(t["name"])
    s1 = st.sidebar.file_uploader("Image 1", type=['png', 'jpg', 'jpeg'], key="s1")
    s2 = st.sidebar.file_uploader("Image 2", type=['png', 'jpg', 'jpeg'], key="s2")
    s3 = st.sidebar.file_uploader("Image 3", type=['png', 'jpg', 'jpeg'], key="s3")
    
    if st.sidebar.button(t["save"]):
        if new_name and s1 and s2 and s3:
            path = os.path.join("students_data", new_name)
            if not os.path.exists(path): os.makedirs(path)
            for i, s in enumerate([s1, s2, s3]):
                with open(os.path.join(path, f"sample_{i}.png"), "wb") as f:
                    f.write(s.getbuffer())
            st.sidebar.success("Saved!")
            st.rerun()

else:
    if existing_students:
        selected_student = st.sidebar.selectbox(t["select"], existing_students)
        path = os.path.join("students_data", selected_student)
        for i in range(3):
            img_path = os.path.join(path, f"sample_{i}.png")
            if os.path.exists(img_path):
                sample_images.append(Image.open(img_path))
    else:
        st.sidebar.warning("No students found.")

st.divider()
c1, c2 = st.columns(2)
with c1:
    st.header(t["exam"])
    exam_file = st.file_uploader("", type=['png', 'jpg', 'jpeg'])
with c2:
    st.header(t["rubric"])
    rubric = st.text_area("", height=150)

if st.button(t["check"]):
    if selected_student and sample_images and exam_file and rubric:
        with st.spinner("Processing..."):
            try:
                model = genai.GenerativeModel('gemini-1.5-pro')
                img_exam = Image.open(exam_file)
                
                # התיקון כאן: הוספת כל התמונות וההוראות יחד
                prompt = f"Learn handwriting from the first 3 images. Decode the last image. Rubric: {rubric}. Answer in Hebrew."
                response = model.generate_content([prompt] + sample_images + [img_exam])
                
                st.success(t["success"])
                st.write(response.text)
            except Exception as e:
                st.error(f"{t['error']} {e}")
    else:
        st.warning("Missing data (Student/Exam/Rubric)")
