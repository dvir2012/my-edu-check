import streamlit as st
import google.generativeai as genai
from PIL import Image
import pandas as pd
from datetime import datetime
import sqlite3
import hashlib

# ==========================================
# 1. בסיס נתונים (SQLite)
# ==========================================
def init_db(user_id):
    conn = sqlite3.connect('results.db', check_same_thread=False)
    c = conn.cursor()
    table_name = f"user_{user_id}"
    c.execute(f'''CREATE TABLE IF NOT EXISTS {table_name}
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  date TEXT, student_name TEXT, subject TEXT, result TEXT)''')
    conn.commit()
    conn.close()

def save_to_db(user_id, name, subject, result):
    conn = sqlite3.connect('results.db', check_same_thread=False)
    c = conn.cursor()
    table_name = f"user_{user_id}"
    date_now = datetime.now().strftime("%d/%m/%Y %H:%M")
    c.execute(f"INSERT INTO {table_name} (date, student_name, subject, result) VALUES (?, ?, ?, ?)",
              (date_now, name, subject, result))
    conn.commit()
    conn.close()

def load_from_db(user_id):
    conn = sqlite3.connect('results.db', check_same_thread=False)
    table_name = f"user_{user_id}"
    try:
        df = pd.read_sql_query(f"SELECT date, student_name, subject, result FROM {table_name}", conn)
    except:
        df = pd.DataFrame(columns=['date', 'student_name', 'subject', 'result'])
    conn.close()
    return df

def generate_user_id(phone):
    clean_phone = phone.replace("-", "").replace(" ", "")
    return hashlib.md5(clean_phone.encode()).hexdigest()[:12]

# ==========================================
# 2. הגדרות AI
# ==========================================
def init_gemini():
    if "GEMINI_API_KEY" not in st.secrets:
        st.error("🔑 מפתח API חסר ב-Secrets!")
        return None
    api_key = st.secrets["GEMINI_API_KEY"]
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('models/gemini-2.0-flash')
        return model
    except Exception as e:
        st.error(f"❌ שגיאה בחיבור ל-AI: {str(e)}")
        return None

