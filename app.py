import streamlit as st
import google.generativeai as genai
from PIL import Image
from streamlit_gsheets import GSheetsConnection
import pandas as pd

st.set_page_config(page_title="EduCheck Pro - Multi-Lang", layout="wide")

# חיבור לגוגל שיטס (הזיכרון הקבוע)
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    existing_data = conn.read(spreadsheet=st.secrets["gsheets_url"])
except:
    existing_data = pd.DataFrame(columns=["student_name"])

# הגדרת Gemini
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

st.title("📝 EduCheck Pro - עברית ואנגלית")

# סרגל צדי - ניהול תלמידים
st.sidebar.header("👥 מאגר תלמידים")
action = st.sidebar.radio("פעולה:", ["בחירת תלמיד", "רישום תלמיד חדש"])

if action == "רישום תלמיד חדש":
    new_name = st.sidebar.text_input("שם התלמיד:")
    if st.sidebar.button("שמור תלמיד"):
        if new_name:
            new_row = pd.DataFrame([{"student_name": new_name}])
            updated_df = pd.concat([existing_data, new_row], ignore_index=True)
            conn.update(spreadsheet=st.secrets["gsheets_url"], data=updated_df)
            st.sidebar.success(f"התלמיד {new_name} נשמר!")
            st.rerun()
else:
    if not existing_data.empty:
        student_list = existing_data["student_name"].tolist()
        selected_student = st.sidebar.selectbox("בחר תלמיד:", student_list)
    else:
        st.sidebar.warning("המאגר ריק.")

st.divider()

# שלב 1: לימוד כתב היד (3 תמונות)
st.header("🔤 שלב 1: לימוד הכתב (עברית/אנגלית)")
st.write("העלה 3 תמונות שמכילות את כל האותיות (א-ת וגם A-Z) ומספרים:")

col_a, col_b, col_c = st.columns(3)
with col_a:
    sample1 = st.file_uploader("תמונה 1 (למשל א-ח / A-H):", type=['png', 'jpg', 'jpeg'])
with col_b:
    sample2 = st.file_uploader("תמונה 2 (למשל ט-ע / I-P):", type=['png', 'jpg', 'jpeg'])
with col_c:
    sample3 = st.file_uploader("תמונה 3 (למשל פ-ת / Q-Z):", type=['png', 'jpg', 'jpeg'])

# שלב 2: המבחן
st.header("📄 שלב 2: בדיקת המבחן")
col_ex, col_rub = st.columns(2)
with col_ex:
    exam_file = st.file_uploader("העלה את דף המבחן:", type=['png', 'jpg', 'jpeg'])
with col_rub:
    rubric = st.text_area("מחוון תשובות (כתוב כאן מה התשובה הנכונה):", height=150)

if st.button("נתח מבחן וחשב ציון 🚀"):
    if sample1 and exam_file and rubric:
        with st.spinner('ה-AI לומד את הכתב ומנתח...'):
            try:
                model = genai.GenerativeModel('gemini-1.5-pro')
                
                # הכנת התמונות למודל
                images = [Image.open(sample1)]
                if sample2: images.append(Image.open(sample2))
                if sample3: images.append(Image.open(sample3))
                
                exam_img = Image.open(exam_file)
                images.append(exam_img)
                
                prompt = f"""
                אתה עוזר הוראה מקצועי. קיבלת תמונות של כתב היד של התלמיד (בעברית ובאנגלית).
                1. למד את הכתב מהתמונות הראשונות.
                2. קרא את המבחן בתמונה האחרונה.
                3. השווה למחוון: {rubric}
                
                ענה בעברית:
                - תמלול התשובה של התלמיד.
                - האם התשובה נכונה?
                - ציון סופי.
                """
                
                response = model.generate_content([prompt] + images)
                st.success("הפענוח הושלם!")
                st.markdown("### תוצאות הבדיקה:")
                st.write(response.text)
            except Exception as e:
                st.error(f"שגיאה: {e}")
    else:
        st.warning("נא להעלות לפחות את התמונה הראשונה של הכתב, את המבחן ולמלא מחוון.")
