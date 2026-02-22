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
# 2. אתחול ה-AI (שימוש ברשימת המודלים שלך)
# ==========================================
def init_gemini():
    if "GEMINI_API_KEY" not in st.secrets:
        st.error("🔑 מפתח API חסר ב-Secrets!")
        return None
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
        os.environ["GOOGLE_API_KEY"] = api_key
        genai.configure(api_key=api_key)
        
        # שימוש במודל שנבחר בטאב הגדרות
        model_id = st.session_state.get('active_model', 'models/gemini-2.0-flash')
        return genai.GenerativeModel(model_id)
    except Exception as e:
        st.error(f"שגיאה בחיבור למודל {st.session_state.active_model}: {e}")
        return None

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

# הגדרת ברירת מחדל למודל
if 'active_model' not in st.session_state:
    st.session_state.active_model = 'models/gemini-2.0-flash'

# ==========================================
# 4. הממשק המרכזי
# ==========================================
st.markdown("<h1 class='white-bold' style='text-align: center;'>EduCheck AI Pro 🎓</h1>", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["📄 בדיקת מבחן", "📊 ארכיון", "⚙️ בחירת מודל"])

with tab1:
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        student_name = st.text_input("שם התלמיד:")
        subject = st.text_input("מקצוע:", "תורה")
        rubric = st.text_area("מחוון בדיקה:", "בדוק את התשובות על פי הבנה עמוקה ודיוק.", height=150)
    
    with col2:
        file = st.file_uploader("העלה צילום מבחן:", type=['jpg', 'jpeg', 'png'])
        if st.button("🚀 בדוק מבחן"):
            if not file or not student_name:
                st.warning("מלא את כל הפרטים.")
            else:
                with st.spinner(f"מנתח באמצעות {st.session_state.active_model}..."):
                    model = init_gemini()
                    if model:
                        try:
                            img = Image.open(file)
                            prompt = f"פענח כתב יד עבור {student_name} ב{subject}. מחוון: {rubric}. ענה בעברית."
                            response = model.generate_content([prompt, img])
                            save_to_db(student_name, subject, response.text)
                            st.markdown(response.text)
                        except Exception as e:
                            st.error(f"המודל {st.session_state.active_model} לא זמין כרגע. נסה לבחור מודל 2.0 בטאב הגדרות. שגיאה: {e}")
    st.markdown("</div>", unsafe_allow_html=True)

with tab2:
    st.dataframe(load_from_db(), use_container_width=True)

with tab3:
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    st.subheader("בחר מודל מהרשימה ששלחת:")
    
    # רשימת המודלים שסיפקת
    model_list = [
        'models/gemini-2.5-flash',
        'models/gemini-2.5-pro',
        'models/gemini-2.0-flash',
        'models/gemini-2.0-flash-001'
    ]
    
    selected = st.radio("מודל פעיל:", model_list, index=model_list.index(st.session_state.active_model))
    
    if selected != st.session_state.active_model:
        st.session_state.active_model = selected
        st.success(f"המודל הוחלף ל: {selected}")
    
    st.info("הערה: מודלים מסוג 2.5 הם חדשים מאוד. אם הם מחזירים שגיאה, השתמש ב-2.0 Flash.")
    st.markdown("</div>", unsafe_allow_html=True)
