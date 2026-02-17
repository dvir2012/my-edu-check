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
# 2. עיצוב וחיבור AI
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

def init_gemini():
    if "GEMINI_API_KEY" not in st.secrets:
        st.error("🔑 מפתח API חסר ב-Secrets!")
        return None
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    return genai.GenerativeModel('gemini-1.5-flash')

if 'rubric' not in st.session_state:
    st.session_state.rubric = "מחוון ברירת מחדל: בדוק דיוק, הבנה, דקדוק והלכה/היסטוריה. תן נקודות חלקיות לכל שאלה."

# ==========================================
# 3. ממשק המשתמש (Tabs)
# ==========================================
st.markdown("<h1 class='white-bold' style='text-align: center;'>EduCheck AI Pro 🎓</h1>", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["📄 בדיקה ומחוון", "📊 ארכיון שמור", "⚙️ הגדרות"])

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
            with st.spinner("Gemini מנתח את כתב היד..."):
                try:
                    img = Image.open(file)
                    model_ai = init_gemini()
                    
                    # פרומפט חזק שמחליף את הצורך ב-OCR חיצוני
                    prompt = f"""
                    משימה: בצע OCR לכתב היד העברי בתמונה ולאחר מכן בדוק את המבחן.
                    
                    שם התלמיד: {student_name}
                    מקצוע: {subject}
                    מחוון בדיקה: {st.session_state.rubric}
                    
                    הוראות:
                    1. זהה את הטקסט הכתוב בעברית בתמונה (גם אם הוא נמהר או צפוף).
                    2. השווה את התשובות למחוון.
                    3. ענה בעברית בפורמט הבא בלבד:
                    
                    ציון: [מספר בין 1 ל-100]
                    
                    מה היה טוב:
                    [פירוט]
                    
                    מה היה לא טוב:
                    [פירוט]
                    
                    הסבר לכל שאלה:
                    [פירוט של מה התלמיד כתב לעומת מה שהיה צריך לכתוב]
                    """
                    
                    response = model_ai.generate_content([prompt, img])
                    
                    # שמירה לארכיון
                    save_to_db(student_name, subject, response.text)
                    
                    st.success("הבדיקה הושלמה!")
                    st.markdown("---")
                    st.write(response.text)
                except Exception as e:
                    st.error(f"שגיאה בניתוח המבחן: {e}")
    st.markdown("</div>", unsafe_allow_html=True)

with tab2:
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    db_data = load_from_db()
    if not db_data.empty:
        st.dataframe(db_data, use_container_width=True)
        csv = db_data.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 הורד אקסל (CSV)", data=csv, file_name="archive.csv")
    else: st.info("הארכיון ריק.")
    st.markdown("</div>", unsafe_allow_html=True)

with tab3:
    if st.button("🔴 מחיקת ארכיון"):
        conn = sqlite3.connect('results.db'); conn.execute("DELETE FROM exams"); conn.commit(); conn.close()
        st.rerun()
