import streamlit as st
import google.generativeai as genai
from PIL import Image
import cv2
import numpy as np
import pandas as pd
from datetime import datetime
import sqlite3
import easyocr
import io
import os

# ==========================================
# 1. בסיס נתונים (SQLite) - יציב וחסכוני
# ==========================================
def init_db():
    try:
        conn = sqlite3.connect('results.db', check_same_thread=False)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS exams 
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                      date TEXT, student_name TEXT, subject TEXT, result TEXT)''')
        conn.commit()
        conn.close()
    except Exception as e:
        st.error(f"שגיאה בבסיס הנתונים: {e}")

def save_to_db(name, subject, result):
    try:
        conn = sqlite3.connect('results.db', check_same_thread=False)
        c = conn.cursor()
        date_now = datetime.now().strftime("%d/%m/%Y %H:%M")
        c.execute("INSERT INTO exams (date, student_name, subject, result) VALUES (?, ?, ?, ?)",
                  (date_now, name, subject, result))
        conn.commit()
        conn.close()
    except Exception as e:
        st.error(f"שגיאה בשמירה: {e}")

def load_from_db():
    try:
        conn = sqlite3.connect('results.db', check_same_thread=False)
        df = pd.read_sql_query("SELECT date, student_name, subject, result FROM exams", conn)
        conn.close()
        return df
    except:
        return pd.DataFrame()

init_db()

# ==========================================
# 2. EasyOCR - שיפור טעינה ועיבוד (Memory Optimized)
# ==========================================
@st.cache_resource(show_spinner="טוען מודל OCR עברי... (בפעם הראשונה זה לוקח 1-2 דקות)")
def load_ocr():
    try:
        # gpu=False הכרחי ל-Streamlit Cloud כדי למנוע MemoryError
        return easyocr.Reader(['he', 'en'], gpu=False, download_enabled=True)
    except Exception as e:
        st.warning(f"המערכת תעבוד ללא OCR (רק Gemini): {e}")
        return None

reader = load_ocr()

def perform_ocr(image):
    if reader is None:
        return "OCR Not Available"
    
    # עיבוד מקדים לשיפור הדיוק
    img_array = np.array(image.convert('RGB'))
    gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    # שיפור קונטרסט
    enhanced = cv2.convertScaleAbs(gray, alpha=1.2, beta=10)
    
    # שמירה על סדר שורות ופסקאות
    results = reader.readtext(enhanced, detail=0, paragraph=True)
    return "\n".join(results)

# ==========================================
# 3. עיצוב (CSS) וחיבור AI
# ==========================================
st.set_page_config(page_title="EduCheck AI Pro", page_icon="🎓", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #0f172a; color: white; direction: rtl; text-align: right; }
    .white-bold { color: #ffffff !important; font-weight: 900 !important; text-shadow: 2px 2px 4px #000000; }
    .glass-card { background: rgba(30, 41, 59, 0.7); border: 1px solid #38bdf8; border-radius: 15px; padding: 25px; margin-bottom: 20px; }
    .stButton>button { background: linear-gradient(135deg, #38bdf8 0%, #1d4ed8 100%); color: white !important; font-weight: 700; border-radius: 10px; border: none; }
    label, p, .stMarkdown { color: white !important; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

def init_gemini():
    if "GEMINI_API_KEY" not in st.secrets:
        st.error("🔑 מפתח API חסר ב-Secrets!")
        return None
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    return genai.GenerativeModel('gemini-1.5-flash')

# ==========================================
# 4. ממשק המשתמש
# ==========================================
st.markdown("<h1 class='white-bold' style='text-align: center;'>EduCheck AI Pro 🎓</h1>", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["📄 בדיקת מבחן", "📊 ארכיון (נשמר ב-DB)", "⚙️ הגדרות"])

if 'rubric' not in st.session_state:
    st.session_state.rubric = ""

with tab1:
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    
    with col1:
        student_name = st.text_input("שם התלמיד:")
        subject = st.text_input("מקצוע:", "תורה")
        if st.button("✨ צור מחוון אוטומטי"):
            model_ai = init_gemini()
            if model_ai:
                with st.spinner("מייצר מחוון..."):
                    res = model_ai.generate_content(f"צור מחוון תשובות למבחן ב{subject}")
                    st.session_state.rubric = res.text
        st.session_state.rubric = st.text_area("מחוון הבדיקה:", value=st.session_state.rubric, height=200)
    
    with col2:
        file = st.file_uploader("העלה צילום מבחן:", type=['jpg', 'jpeg', 'png'])
        if st.button("🚀 בדוק מבחן") and file and student_name:
            with st.spinner("מזהה כתב יד ומנתח..."):
                try:
                    img = Image.open(file)
                    # שלב 1: OCR עם עיבוד תמונה
                    detected_text = perform_ocr(img)
                    
                    # שלב 2: Gemini
                    model_ai = init_gemini()
                    prompt = f"""
                    תסתכל על התמונה + על הטקסט שזיהיתי ב-OCR: "{detected_text}"
                    השתמש במחוון הבא: {st.session_state.rubric}
                    תן ציון מ-1 עד 100 לתלמיד {student_name}.
                    ענה בעברית:
                    ציון: [מספר]
                    מה היה טוב: [פירוט]
                    מה היה לא טוב: [פירוט]
                    הסבר לכל שאלה: [פירוט]
                    """
                    response = model_ai.generate_content([prompt, img])
                    
                    # שלב 3: שמירה ל-DB
                    save_to_db(student_name, subject, response.text)
                    st.success("הבדיקה הושלמה ונשמרה!")
                    st.markdown(response.text)
                except Exception as e:
                    st.error(f"שגיאה: {e}")
    st.markdown("</div>", unsafe_allow_html=True)

with tab2:
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    data = load_from_db()
    if not data.empty:
        st.dataframe(data, use_container_width=True)
        st.download_button("📥 הורד אקסל (CSV)", data=data.to_csv(index=False).encode('utf-8-sig'), file_name="archive.csv")
    else:
        st.info("הארכיון ריק.")
    st.markdown("</div>", unsafe_allow_html=True)

with tab3:
    if st.button("🔴 מחיקת כל הארכיון"):
        conn = sqlite3.connect('results.db', check_same_thread=False)
        conn.execute("DELETE FROM exams")
        conn.commit()
        conn.close()
        st.rerun()
