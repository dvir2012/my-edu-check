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

# ==========================================
# 2. הגדרות AI (התיקון המרכזי לשגיאת 404)
# ==========================================
def init_gemini():
    if "GEMINI_API_KEY" not in st.secrets:
        st.error("🔑 מפתח API חסר ב-Secrets!")
        return None
    
    try:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        # שימוש במודל הפלאש העדכני ביותר - הוא היציב ביותר לתמונות וטקסט בעברית
        model = genai.GenerativeModel('gemini-1.5-flash')
        return model
    except Exception as e:
        st.error(f"שגיאה בחיבור ל-Gemini: {e}")
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
    .stButton>button { background: linear-gradient(135deg, #38bdf8 0%, #1d4ed8 100%); color: white !important; font-weight: 700; border-radius: 10px; border: none; width: 100%; height: 3em; }
    label, p, .stMarkdown { color: white !important; font-weight: 600; }
    .stTabs [data-baseweb="tab"] { color: white !important; font-weight: bold; }
    input { background-color: #1e293b !important; color: white !important; }
</style>
""", unsafe_allow_html=True)

init_db()

# ==========================================
# 4. הממשק המרכזי
# ==========================================
st.markdown("<h1 class='white-bold' style='text-align: center;'>EduCheck AI Pro 🎓</h1>", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["📄 בדיקת מבחן", "📊 ארכיון ציונים", "⚙️ הגדרות"])

if 'rubric' not in st.session_state:
    st.session_state.rubric = "בדוק את התשובות על פי הבנה עמוקה של החומר, דיוק בפרטים ושימוש במושגים נכונים."

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
                    try:
                        # הוספת הוראה ברורה לעברית
                        res = model.generate_content(f"צור מחוון תשובות מפורט למבחן בנושא {subject} בשפה העברית.")
                        st.session_state.rubric = res.text
                    except Exception as e:
                        st.error(f"שגיאה ביצירת מחוון: {e}")

        st.session_state.rubric = st.text_area("מחוון הבדיקה (תשובות נכונות):", value=st.session_state.rubric, height=200)
    
    with col2:
        file = st.file_uploader("העלה צילום מבחן (כתב יד):", type=['jpg', 'jpeg', 'png'])
        
        if st.button("🚀 בדוק מבחן"):
            if not file or not student_name:
                st.warning("נא להזין שם תלמיד ולהעלות קובץ.")
            else:
                with st.spinner("מזהה כתב יד עברי ומנתח תוצאות..."):
                    try:
                        img = Image.open(file)
                        model = init_gemini()
                        
                        if model:
                            # פרומפט ממוקד בכתב יד עברי כפי שביקשת
                            prompt = f"""
                            משימה: פענוח כתב יד עברי (Handwritten Hebrew) ובדיקת מבחן.
                            
                            פרטי המבחן:
                            - תלמיד: {student_name}
                            - נושא: {subject}
                            - מחוון לתיקון: {st.session_state.rubric}
                            
                            הוראות לעבודה:
                            1. זהה את הטקסט בעברית מהתמונה. שים לב לאותיות דומות בכתב יד.
                            2. השווה את תוכן התשובות למחוון שסופק.
                            3. תן ציון הוגן והסבר את השיקולים.
                            
                            ענה בעברית מלאה בפורמט הבא:
                            ## תוצאות עבור {student_name}
                            **ציון סופי:** [מספר]
                            
                            **מה היה טוב:**
                            [פירוט]
                            
                            **נקודות לשיפור:**
                            [פירוט]
                            
                            **הטקסט שזוהה מהמבחן (OCR):**
                            [הצג כאן את מה שפענחת מכתב היד של התלמיד]
                            """
                            
                            response = model.generate_content([prompt, img])
                            save_to_db(student_name, subject, response.text)
                            
                            st.success("הניתוח הושלם!")
                            st.markdown("---")
                            st.markdown(response.text)
                    except Exception as e:
                        st.error(f"שגיאה בניתוח המבחן: {e}")
    st.markdown("</div>", unsafe_allow_html=True)

with tab2:
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    df = load_from_db()
    if not df.empty:
        st.dataframe(df, use_container_width=True)
        csv = df.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 הורד אקסל (CSV)", data=csv, file_name=f"grades_{datetime.now().strftime('%d_%m')}.csv")
    else:
        st.info("אין נתונים בארכיון עדיין.")
    st.markdown("</div>", unsafe_allow_html=True)

with tab3:
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    if st.button("🔴 מחיקת כל הארכיון"):
        conn = sqlite3.connect('results.db')
        conn.execute("DELETE FROM exams")
        conn.commit()
        conn.close()
        st.success("הארכיון נמחק.")
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)
