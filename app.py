import streamlit as st
import google.generativeai as genai
from PIL import Image
import os

st.set_page_config(page_title="EduCheck Pro - Synced AI", layout="wide")

if not os.path.exists("students_data"):
    os.makedirs("students_data")

if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("Missing API Key!")

# בחירת שפה
lang = st.sidebar.selectbox("Language", ["עברית", "English"])
t_check = "בדוק מבחן 🚀" if lang == "עברית" else "Analyze Exam 🚀"

st.title("📝 EduCheck Pro")

# ניהול מאגר תלמידים
st.sidebar.header("מאגר תלמידים")
action = st.sidebar.radio("פעולה:", ["תלמיד קיים", "רישום חדש"])

existing_students = os.listdir("students_data")
selected_student = None
sample_files = []

if action == "רישום חדש":
    new_name = st.sidebar.text_input("שם התלמיד:")
    s1 = st.sidebar.file_uploader("חלק 1 (א-ח / A-H)", type=['png', 'jpg', 'jpeg'], key="s1")
    s2 = st.sidebar.file_uploader("חלק 2 (ט-ע / I-P)", type=['png', 'jpg', 'jpeg'], key="s2")
    s3 = st.sidebar.file_uploader("חלק 3 (פ-ת / Q-Z)", type=['png', 'jpg', 'jpeg'], key="s3")
    
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
                sample_files.append(Image.open(img_path))

st.divider()
col1, col2 = st.columns(2)
with col1:
    exam_file = st.file_uploader("העלה את המבחן:", type=['png', 'jpg', 'jpeg'])
with col2:
    rubric = st.text_area("מחוון (התשובה הנכונה):", height=150)

if st.button(t_check):
    if selected_student and sample_files and exam_file and rubric:
        with st.spinner("מסנכרן בין מאגר האותיות למבחן..."):
            try:
                # שימוש במודל יציב ומהיר
                model = genai.GenerativeModel('gemini-1.5-flash')
                img_exam = Image.open(exam_file)
                
                # יצירת תוכן מסונכרן - כל תמונה מקבלת תיאור תפקיד
                content = [
                    "INSTRUCTION: You are a synced handwriting analyzer.",
                    "REFERENCE IMAGE 1 (Letters א-ח / A-H):", sample_files[0],
                    "REFERENCE IMAGE 2 (Letters ט-ע / I-P):", sample_files[1],
                    "REFERENCE IMAGE 3 (Letters פ-ת / Q-Z):", sample_files[2],
                    "TASK: Use the references above to decode this exam image:", img_exam,
                    f"CONTEXT: After decoding, compare to this rubric: {rubric}. Answer in Hebrew."
                ]
                
                response = model.generate_content(content)
                st.success("הפענוח הושלם!")
                st.write(response.text)
                
            except Exception as e:
                st.error(f"שגיאה: {e}")
    else:
        st.warning("חסרים נתונים לבדיקה.")
