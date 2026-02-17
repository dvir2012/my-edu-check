import streamlit as st
import google.generativeai as genai
from PIL import Image
import pandas as pd
from datetime import datetime
import sqlite3
import io

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

init_db()

# ==========================================
# 2. הגדרות AI (תיקון שגיאת ה-404)
# ==========================================
def init_gemini():
    if "GEMINI_API_KEY" not in st.secrets:
        st.error("🔑 מפתח API חסר ב-Secrets!")
        return None
    
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    
    # שימוש בגרסה היציבה והמעודכנת ביותר
    return genai.GenerativeModel('gemini-1.5-flash-latest')

# ==========================================
# 3. עיצוב הממשק (CSS)
# ==========================================
st.set_page_config(page_title="EduCheck AI Pro", page_icon="🎓", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #0f172a; color: white; direction: rtl; text-align: right; }
    .white-bold { color: #ffffff !important; font-weight: 900 !important; text-shadow: 2px 2px 4px #000000; }
    .glass-card { background: rgba(30, 41, 59, 0.7); border: 1px solid #38bdf8; border-radius: 15px; padding: 25px; margin-bottom: 20px; }
    .stButton>button { background: linear-gradient(135deg, #38bdf8 0%, #1d4ed8 100%); color: white !important; font-weight: 700; border-radius: 10px; border: none; width: 100%; }
    label, p, .stMarkdown { color: white !important; font-weight: 600; }
    .stTabs [data-baseweb="tab"] { color: white !important; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

if 'rubric' not in st.session_state:
    st.session_state.rubric = "בדוק את התשובות על פי הבנה עמוקה של החומר, דיוק בפרטים ושימוש במושגים נכונים."

# ==========================================
# 4. הממשק המרכזי
# ==========================================
st.markdown("<h1 class='white-bold' style='text-align: center;'>EduCheck AI Pro 🎓</h1>", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["📄 בדיקת מבחן בכתב יד", "📊 ארכיון ציונים", "⚙️ הגדרות"])

with tab1:
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    
    with col1:
        student_name = st.text_input("שם התלמיד:")
        subject = st.text_input("מקצוע:", "תורה")
        if st.button("✨ צור מחוון אוטומטי"):
            model = init_gemini()
            if model:
                with st.spinner("מייצר מחוון..."):
                    res = model.generate_content(f"צור מחוון תשובות מפורט למבחן ב{subject}")
                    st.session_state.rubric = res.text
        st.session_state.rubric = st.text_area("מחוון הבדיקה:", value=st.session_state.rubric, height=200)
    
    with col2:
        file = st.file_uploader("העלה צילום מבחן (כתב יד עברי):", type=['jpg', 'jpeg', 'png'])
        if st.button("🚀 בדוק מבחן") and file and student_name:
            with st.spinner("מפענח כתב יד עברי ומנתח תוצאות..."):
                try:
                    img = Image.open(file)
                    model = init_gemini()
                    
                    prompt = f"""
                    משימה: פענוח כתב יד עברי ובדיקת מבחן.
                    
                    הוראות:
                    1. סרוק את התמונה וזהה את כתב היד העברי של התלמיד {student_name}.
                    2. שים לב לאותיות דומות בעברית (ד/ר, ב/כ, ח/ת) ופענח לפי ההקשר.
                    3. השווה את התוכן למחוון הבא: {st.session_state.rubric}
                    
                    ענה בעברית בפורמט הבא:
                    ציון סופי: [מספר]
                    מה היה טוב: [פירוט]
                    נקודות לשיפור: [פירוט]
                    טקסט שפוענח מהמבחן: [הצג את תוכן תשובות התלמיד שזיהית]
                    """
                    
                    response = model.generate_content([prompt, img])
                    save_to_db(student_name, subject, response.text)
                    
                    st.success("הניתוח הושלם בהצלחה!")
                    st.markdown("---")
                    st.write(response.text)
                except Exception as e:
                    st.error(f"שגיאה בניתוח המבחן: {e}")
    st.markdown("</div>", unsafe_allow_html=True)

with tab2:
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    df = load_from_db()
    if not df.empty:
        st.dataframe(df, use_container_width=True)
        csv = df.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 הורד אקסל (CSV)", data=csv, file_name="exams_results.csv")
    else:
        st.info("אין נתונים בארכיון עדיין.")
    st.markdown("</div>", unsafe_allow_html=True)

with tab3:
    if st.button("🔴 מחיקת כל הארכיון"):
        conn = sqlite3.connect('results.db')
        conn.execute("DELETE FROM exams")
        conn.commit()
        conn.close()
        st.success("הארכיון נמחק.")
        st.rerun()
