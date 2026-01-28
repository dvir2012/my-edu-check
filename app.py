import streamlit as st
import google.generativeai as genai
from PIL import Image

st.set_page_config(page_title="EduCheck Pro - מאגר תלמידים", layout="wide")

# אתחול מאגר התלמידים בזיכרון (Session State)
if 'students_db' not in st.session_state:
    st.session_state['students_db'] = {}

# הגדרת ה-API
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("יש להגדיר API Key ב-Secrets")

st.title("📝 EduCheck Pro - ניהול תלמידים חכם")

# סרגל צדי - ניהול תלמידים
st.sidebar.header("👥 ניהול מאגר תלמידים")

# בחירה בין "תלמיד קיים" ל"הוספת תלמיד חדש"
mode = st.sidebar.radio("בחר פעולה:", ["בחר תלמיד קיים", "הוסף תלמיד חדש למערכת"])

alphabet = ['א', 'ב', 'ג', 'ד', 'ה', 'ו', 'ז', 'ח', 'ט', 'י', 'כ', 'ל', 'מ', 'נ', 'ס', 'ע', 'פ', 'צ', 'ק', 'ר', 'ש', 'ת']

if mode == "הוסף תלמיד חדש למערכת":
    new_student_name = st.sidebar.text_input("שם התלמיד החדש:")
    st.sidebar.write("העלה דוגמאות כתב יד:")
    
    current_letter_images = {}
    for letter in alphabet:
        with st.sidebar.expander(f"אות {letter}"):
            img = st.file_uploader(f"העלה {letter}", type=['png', 'jpg', 'jpeg'], key=f"new_{letter}")
            if img:
                current_letter_images[letter] = Image.open(img)
    
    if st.sidebar.button("שמור תלמיד במאגר"):
        if new_student_name and current_letter_images:
            st.session_state['students_db'][new_student_name] = current_letter_images
            st.sidebar.success(f"התלמיד {new_student_name} נשמר!")
        else:
            st.sidebar.error("יש להזין שם ולהעלות לפחות אות אחת.")

else:
    all_students = list(st.session_state['students_db'].keys())
    if all_students:
        selected_student = st.sidebar.selectbox("בחר תלמיד מהרשימה:", all_students)
        st.sidebar.info(f"טוען נתוני כתב יד עבור: {selected_student}")
        current_letter_images = st.session_state['students_db'][selected_student]
    else:
        st.sidebar.warning("אין תלמידים במאגר. הוסף תלמיד חדש.")
        current_letter_images = {}

# מסך ראשי - בדיקת המבחן
st.divider()
col1, col2 = st.columns(2)

with col1:
    st.header("📸 העלאת המבחן")
    exam_img_file = st.file_uploader("צילום המבחן:", type=['png', 'jpg', 'jpeg'])

with col2:
    st.header("🎯 המחוון")
    rubric = st.text_area("התשובה המצופה:", height=150)

if st.button("בדוק מבחן עבור התלמיד שנבחר 🚀"):
    if exam_img_file and rubric and current_letter_images:
        with st.spinner('מנתח כתב יד ספציפי...'):
            try:
                model = genai.GenerativeModel('gemini-1.5-pro')
                content_to_send = []
                
                instructions = "השתמש בדוגמאות האותיות הבאות כדי ללמוד את כתב היד של התלמיד:\n"
                for letter, img in current_letter_images.items():
                    instructions += f"התמונה הזו היא האות {letter}\n"
                    content_to_send.append(img)
                
                exam_img = Image.open(exam_img_file)
                content_to_send.append(exam_img)
                content_to_send.append(f"{instructions}\nעכשיו פענח את המבחן והשווה למחוון: {rubric}")
                
                response = model.generate_content(content_to_send)
                st.success("הבדיקה הושלמה!")
                st.write(response.text)
            except Exception as e:
                st.error(f"שגיאה: {e}")
    else:
        st.warning("וודא שבחרת תלמיד עם אותיות, העלית מבחן וכתבת מחוון.")
