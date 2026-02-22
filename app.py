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
# 2. אתחול ה-AI (תוקן - ללא -latest)
# ==========================================
def init_gemini():
    if "GEMINI_API_KEY" not in st.secrets:
        st.error("🔑 מפתח API חסר ב-Secrets! הגדר אותו ב-Streamlit Cloud.")
        return None
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
        os.environ["GOOGLE_API_KEY"] = api_key
        genai.configure(api_key=api_key)
        # ✅ תוקן: שם מודל מדויק ללא -latest
        return genai.GenerativeModel('gemini-1.5-flash')
    except Exception as e:
        st.error(f"שגיאה בחיבור ל-Gemini: {e}")
        return None

# ==========================================
# 3. עיצוב הממשק (CSS מתקדם)
# ==========================================
st.set_page_config(page_title="EduCheck AI Pro", page_icon="🎓", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #0f172a; color: white; direction: rtl; text-align: right; }
    .white-bold { color: #ffffff !important; font-weight: 900 !important; text-shadow: 2px 2px 4px #000000; }
    .glass-card { background: rgba(30, 41, 59, 0.7); border: 1px solid #38bdf8; border-radius: 15px; padding: 25px; margin-bottom: 20px; }
    .stButton>button { background: linear-gradient(135deg, #38bdf8 0%, #1d4ed8 100%); color: white !important; font-weight: 700; border-radius: 10px; border: none; width: 100%; height: 3.5em; }
    label, p, .stMarkdown, h1, h2, h3 { color: white !important; }
    .stTabs [data-baseweb="tab"] { color: white !important; font-weight: bold; }
    input, textarea { background-color: #1e293b !important; color: white !important; border: 1px solid #38bdf8 !important; }
</style>
""", unsafe_allow_html=True)

init_db()

# ==========================================
# 4. הממשק המרכזי
# ==========================================
st.markdown("<h1 class='white-bold' style='text-align: center;'>EduCheck AI Pro 🎓</h1>", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["📄 בדיקת מבחן בכתב יד", "📊 ארכיון תוצאות", "⚙️ הגדרות מערכת"])

if 'rubric' not in st.session_state:
    st.session_state.rubric = "בדוק את התשובות על פי הבנה עמוקה, דיוק בפרטים ושימוש במושגים נכונים."

# --- טאב 1: בדיקת מבחן ---
with tab1:
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    
    with col1:
        student_name = st.text_input("שם התלמיד:")
        subject = st.text_input("מקצוע:", "תורה")
        
        if st.button("✨ צור מחוון אוטומטי (AI)"):
            model = init_gemini()
            if model:
                with st.spinner("מייצר מחוון תשובות..."):
                    try:
                        res = model.generate_content(f"צור מחוון תשובות מפורט ותקני למבחן ב{subject} בעברית.")
                        st.session_state.rubric = res.text
                    except Exception as e:
                        st.error(f"שגיאה: {e}")

        st.session_state.rubric = st.text_area("מחוון הבדיקה (תשובות נכונות):", value=st.session_state.rubric, height=250)
    
    with col2:
        file = st.file_uploader("העלה צילום מבחן (כתב יד):", type=['jpg', 'jpeg', 'png'])
        
        if st.button("🚀 התחל בדיקה אוטומטית"):
            if not file or not student_name:
                st.warning("חובה להזין שם תלמיד ולהעלות קובץ תמונה.")
            else:
                with st.spinner("מפענח כתב יד ומנתח תוצאות..."):
                    try:
                        img = Image.open(file)
                        model = init_gemini()
                        
                        if model:
                            prompt = f"""
                            אתה מורה מומחה לפענוח כתב יד עברי.
                            משימה:
                            1. פענח את כתב היד בתמונה עבור התלמיד {student_name} בנושא {subject}.
                            2. השווה את התשובות למחוון הבא: {st.session_state.rubric}
                            
                            ענה בעברית בפורמט הבא:
                            ## תוצאות עבור {student_name}
                            **ציון סופי:** [מספר]
                            **מה היה טוב:** [פירוט]
                            **נקודות לשיפור:** [פירוט]
                            **הטקסט שפענחת מהתמונה:** [הטקסט המלא]
                            """
                            response = model.generate_content([prompt, img])
                            save_to_db(student_name, subject, response.text)
                            st.success("הבדיקה הושלמה בהצלחה!")
                            st.markdown("---")
                            st.markdown(response.text)
                    except Exception as e:
                        st.error(f"שגיאה בניתוח המבחן: {e}")
    st.markdown("</div>", unsafe_allow_html=True)

# --- טאב 2: ארכיון ---
with tab2:
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    df = load_from_db()
    if not df.empty:
        st.dataframe(df, use_container_width=True)
        csv = df.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 הורד את כל ההיסטוריה (CSV)", data=csv, file_name="history.csv")
    else:
        st.info("הארכיון ריק כרגע.")
    st.markdown("</div>", unsafe_allow_html=True)

# --- טאב 3: הגדרות ---
with tab3:
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    st.write("ניהול בסיס הנתונים:")
    if st.button("🔴 מחיקת כל הארכיון לצמיתות"):
        conn = sqlite3.connect('results.db')
        conn.execute("DELETE FROM exams")
        conn.commit()
        conn.close()
        st.success("כל הנתונים נמחקו.")
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)
