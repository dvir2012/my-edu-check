import streamlit as st
import google.generativeai as genai
from PIL import Image
import os

# הגדרות דף
st.set_page_config(page_title="EduCheck Pro v2", layout="wide")

# יצירת תיקייה לאחסון תלמידים
if not os.path.exists("students_data"):
    os.makedirs("students_data")

# חיבור ל-API - שימוש במודל הפלאש העדכני למניעת שגיאת 404
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("Missing API Key in Secrets!")

# בחירת שפת ממשק
lang = st.sidebar.selectbox("בחר שפת ממשק / Language", ["עברית", "English"])

if lang == "עברית":
    t = {"title": "📝 EduCheck Pro", "manage": "👥 ניהול תלמידים", "action": "בחר פעולה:", "exist": "תלמיד קיים", "new": "רישום תלמיד חדש", "name": "שם התלמיד:", "upload": "העלה 3 תמונות לימוד:", "save": "שמור תלמיד", "select": "בחר תלמיד:", "exam": "📸 העלאת המבחן", "rubric": "🎯 מחוון תשובות", "check": "בדוק מבחן 🚀", "success": "הבדיקה הושלמה!", "error": "קרתה שגיאה:"}
else:
    t = {"title": "📝 EduCheck Pro", "manage": "👥 Management", "action": "Select Action:", "exist": "Existing Student", "new": "New Student", "name": "Student Name:", "upload": "Upload 3 samples:", "save": "Save Student", "select": "Select Student:", "exam": "📸 Upload Exam", "rubric": "🎯 Answer Key", "check": "Check Exam 🚀", "success": "Analysis Complete!", "error": "Error occurred:"}

st.title(t["title"])

# סרגל צדי לניהול המאגר
st.sidebar.header(t["manage"])
action = st.sidebar.radio(t["action"], [t["exist"], t["new"]])

existing_students = os.listdir("students_data")
selected_student = None
sample_images = []

if action == t["new"]:
    new_name = st.sidebar.text_input(t["name"])
    s1 = st.sidebar.file_uploader("Image 1 (א-ח / A-H)", type=['png', 'jpg', 'jpeg'], key="s1")
    s2 = st.sidebar.file_uploader("Image 2 (ט-ע / I-P)", type=['png', 'jpg', 'jpeg'], key="s2")
    s3 = st.sidebar.file_uploader("Image 3 (פ-ת / Q-Z)", type=['png', 'jpg', 'jpeg'], key="s3")
    
    if st.sidebar.button(t["save"]):
        if new_name and s1 and s2 and s3:
            path = os.path.join("students_data", new_name)
            if not os.path.exists(path): os.makedirs(path)
            for i, s in enumerate([s1, s2, s3]):
                with open(os.path.join(path, f"sample_{i}.png"), "wb") as f:
                    f.write(s.getbuffer())
            st.sidebar.success("Saved to Database!")
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
    rubric = st.text_area(t["rubric"], height=150)

if st.button(t["check"]):
    if selected_student and sample_images and exam_file and rubric:
        with st.spinner("מנתח לפי מאגר האותיות השמור..."):
            try:
                # שימוש במודל פלאש למניעת 404
                model = genai.GenerativeModel('gemini-1.5-flash-latest')
                img_exam = Image.open(exam_file)
                
                # יצירת הנחיה שמכריחה אותו להשתמש במאגר
                prompt = f"""
                משימה דחופה: פענוח כתב יד בהתאמה אישית.
                
                לפניך 3 תמונות שהן 'מאגר נתוני האותיות' של התלמיד {selected_student}. 
                עליך ללמוד כל אות וצורה מהמאגר הזה. אל תנחש לפי ידע כללי, אלא רק לפי הצורות במאגר.
                
                לאחר מכן, פענח את התמונה האחרונה (המבחן).
                מחוון לבדיקה: {rubric}
                
                ענה בעברית:
                1. תמלול מדויק של תשובת התלמיד.
                2. השוואה למחוון.
                3. ציון סופי.
                """
                
                # שליחת המאגר (3 תמונות) + המבחן
                response = model.generate_content([prompt] + sample_images + [img_exam])
                
                st.success(t["success"])
                st.markdown(f"### ניתוח עבור: {selected_student}")
                st.write(response.text)
            except Exception as e:
                st.error(f"{t['error']} {e}")
    else:
        st.warning("Missing Data: Ensure student is selected and exam is uploaded.")
