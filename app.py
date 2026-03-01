import streamlit as st
import google.generativeai as genai
from PIL import Image
import pandas as pd
from datetime import datetime
import sqlite3
import time
import re

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
# 1. בסיס נתונים (כולל עמודת ציון למעקב)
# ==========================================
def init_db():
    conn = sqlite3.connect('results.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS exams
                (id INTEGER PRIMARY KEY AUTOINCREMENT,
                 teacher_id TEXT,
                 date TEXT, student_name TEXT, subject TEXT, result TEXT, grade INTEGER)''')
    
    c.execute("PRAGMA table_info(exams)")
    columns = [column[1] for column in c.fetchall()]
    if 'teacher_id' not in columns:
        try: c.execute("ALTER TABLE exams ADD COLUMN teacher_id TEXT")
        except: pass
    if 'grade' not in columns:
        try: c.execute("ALTER TABLE exams ADD COLUMN grade INTEGER")
        except: pass
    conn.commit()
    conn.close()

def save_to_db(name, subject, result, grade):
    conn = sqlite3.connect('results.db', check_same_thread=False)
    c = conn.cursor()
    date_now = datetime.now().strftime("%d/%m/%Y %H:%M")
    c.execute("INSERT INTO exams (teacher_id, date, student_name, subject, result, grade) VALUES (?, ?, ?, ?, ?, ?)",
            (st.session_state.teacher_id, date_now, name, subject, result, grade))
    conn.commit()
    conn.close()

def load_from_db(subject_filter="הכל"):
    conn = sqlite3.connect('results.db', check_same_thread=False)
    tid = st.session_state.teacher_id
    try:
        if subject_filter == "הכל":
            query = "SELECT date, student_name, subject, grade, result FROM exams WHERE teacher_id = ?"
            df = pd.read_sql_query(query, conn, params=(tid,))
        else:
            query = "SELECT date, student_name, subject, grade, result FROM exams WHERE teacher_id = ? AND subject = ?"
            df = pd.read_sql_query(query, conn, params=(tid, subject_filter))
    except:
        df = pd.DataFrame(columns=['date', 'student_name', 'subject', 'grade', 'result'])
    conn.close()
    return df

# ==========================================
# 2. הגדרות AI - רשימת המודלים המדויקת שלך
# ==========================================
def get_available_models():
    """רשימת המודלים המקורית שלך"""
    return [
        'models/gemini-2.0-flash-001',    # Specific version - more likely to work
        'models/gemini-2.5-flash',        # Newer Flash model
        'models/gemini-2.5-pro',          # Pro model (limited free tier)
        'models/gemini-pro',               # Fallback
        'models/gemini-1.5-pro'            # Another fallback
    ]

def generate_content_with_fallback(prompt, image=None):
    model_names = get_available_models()
    generation_config = {"temperature": 0.0, "top_p": 1, "top_k": 1, "max_output_tokens": 2048}
    last_error = None
    for model_name in model_names:
        try:
            model = genai.GenerativeModel(model_name=model_name, generation_config=generation_config)
            content = [prompt, image] if image else prompt
            return model.generate_content(content)
        except Exception as e:
            last_error = e
            continue
    if last_error: raise last_error
    raise Exception("No models available")

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
    [data-testid="stMetricValue"] { color: #38bdf8 !important; font-size: 40px !important; }
</style>
""", unsafe_allow_html=True)

init_db()

# ==========================================
# 4. הממשק המרכזי
# ==========================================
st.markdown("<h1 class='white-bold' style='text-align: center;'>EduCheck AI Pro 🎓</h1>", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["📄 בדיקת מבחן", "📊 ארכיון אישי", "⚙️ הגדרות"])

if 'rubric' not in st.session_state:
    st.session_state.rubric = "בדוק את התשובות על פי הבנה עמוקה של החומר ודיוק בפרטים."

with tab1:
    # שימוש ב-Columns לשיפור ה-UX
    col_input, col_preview = st.columns([1, 1])
    
    with col_input:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        student_name = st.text_input("שם התלמיד:")
        subject = st.selectbox("מקצוע:", SUBJECTS_LIST)
        st.session_state.rubric = st.text_area("מחוון הבדיקה:", value=st.session_state.rubric, height=100)
        
        upload_method = st.radio("שיטת העלאה:", ["קובץ", "מצלמה"], horizontal=True)
        file = st.file_uploader("העלה מבחן:", type=['jpg', 'jpeg', 'png']) if upload_method == "קובץ" else st.camera_input("צלם מבחן")
        st.markdown("</div>", unsafe_allow_html=True)

    with col_preview:
        if file:
            st.image(file, caption="תצוגת המבחן", use_container_width=True)
        else:
            st.info("כאן תופיע תצוגה מקדימה של המבחן")

    if st.button("🚀 בדוק מבחן"):
        if not file or not student_name:
            st.warning("נא למלא שם תלמיד ולהעלות קובץ.")
        else:
            try:
                with st.spinner("המורה הדיגיטלי בודק את המבחן..."):
                    img = Image.open(file)
                    img.thumbnail((1600, 1600))
                    
                    # Prompt משופר פדגוגית
                    prompt = f"""
                    אתה מורה מומחה בעל ניסיון רב. תפקידך לפענח ולבדוק את המבחן של {student_name} ב{subject}.
                    השתמש במחוון: {st.session_state.rubric}
                    
                    הוראות:
                    1. פענח את הטקסט מהתמונה בזהירות.
                    2. חשב ציון סופי (0-100) על סמך המחוון.
                    
                    פורמט תשובה (חובה):
                    GRADE: [הציון במספר]
                    ## תוצאות עבור {student_name}
                    **ציון סופי:** [מספר]
                    **מה היה טוב:** [פירוט]
                    **נקודות לשיפור:** [פירוט]
                    """
                    
                    response = generate_content_with_fallback(prompt, img)
                    
                    if response and response.text:
                        full_res = response.text
                        # חילוץ ציון להצגה ב-Metric
                        grade_match = re.search(r"GRADE:\s*(\d+)", full_res)
                        grade_val = grade_match.group(1) if grade_match else "N/A"
                        clean_text = full_res.replace(f"GRADE: {grade_val}", "").strip()
                        
                        save_to_db(student_name, subject, clean_text, int(grade_val) if grade_val.isdigit() else 0)
                        
                        st.markdown("---")
                        res_col1, res_col2 = st.columns([1, 2])
                        with res_col1:
                            st.metric(label="ציון סופי", value=f"{grade_val}/100")
                        with res_col2:
                            st.markdown(clean_text)
            except Exception as e:
                st.error(f"שגיאה: {str(e)}")

with tab2:
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    st.subheader(f"ארכיון אישי - מורה {st.session_state.teacher_id}")
    df = load_from_db(st.selectbox("סנן לפי מקצוע:", ["הכל"] + SUBJECTS_LIST, key="arch_filter"))
    if not df.empty:
        st.dataframe(df, use_container_width=True)
        st.download_button("📥 הורד אקסל", data=df.to_csv(index=False).encode('utf-8-sig'), file_name=f"grades_{st.session_state.teacher_id}.csv")
    st.markdown("</div>", unsafe_allow_html=True)

with tab3:
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    if st.button("🔓 התנתקות"):
        st.session_state.authenticated = False
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)
