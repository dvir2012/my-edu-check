import streamlit as st
import google.generativeai as genai
from PIL import Image
import pandas as pd
from datetime import datetime
import sqlite3

# ==========================================
# 0. מנגנון סיסמאות והפרדת משתמשים
# ==========================================
PASSWORDS = [str(i) for i in range(1000, 10000)]

if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'teacher_id' not in st.session_state:
    st.session_state.teacher_id = None

def login_screen():
    st.markdown("<h2 style='text-align:center; color:white;'>כניסה למערכת EduCheck</h2>", unsafe_allow_html=True)
    pwd = st.text_input("הזן סיסמת מורה:", type="password")
    if st.button("התחבר"):
        if pwd in PASSWORDS:
            st.session_state.authenticated = True
            st.session_state.teacher_id = pwd  
            st.rerun()
        else:
            st.error("סיסמה שגויה")

if not st.session_state.authenticated:
    login_screen()
    st.stop()

SUBJECTS_LIST = ["תורה", "נביא", "הלכה", "גמרא", "חשבון", "אנגלית", "שפה","כישורי חיים", "מחשבת ישראל", "היסטוריה", "מדעים", "אזרחות", "אחר"]

# ==========================================
# 1. בסיס נתונים עם תיקון שגיאת עמודה חסרה
# ==========================================
def init_db():
    conn = sqlite3.connect('results.db', check_same_thread=False)
    c = conn.cursor()
    # יצירת הטבלה אם לא קיימת
    c.execute('''CREATE TABLE IF NOT EXISTS exams
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  teacher_id TEXT,
                  date TEXT, 
                  student_name TEXT, 
                  subject TEXT, 
                  result TEXT)''')
    
    # בדיקה אם עמודת teacher_id קיימת (למניעת שגיאת DatabaseError במעבר גרסאות)
    c.execute("PRAGMA table_info(exams)")
    columns = [column[1] for column in c.fetchall()]
    if 'teacher_id' not in columns:
        try:
            c.execute("ALTER TABLE exams ADD COLUMN teacher_id TEXT")
        except:
            pass
            
    conn.commit()
    conn.close()

def save_to_db(name, subject, result):
    conn = sqlite3.connect('results.db', check_same_thread=False)
    c = conn.cursor()
    date_now = datetime.now().strftime("%d/%m/%Y %H:%M")
    c.execute("INSERT INTO exams (teacher_id, date, student_name, subject, result) VALUES (?, ?, ?, ?, ?)",
             (st.session_state.teacher_id, date_now, name, subject, result))
    conn.commit()
    conn.close()

def load_from_db(subject_filter="הכל"):
    conn = sqlite3.connect('results.db', check_same_thread=False)
    tid = st.session_state.teacher_id
    try:
        if subject_filter == "הכל":
            query = "SELECT date, student_name, subject, result FROM exams WHERE teacher_id = ?"
            df = pd.read_sql_query(query, conn, params=(tid,))
        else:
            query = "SELECT date, student_name, subject, result FROM exams WHERE teacher_id = ? AND subject = ?"
            df = pd.read_sql_query(query, conn, params=(tid, subject_filter))
    except Exception as e:
        # אם יש שגיאה בשליפה, נחזיר דאטהפריים ריק כדי לא להקריס את האפליקציה
        df = pd.DataFrame(columns=['date', 'student_name', 'subject', 'result'])
    finally:
        conn.close()
    return df

# ==========================================
# 2. הגדרות AI - המודלים שביקשת
# ==========================================
def init_gemini():
    if "GEMINI_API_KEY" not in st.secrets:
        st.error("🔑 מפתח API חסר!")
        return None
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
    
    model_names =[
            'models/gemini-2.5-flash',
            'models/gemini-2.5-pro',
            'models/gemini-2.0-flash',
            'models/gemini-2.0-flash-001',
       ]
       
    for model_name in model_names:
        try:
            return genai.GenerativeModel(model_name)
        except:
            continue
    return None

# ==========================================
# 3. עיצוב הממשק
# ==========================================
st.set_page_config(page_title="EduCheck AI Pro", page_icon="🎓", layout="wide")
st.markdown("""
<style>
    .stApp { background-color: #0f172a; color: white; direction: rtl; text-align: right; }
    .white-bold { color: #ffffff !important; font-weight: 900 !important; text-shadow: 2px 2px 4px #000000; }
    .glass-card { background: rgba(30, 41, 59, 0.7); border: 1px solid #38bdf8; border-radius: 15px; padding: 25px; margin-bottom: 20px; }
    .stButton>button { background: linear-gradient(135deg, #38bdf8 0%, #1d4ed8 100%); color: white !important; font-weight: 700; border-radius: 10px; border: none; }
</style>
""", unsafe_allow_html=True)

init_db()

# ==========================================
# 4. הממשק המרכזי
# ==========================================
st.markdown("<h1 class='white-bold' style='text-align: center;'>EduCheck AI Pro 🎓</h1>", unsafe_allow_html=True)
st.markdown(f"<p style='text-align: center;'>שלום, מורה {st.session_state.teacher_id}</p>", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["📄 בדיקת מבחן", "📊 ארכיון אישי", "⚙️ הגדרות"])

if 'rubric' not in st.session_state:
    st.session_state.rubric = "בדוק את התשובות על פי הבנה עמוקה של החומר."

with tab1:
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        student_name = st.text_input("שם התלמיד:")
        subject = st.selectbox("מקצוע:", SUBJECTS_LIST)
        st.session_state.rubric = st.text_area("מחוון הבדיקה:", value=st.session_state.rubric, height=150)
    with col2:
        file = st.file_uploader("העלה מבחן:", type=['jpg', 'png', 'jpeg'])
        if st.button("🚀 בדוק מבחן"):
            if file and student_name:
                with st.spinner("בבדיקה..."):
                    model = init_gemini()
                    if model:
                        img = Image.open(file)
                        prompt = f"פענח בלב את המבחן של {student_name} במקצוע {subject} לפי המחוון: {st.session_state.rubric}. החזר רק ציון ומשוב בעברית."
                        response = model.generate_content([prompt, img])
                        save_to_db(student_name, subject, response.text)
                        st.markdown(response.text)
    st.markdown("</div>", unsafe_allow_html=True)

with tab2:
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    st.subheader("הארכיון שלך")
    filter_sub = st.selectbox("סנן:", ["הכל"] + SUBJECTS_LIST)
    df = load_from_db(filter_sub)
    if not df.empty:
        st.dataframe(df, use_container_width=True)
    else:
        st.info("אין נתונים להצגה כרגע.")
    st.markdown("</div>", unsafe_allow_html=True)

with tab3:
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    if st.button("🔓 התנתקות"):
        st.session_state.authenticated = False
        st.session_state.teacher_id = None
        st.rerun()
    st.markdown("---")
    if st.button("🔴 ניקוי הארכיון שלי"):
        conn = sqlite3.connect('results.db')
        conn.execute("DELETE FROM exams WHERE teacher_id = ?", (st.session_state.teacher_id,))
        conn.commit()
        conn.close()
        st.success("הארכיון שלך נוקה.")
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)
