import streamlit as st
import google.generativeai as genai
from PIL import Image
from streamlit_gsheets import GSheetsConnection
import pandas as pd

st.set_page_config(page_title="EduCheck Pro", layout="wide")

# חיבור לגוגל שיטס
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    existing_data = conn.read(spreadsheet=st.secrets["gsheets_url"])
except:
    existing_data = pd.DataFrame(columns=["student_name"])

# הגדרת Gemini
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

st.title("📝 EduCheck Pro - מאגר תלמידים בענן")

# סרגל צדי
st.sidebar.header("📁 ניהול תלמידים")
action = st.sidebar.radio("מה ברצונך למשות?", ["בחירת תלמיד קיים", "הוספת תלמיד חדש"])

if action == "הוספת תלמיד חדש":
    new_name = st.sidebar.text_input("שם התלמיד:")
    if st.sidebar.button("שמור תלמיד במאגר"):
        if new_name:
            new_row = pd.DataFrame([{"student_name": new_name}])
            updated_df = pd.concat([existing_data, new_row], ignore_index=True)
            conn.update(spreadsheet=st.secrets["gsheets_url"], data=updated_df)
            st.sidebar.success(f"התלמיד {new_name} נשמר באקסל!")
            st.rerun()

else:
    if not existing_data.empty:
        student_list = existing_data["student_name"].tolist()
        selected_student = st.sidebar.selectbox("בחר תלמיד מהרשימה:", student_list)
    else:
        st.sidebar.warning("אין תלמידים רשומים.")

# העלאת דוגמת הכתב (חד פעמי לכל סשן)
st.subheader(f"📖 שלב 1: לימוד כתב היד")
sample_file = st.file_uploader("העלה דף עם אותיות א-ת (כדי שה-AI יכיר את הכתב):", type=['png', 'jpg', 'jpeg'])

# בדיקת המבחן
st.subheader(f"✍️ שלב 2: בדיקת המבחן")
col1, col2 = st.columns(2)
with col1:
    exam_file = st.file_uploader("העלה צילום מבחן:", type=['png', 'jpg', 'jpeg'])
with col2:
    rubric = st.text_area("מחוון (התשובה הנכונה):")

if st.button("הפעל בדיקה 🚀"):
    if sample_file and exam_file and rubric:
        with st.spinner('מנתח...'):
            model = genai.GenerativeModel('gemini-1.5-pro')
            img_sample = Image.open(sample_file)
            img_exam = Image.open(exam_file)
            
            prompt = f"למד את הכתב מהתמונה הראשונה ופענח את המבחן בשנייה. השווה למחוון: {rubric}. ענה בעברית."
            response = model.generate_content([prompt, img_sample, img_exam])
            
            st.success("תוצאות:")
            st.write(response.text)
    else:
        st.warning("נא להעלות את כל הקבצים הנדרשים.")
