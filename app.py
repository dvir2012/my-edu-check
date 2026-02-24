import streamlit as st
import google.generativeai as genai
from PIL import Image
import pandas as pd
from datetime import datetime
import sqlite3
import hashlib

# ==========================================
# 1. בסיס נתונים (SQLite) - מופרד לפי משתמש
# ==========================================
def init_db(user_id):
    conn = sqlite3.connect('results.db', check_same_thread=False)
    c = conn.cursor()
    # יצירת טבלה ייחודית לכל מורה
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
    # הופך את הטלפון למזהה ייחודי קצר ומוצפן
    clean_phone = phone.replace("-", "").replace(" ", "")
    return hashlib.md5(clean_phone.encode()).hexdigest()[:12]

# ==========================================
# 2. הגדרות AI (שמות המודלים נשמרו בדיוק כפי שביקשת)
# ==========================================
def init_gemini():
    if "GEMINI_API_KEY" not in st.secrets:
        st.error("🔑 מפתח API חסר ב-Secrets!")
        return None
    
    api_key = st.secrets["GEMINI_API_KEY"]
    if not api_key or len(api_key) < 20:
        st.error("🔑 מפתח API לא תקין!")
        return None

    try:
        genai.configure(api_key=api_key)
        
        # רשימת המודלים המקורית שלך - לא שונה דבר
        model_names = [
            'models/gemini-2.5-flash',
            'models/gemini-2.5-pro',
            'models/gemini-2.0-flash',
            'models/gemini-2.0-flash-001',
        ]
        
        last_error = None
        for model_name in model_names:
            try:
                model = genai.GenerativeModel(model_name)
                return model
            except Exception as e:
                last_error = e
                continue
        
        st.error(f"❌ שגיאה בחיבור למודלים: {str(last_error)}")
        return None
    except Exception as e:
        st.error(f"❌ שגיאה כללית: {str(e)}")
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
   input { background-color: #1e293b !important; color: white !important; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 4. מערכת כניסה מאובטחת
# ==========================================
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.user_id = ""

if not st.session_state.authenticated:
    st.markdown("<h1 class='white-bold' style='text-align: center;'>EduCheck AI 🔒</h1>", unsafe_allow_html=True)
    with st.container():
        st.markdown("<div class='glass-card' style='max-width: 450px; margin: 0 auto;'>", unsafe_allow_html=True)
        phone_input = st.text_input("הזן מספר טלפון לכניסה לארכיון האישי שלך:", placeholder="05XXXXXXXX")
        if st.button("התחבר"):
            if len(phone_input) >= 9:
                st.session_state.user_id = generate_user_id(phone_input)
                st.session_state.authenticated = True
                st.rerun()
            else: st.error("נא להזין מספר טלפון תקין")
        st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# אתחול ה-DB למשתמש הספציפי
current_user = st.session_state.user_id
init_db(current_user)

# ==========================================
# 5. הממשק המרכזי
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
        
        # בחירת מקצוע בבדיקת מבחן
        common_subjects = ["תורה", "נביא", "גמרא", "הלכה", "מתמטיקה", "אחר..."]
        subject_choice = st.selectbox("בחר מקצוע:", common_subjects)
        if subject_choice == "אחר...":
            subject = st.text_input("הזן שם מקצוע חדש:")
        else:
            subject = subject_choice
        
        if st.button("✨ צור מחוון אוטומטי"):
            model = init_gemini()
            if model:
                with st.spinner("מייצר מחוון..."):
                    try:
                        res = model.generate_content(f"צור מחוון תשובות מפורט למבחן בנושא {subject} בעברית.")
                        st.session_state.rubric = res.text
                        st.success("✅ מחוון נוצר בהצלחה!")
                    except Exception as e:
                        st.error(f"שגיאה: {str(e)}")

        st.session_state.rubric = st.text_area("מחוון הבדיקה:", value=st.session_state.rubric, height=200)

    with col2:
        file = st.file_uploader("העלה צילום מבחן (כתב יד):", type=['jpg', 'jpeg', 'png'])
        
        if st.button("🚀 בדוק מבחן"):
            if not file or not student_name or not subject:
                st.warning("נא להזין שם תלמיד, מקצוע ולהעלות קובץ.")
            else:
                with st.spinner("מפענח ומנתח..."):
                    try:
                        img = Image.open(file)
                        model = init_gemini()
                        if model:
                            prompt = f"""
                            משימה: פענוח כתב יד עברי ובדיקת מבחן עבור {student_name}.
                            נושא: {subject}
                            מחוון: {st.session_state.rubric}
                            ענה בעברית: ## תוצאות עבור {student_name}, **ציון סופי**, **מה היה טוב**, **נקודות לשיפור**, **הטקסט שזוהה**.
                            """
                            response = model.generate_content([prompt, img])
                            save_to_db(current_user, student_name, subject, response.text)
                            st.markdown(response.text)
                    except Exception as e:
                        st.error(f"שגיאה בניתוח: {str(e)}")
    st.markdown("</div>", unsafe_allow_html=True)

with tab2:
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    df = load_from_db(current_user)
    if not df.empty:
        # בחירת מקצוע בארכיון (סינון)
        unique_subjects = ["הכל"] + list(df['subject'].unique())
        selected_subject = st.selectbox("סנן לפי מקצוע:", unique_subjects)
        
        if selected_subject != "הכל":
            filtered_df = df[df['subject'] == selected_subject]
        else:
            filtered_df = df
            
        st.dataframe(filtered_df, use_container_width=True)
        csv = filtered_df.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 הורד אקסל (CSV)", data=csv, file_name=f"grades_{selected_subject}_{current_user}.csv")
    else:
        st.info("אין נתונים בארכיון האישי שלך.")
    st.markdown("</div>", unsafe_allow_html=True)

with tab3:
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    st.subheader("ניהול חשבון")
    
    # כפתור התנתקות בתוך הגדרות
    if st.button("🚪 התנתק מהמערכת"):
        st.session_state.authenticated = False
        st.session_state.user_id = ""
        st.rerun()
    
    st.markdown("---")
    if st.button("🔴 מחיקת הארכיון האישי שלי"):
        conn = sqlite3.connect('results.db')
        conn.execute(f"DROP TABLE IF EXISTS user_{current_user}")
        conn.commit()
        conn.close()
        st.success("הארכיון שלך נמחק לצמיתות.")
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)
