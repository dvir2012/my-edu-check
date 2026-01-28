import streamlit as st
import google.generativeai as genai
from PIL import Image
import os

# הגדרות דף
st.set_page_config(page_title="EduCheck Pro - מאגר קבוע", layout="wide")

# יצירת תיקייה ראשית לאחסון תמונות התלמידים אם היא לא קיימת
if not os.path.exists("students_data"):
    os.makedirs("students_data")

# הגדרת ה-API של Gemini
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("חסר מפתח API ב-Secrets")

st.title("📝 EduCheck Pro - מאגר תלמידים קבוע")

# סרגל צדי - ניהול תלמידים
st.sidebar.header("👥 ניהול תלמידים")
action = st.sidebar.radio("בחר פעולה:", ["בחירת תלמיד קיים", "רישום תלמיד חדש"])

# רשימת התלמידים הקיימים (לפי התיקיות שנוצרו)
existing_students = os.listdir("students_data")

selected_student = None
sample_images = []

if action == "רישום תלמיד חדש":
    new_student_name = st.sidebar.text_input("שם התלמיד החדש:")
    st.sidebar.write("העלה 3 תמונות לימוד (א-ת, A-Z):")
    s1 = st.sidebar.file_uploader("תמונה 1:", type=['png', 'jpg', 'jpeg'], key="new_s1")
    s2 = st.sidebar.file_uploader("תמונה 2:", type=['png', 'jpg', 'jpeg'], key="new_s2")
    s3 = st.sidebar.file_uploader("תמונה 3:", type=['png', 'jpg', 'jpeg'], key="new_s3")
    
    if st.sidebar.button("שמור תלמיד במערכת"):
        if new_student_name and s1 and s2 and s3:
            # יצירת תיקייה לתלמיד
            path = os.path.join("students_data", new_student_name)
            if not os.path.exists(path):
                os.makedirs(path)
            
            # שמירת התמונות פיזית בשרת
            for i, s in enumerate([s1, s2, s3]):
                with open(os.path.join(path, f"sample_{i}.png"), "wb") as f:
                    f.write(s.getbuffer())
            
            st.sidebar.success(f"התלמיד {new_student_name} נשמר בהצלחה!")
            st.rerun()
        else:
            st.sidebar.error("חובה להזין שם ולהעלות את כל 3 התמונות.")

else:
    if existing_students:
        selected_student = st.sidebar.selectbox("בחר תלמיד:", existing_students)
        st.sidebar.info(f"טוען נתוני כתב יד עבור: {selected_student}")
        
        # טעינת התמונות השמורות של התלמיד שנבחר
        path = os.path.join("students_data", selected_student)
        for i in range(3):
            img_path = os.path.join(path, f"sample_{i}.png")
            if os.path.exists(img_path):
                sample_images.append(Image.open(img_path))
    else:
        st.sidebar.warning("אין תלמידים רשומים. בחר 'רישום תלמיד חדש'.")

# מסך ראשי - בדיקת המבחן
st.divider()
col1, col2 = st.columns(2)

with col1:
    st.header("📸 העלאת המבחן")
    exam_file = st.file_uploader("צילום המבחן (עברית/אנגלית):", type=['png', 'jpg', 'jpeg'])

with col2:
    st.header("🎯 המחוון")
    rubric = st.text_area("התשובה המצופה:", height=150)

if st.button("בדוק מבחן עבור התלמיד 🚀"):
    if selected_student and sample_images and exam_file and rubric:
        with st.spinner(f'מנתח לפי כתב היד של {selected_student}...'):
            try:
                model = genai.GenerativeModel('gemini-1.5-pro')
                img_exam = Image.open(exam_file)
                
                # יצירת רשימת הקבצים למודל: 3 תמונות לימוד + תמונת המבחן
                inputs = sample_images + [img_exam]
                
                prompt = f"""
                משימה: פענוח ובדיקת מבחן.
                התמונות הראשונות הן דוגמאות לכתב היד של התלמיד (עברית ואנגלית). למד אותן היטב.
                התמונה האחרונה היא המבחן.
                
                1. תמלל את מה שכתוב במבחן.
                2. השווה למחוון: {rubric}
                3. תן ציון והסבר בעברית.
                """
                
                response = model.generate_content([prompt] + inputs)
                st.success("הבדיקה הושלמה!")
                st.markdown("### תוצאות:")
                st.write(response.text)
            except Exception as e:
                st.error(f"שגיאה: {e}")
    else:
        st.warning("וודא שבחרת תלמיד קיים (עם תמונות שמורות), העלית מבחן והזנת מחוון.")