# ==========================================
# 3. עיצוב ו-CSS
# ==========================================
st.set_page_config(page_title="EduCheck AI Pro", page_icon="🎓", layout="wide")
st.markdown("""
<style>
   .stApp { background-color: #0f172a; color: white; direction: rtl; text-align: right; }
   .white-bold { color: #ffffff !important; font-weight: 900 !important; text-shadow: 2px 2px 4px #000000; }
   .glass-card { background: rgba(30, 41, 59, 0.7); border: 1px solid #38bdf8; border-radius: 15px; padding: 25px; margin-bottom: 20px; }
   .stButton>button { background: linear-gradient(135deg, #38bdf8 0%, #1d4ed8 100%); color: white !important; font-weight: 700; border-radius: 10px; border: none; width: 100%; height: 3.5em; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 4. מערכת כניסה
# ==========================================
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.user_id = ""
    st.session_state.display_phone = ""

if not st.session_state.authenticated:
    st.markdown("<h1 class='white-bold' style='text-align: center;'>EduCheck AI 🔒</h1>", unsafe_allow_html=True)
    with st.container():
        st.markdown("<div class='glass-card' style='max-width: 450px; margin: 0 auto;'>", unsafe_allow_html=True)
        phone_input = st.text_input("הזן מספר טלפון לכניסה לארכיון:", placeholder="05XXXXXXXX")
        if st.button("התחבר"):
            if len(phone_input) >= 9:
                st.session_state.user_id = generate_user_id(phone_input)
                st.session_state.display_phone = phone_input
                st.session_state.authenticated = True
                st.rerun()
            else: st.error("נא להזין מספר טלפון תקין")
        st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

current_user_id = st.session_state.user_id
init_db(current_user_id)

# ==========================================
# 5. ממשק ראשי
# ==========================================
st.markdown(f"<h1 class='white-bold' style='text-align: center;'>EduCheck AI Pro 🎓</h1>", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["📄 בדיקת מבחן", "📊 ארכיון חכם", "⚙️ הגדרות"])

SUBJECT_OPTIONS = ["תורה", "נביא", "דינים", "מדעים", "חשבון", "אנגלית", "עברית", "אחר..."]

with tab1:
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📝 פרטי המבחן")
        student_name = st.text_input("שם התלמיד:")
        selected_sub = st.selectbox("בחר מקצוע:", SUBJECT_OPTIONS)
        subject = st.text_input("ציין מקצוע אחר:") if selected_sub == "אחר..." else selected_sub
        
        st.markdown("---")
        st.subheader("📋 המחוון (תשובות נכונות)")
        rubric_text = st.text_area("הקלד מחוון:", placeholder="מה התשובות הנכונות במבחן?")
        rubric_file = st.file_uploader("או העלה דף מחוון (PDF/תמונה):", type=['pdf', 'jpg', 'png', 'jpeg'], key="rubric_file")

    with col2:
        st.subheader("📸 העלאת המבחן")
        mode = st.radio("איך תרצה להעלות את המבחן?", ["העלאת קובץ", "צילום במצלמה"])
        
        test_image = None
        if mode == "העלאת קובץ":
            test_image = st.file_uploader("בחר צילום מבחן:", type=['jpg', 'png', 'jpeg'], key="test_file")
        else:
            test_image = st.camera_input("צלם את המבחן:")

        if st.button("🚀 התחל בדיקה"):
            if test_image and student_name:
                with st.spinner("ה-AI מנתח ומדרג..."):
                    model = init_gemini()
                    if model:
                        img = Image.open(test_image)
                        
                        # הכנת המחוון ל-AI
                        rubric_context = rubric_text
                        if rubric_file:
                            rubric_context += " (שים לב למחוון המצורף בקובץ)"
                        
                        prompt = f"""
                        משימה: בדוק מבחן ב{subject} של התלמיד {student_name}.
                        מחוון בדיקה: {rubric_context}
                        ענה בעברית בפורמט ברור:
                        ## תוצאות עבור {student_name}
                        **ציון סופי:** [0-100]
                        **נקודות חוזקה:** [פירוט]
                        **טעויות לתיקון:** [פירוט]
                        **תוכן המבחן כפי שזוהה:** [פענוח הטקסט]
                        """
                        
                        content_list = [prompt, img]
                        if rubric_file and rubric_file.type != 'application/pdf':
                            content_list.append(Image.open(rubric_file))
                        
                        res = model.generate_content(content_list)
                        save_to_db(current_user_id, student_name, subject, res.text)
                        st.markdown(res.text)
            else: st.warning("נא למלא שם ולהעלות מבחן.")
    st.markdown("</div>", unsafe_allow_html=True)

with tab2:
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    st.subheader("🔎 סינון הארכיון")
    df = load_from_db(current_user_id)
    
    if not df.empty:
        subjects_in_db = ["הצג הכל"] + sorted(df['subject'].unique().tolist())
        filter_sub = st.selectbox("סנן לפי מקצוע שבדקת:", subjects_in_db)
        
        filtered_df = df if filter_sub == "הצג הכל" else df[df['subject'] == filter_sub]
        st.dataframe(filtered_df, use_container_width=True)
        
        csv = filtered_df.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 הורד נתונים מסוננים לאקסל", csv, f"grades_{filter_sub}.csv")
    else: st.info("אין נתונים בארכיון.")
    st.markdown("</div>", unsafe_allow_html=True)

with tab3:
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    st.subheader("⚙️ ניהול חשבון")
    st.info(f"מחובר כמורה: {st.session_state.display_phone}")
    
    if st.button("🚪 התנתק מהמערכת (Logout)"):
        st.session_state.authenticated = False
        st.session_state.user_id = ""
        st.rerun()
    
    st.markdown("---")
    st.error("⚠️ פעולות מסוכנות")
    confirm = st.checkbox("אני מאשר מחיקה מוחלטת של כל ההיסטוריה שלי.")
    if st.button("🔴 מחק ארכיון לצמיתות"):
        if confirm:
            conn = sqlite3.connect('results.db'); conn.execute(f"DELETE FROM user_{current_user_id}"); conn.commit(); conn.close()
            st.success("הארכיון נמחק."); st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)
