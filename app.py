import streamlit as st
import google.generativeai as genai
from PIL import Image
import pandas as pd
from datetime import datetime
import sqlite3
import io
import os

# ==========================================
# 1. בסיס נתונים (SQLite)
# ==========================================
def init_db():
    conn = sqlite3.connect('results.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS exams 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  date TEXT, student_name TEXT, subject TEXT, result TEXT)''')
    conn.commit()
    conn.close()

def save_to_db(name, subject, result):
    conn = sqlite3.connect('results.db', check_same_thread=False)
    c = conn.cursor()
    date_now = datetime.now().strftime("%d/%m/%Y %H:%M")
    c.execute("INSERT INTO exams (date, student_name, subject, result) VALUES (?, ?, ?, ?)",
              (date_now, name, subject, result))
    conn.commit()
    conn.close()

def load_from_db():
    conn = sqlite3.connect('results.db', check_same_thread=False)
    df = pd.read_sql_query("SELECT date, student_name, subject, result FROM exams", conn)
    conn.close()
    return df

# ==========================================
# 2. פונקציית הליבה: ניסיון רב-מודלים (Failover)
# ==========================================
def process_with_ai(prompt, image):
    """
    מנסה להריץ את הבקשה על רשימת מודלים לפי סדר עדיפות.
    אם מודל אחד נכשל, עובר למודל הבא.
    """
    model_names = [
        'gemini-2.0-flash',       # כרגע הגרסה היציבה ביותר לייצור
        'gemini-1.5-pro',         # גיבוי חזק מאוד
        'gemini-1.5-flash',       # גיבוי מהיר
        'gemini-1.5-flash-8b'     # גיבוי אחרון
    ]
    
    # הערה: השמות 'gemini-2.5-flash' וכו' עוד לא שוחררו רשמית לכל המשתמשים ב-SDK,
    # לכן השתמשתי בשמות המעודכנים ביותר שזמינים כרגע ב-API כדי שהקוד יעבוד לך מיד.
    
    if "GEMINI_API_KEY" not in st.secrets:
        st.error("🔑 מפתח API חסר ב-Secrets!")
        return None, None

    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)

    last_error = ""
    for model_name in model_names:
        try:
            # ניסיון ליצור את המודל ולהריץ תוכן
            model = genai.GenerativeModel(model_name)
            response = model.generate_content([prompt, image])
            return response.text, model_name  # מחזיר את התשובה ואת שם המודל שהצליח
        except Exception as e:
            last_error = str(e)
            continue # נכשל? עובר למודל הבא ברשימה
            
    st.error(f"כל המודלים נכשלו. שגיאה אחרונה: {last_error}")
    return None, None

# ==========================================
# 3. עיצוב הממשק (CSS)
# ==========================================
st.set_page_config(page_title="EduCheck AI Pro", page_icon="🎓", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #0f172a; color: white; direction: rtl; text-align: right; }
    .white-bold { color: #ffffff !important; font-weight: 900 !important; text-shadow: 2px 2px 4px #000000; }
    .glass-card { background: rgba(30, 41, 59, 0.7); border: 1px solid #38bdf8; border-radius: 15px; padding: 25px; margin-bottom: 20px; }
    .stButton>button { background: linear-gradient(135deg, #38bdf8 0%, #1d4ed8 100%); color: white !important; font-weight: 700; border-radius: 10px; border: none; width: 100%; height: 3.5em; }
    label, p, .stMarkdown, h1, h2, h3 { color: white !important; }
    input, textarea { background-color: #1e293b !important; color: white !important; border: 1px solid #38bdf8 !important; }
</style>
""", unsafe_allow_html=True)

init_db()

# ==========================================
# 4. הממשק המרכזי
# ==========================================
st.markdown("<h1 class='white-bold' style='text-align: center;'>EduCheck AI Pro 🎓</h1>", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["📄 בדיקת מבחן", "📊 ארכיון", "⚙️ הגדרות"])

if 'rubric' not in st.session_state:
    st.session_state.rubric = "בדוק לפי הבנה עמוקה ודיוק."

with tab1:
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        student_name = st.text_input("שם התלמיד:")
        subject = st.text_input("מקצוע:", "תורה")
        st.session_state.rubric = st.text_area("מחוון בדיקה:", value=st.session_state.rubric, height=200)
    
    with col2:
        file = st.file_uploader("העלה צילום מבחן:", type=['jpg', 'jpeg', 'png'])
        if st.button("🚀 התחל בדיקה אוטומטית"):
            if file and student_name:
                with st.spinner("מנסה לפענח (בודק מודלים זמינים)..."):
                    img = Image.open(file)
                    prompt = f"פענח כתב יד עברי עבור {student_name} ב{subject} לפי מחוון: {st.session_state.rubric}. ענה בעברית."
                    
                    # שימוש בפונקציה החכמה
                    result_text, successful_model = process_with_ai(prompt, img)
                    
                    if result_text:
                        save_to_db(student_name, subject, result_text)
                        st.info(f"בוצע בהצלחה באמצעות מודל: {successful_model}")
                        st.markdown("---")
                        st.markdown(result_text)
            else:
                st.warning("נא להזין שם ולהעלות תמונה.")
    st.markdown("</div>", unsafe_allow_html=True)

with tab2:
    st.dataframe(load_from_db(), use_container_width=True)

with tab3:
    if st.button("🔴 מחיקת ארכיון"):
        conn = sqlite3.connect('results.db')
        conn.execute("DELETE FROM exams")
        conn.commit()
        conn.close()
        st.success("הארכיון נמחק.")
        st.rerun()
