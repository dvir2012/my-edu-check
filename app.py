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
# 1. בסיס נתונים (SQLite) - יציב וקבוע
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
        st.error(f"שגיאה באתחול בסיס הנתונים: {e}")

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

init_db()

# ==========================================
# 2. EasyOCR - שיפור 1: עיבוד תמונה וסדר שורות
# ==========================================
@st.cache_resource
def load_ocr():
    try:
        # ניסיון טעינה עם קוד עברית סטנדרטי, ללא GPU למניעת קריסות ב-Cloud
        return easyocr.Reader(['he', 'en'], gpu=False)
    except:
        return None

reader = load_ocr()

def perform_ocr(image):
    if reader is None:
        return "שירות ה-OCR לא זמין כרגע."
    
    # המרה ל-numpy ועיבוד מקדים (Preprocessing)
    img_array = np.array(image.convert('RGB'))
    gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    
    # שיפור קונטרסט (Contrast Enhancement) - עוזר לכתב יד חלש
    enhanced = cv2.convertScaleAbs(gray, alpha=1.2, beta=10)
    
    # זיהוי עם paragraph=True לשמירה על מבנה שורות (שיפור 2)
    results = reader.readtext(enhanced, detail=0, paragraph=True)
    return "\n".join(results)

# ==========================================
# 3. עיצוב (CSS) וחיבור AI
# ==========================================
st.set_page_config(page_title="EduCheck AI Pro", page_icon="🎓", layout="wide")

# עיצוב ה-Glassmorphism והצבעים
st.markdown("""
<style>
    .stApp { background-color: #0f172a; color: white; direction: rtl; text-align: right; }
    .white-bold { color: #ffffff !important; font-weight: 900 !important; text-shadow: 2px 2px 4px #000000; }
    .glass-card { background: rgba(30, 41, 59, 0.7); border: 1px solid #38bdf8; border-radius: 15px; padding: 25px; margin-bottom: 20px; }
    .stButton>button { background: linear-gradient(135deg, #38bdf8 0%, #1d4ed8 100%); color: white !important; font-weight: 700; border-radius: 10px; border: none; width: 100%; }
    .logout-btn>button { background: linear-gradient(135deg, #ef4444 0%, #991b1b 100%) !important; }
    label, p, .stMarkdown { color: white !important; font-weight: 600; }
    .stTabs [data-baseweb="tab"] { color: white !important; }
</style>
""", unsafe_allow_html=True)

def init_gemini():
    if "GEMINI_API_KEY" not in st.secrets:
        st.error("🔑 מפתח API חסר ב-Secrets!")
        return None
    try:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        return genai.GenerativeModel('gemini-1.5-flash')
    except Exception as e:
        st.error(f"שגיאה בחיבור ל-Gemini: {e}")
        return None

# אתחול Session State למחוון
if 'rubric' not in st.session_state:
    st.session_state.rubric = "מחוון ברירת מחדל: בדוק דיוק היסטורי/הלכתי ודקדוק."

# ==========================================
# 4. ממשק המשתמש (Tabs)
# ==========================================
st.markdown("<h1 class='white-bold' style='text-align: center;'>EduCheck AI Pro 🎓</h1>", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["📄 בדיקה ומחוון", "📊 ארכיון (SQLite)", "⚙️ הגדרות"])

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
            with st.spinner("מזהה כתב יד ומנתח ב-AI..."):
                try:
                    img = Image.open(file)
                    
                    # שלב 1: OCR משופר עם עיבוד תמונה
                    detected_text = perform_ocr(img)
                    
                    # שלב 2: Gemini - פרומפט מובנה (שיפור 3)
                    model_ai = init_gemini()
                    prompt = f"""
                    תסתכל על התמונה המצורפת ועל הטקסט שחולץ מה-OCR:
                    "{detected_text}"
                    
                    השתמש במחוון הבא כבסיס לבדיקה: {st.session_state.rubric}
                    
                    תן ציון מ-1 עד 100 עבור התלמיד {student_name}.
                    תכתוב בעברית בצורה מסודרת בדיוק כך:
                    ציון: [כאן הציון]
                    מה היה טוב: [פירוט]
                    מה היה לא טוב: [פירוט]
                    הסבר לכל שאלה: [השוואה מפורטת בין תשובת התלמיד למחוון]
                    """
                    response = model_ai.generate_content([prompt, img])
                    
                    # שלב 3: שמירה לבסיס הנתונים
                    save_to_db(student_name, subject, response.text)
                    
                    st.success("הבדיקה הושלמה ונשמרה!")
                    st.markdown("### 📝 תוצאה:")
                    st.write(response.text)
                except Exception as e:
                    st.error(f"שגיאה במהלך הבדיקה: {e}")
    st.markdown("</div>", unsafe_allow_html=True)

with tab2:
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    db_data = load_from_db()
    if not db_data.empty:
        st.dataframe(db_data, use_container_width=True)
        csv = db_data.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 הורד אקסל מלא (CSV)", data=csv, file_name="exams_archive.csv")
    else:
        st.info("הארכיון ריק.")
    st.markdown("</div>", unsafe_allow_html=True)

with tab3:
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    st.subheader("ניהול מערכת")
    if st.button("🔴 מחיקת כל הארכיון"):
        conn = sqlite3.connect('results.db', check_same_thread=False)
        conn.execute("DELETE FROM exams")
        conn.commit()
        conn.close()
        st.warning("הארכיון נמחק בהצלחה.")
        st.rerun()
    st.markdown("---")
    st.write("**מצב מערכת:** אופטימלי (ללא PyTorch)")
    st.write(f"**תאריך:** {datetime.now().strftime('%d/%m/%Y')}")
    st.markdown("</div>", unsafe_allow_html=True)
