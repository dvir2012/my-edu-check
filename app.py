import streamlit as st
import google.generativeai as genai
from PIL import Image
import pandas as pd
from datetime import datetime
import sqlite3

# ==========================================
# 1. בסיס נתונים (SQLite) - מעודכן לתמיכה בטבלאות נפרדות
# ==========================================
def init_db(user_code):
    conn = sqlite3.connect('results.db', check_same_thread=False)
    c = conn.cursor()
    # יצירת טבלה ייחודית לכל קוד גישה
    table_name = f"exams_{user_code}"
    c.execute(f'''CREATE TABLE IF NOT EXISTS {table_name}
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  date TEXT, student_name TEXT, subject TEXT, result TEXT)''')
    conn.commit()
    conn.close()

def save_to_db(user_code, name, subject, result):
    conn = sqlite3.connect('results.db', check_same_thread=False)
    c = conn.cursor()
    table_name = f"exams_{user_code}"
    date_now = datetime.now().strftime("%d/%m/%Y %H:%M")
    c.execute(f"INSERT INTO {table_name} (date, student_name, subject, result) VALUES (?, ?, ?, ?)",
              (date_now, name, subject, result))
    conn.commit()
    conn.close()

def load_from_db(user_code):
    conn = sqlite3.connect('results.db', check_same_thread=False)
    table_name = f"exams_{user_code}"
    try:
        df = pd.read_sql_query(f"SELECT date, student_name, subject, result FROM {table_name}", conn)
    except:
        df = pd.DataFrame(columns=['date', 'student_name', 'subject', 'result'])
    conn.close()
    return df

# ==========================================
# 2. הגדרות AI (תיקון שגיאת 404)
# ==========================================
def init_gemini():
    if "GEMINI_API_KEY" not in st.secrets:
        st.error("🔑 מפתח API חסר ב-Secrets! אנא הוסף אותו בלוח הבקרה של Streamlit.")
        return None
  
    api_key = st.secrets["GEMINI_API_KEY"]
  
    if not api_key or api_key == "הכנס_כאן_את_מפתח_ה_API_שלך" or len(api_key) < 20:
        st.error("🔑 מפתח API לא תקין! אנא ודא שהכנסת מפתח תקין בקובץ .streamlit/secrets.toml")
        st.info("💡 קבל מפתח מ: https://aistudio.google.com/")
        return None
  
    try:
        genai.configure(api_key=api_key)
      
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
                # בדיקה מהירה אם המודל זמין
                return model
            except Exception as e:
                last_error = e
                continue
      
        error_msg = str(last_error) if last_error else "שגיאה לא ידועה"
        st.error(f"❌ שגיאה בחיבור למודלים: {error_msg}")
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
   .stTabs [data-baseweb="tab"] { color: white !important; font-weight: bold; }
   input { background-color: #1e293b !important; color: white !important; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 4. מנגנון כניסה וקודי גישה
# ==========================================

# יצירת רשימה של 100 קודים (Edu1, Edu2 ... Edu100)
VALID_CODES = [f"Edu{i}" for i in range(1, 101)]

if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.user_code = ""

if not st.session_state.authenticated:
    st.markdown("<h1 class='white-bold' style='text-align: center;'>כניסה למערכת EduCheck 🔒</h1>", unsafe_allow_html=True)
    with st.container():
        st.markdown("<div class='glass-card' style='max-width: 400px; margin: 0 auto;'>", unsafe_allow_html=True)
        input_code = st.text_input("הכנס קוד גישה אישי:", type="password")
        if st.button("כניסה"):
            if input_code in VALID_CODES:
                st.session_state.authenticated = True
                st.session_state.user_code = input_code
                st.rerun()
            else:
                st.error("קוד גישה שגוי. נסה שוב.")
        st.markdown("</div>", unsafe_allow_html=True)
    st.stop() # עוצר את הרצת שאר הקוד עד להתחברות

# אתחול מסד הנתונים עבור המשתמש הספציפי
current_user = st.session_state.user_code
init_db(current_user)

# ==========================================
# 5. הממשק המרכזי (רק למחוברים)
# ==========================================
st.markdown(f"<h1 class='white-bold' style='text-align: center;'>EduCheck AI Pro 🎓</h1>", unsafe_allow_html=True)
st.sidebar.markdown(f"👤 מחובר כעת: **{current_user}**")
if st.sidebar.button("התנתק"):
    st.session_state.authenticated = False
    st.rerun()

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
                       res = model.generate_content(f"צור מחוון תשובות מפורט למבחן בנושא {subject} בעברית.")
                       if not res or not res.text:
                           st.error("❌ לא התקבלה תשובה מה-AI. נסה שוב.")
                       else:
                           st.session_state.rubric = res.text
                           st.success("✅ מחוון נוצר בהצלחה!")
                   except Exception as e:
                       st.error(f"❌ שגיאה ביצירת מחוון: {str(e)}")

       st.session_state.rubric = st.text_area("מחוון הבדיקה (תשובות נכונות):", value=st.session_state.rubric, height=200)
  
   with col2:
       file = st.file_uploader("העלה צילום מבחן (כתב יד):", type=['jpg', 'jpeg', 'png'])
      
       if st.button("🚀 בדוק מבחן"):
           if not file or not student_name:
               st.warning("נא להזין שם תלמיד ולהעלות קובץ.")
           else:
               with st.spinner("מפענח כתב יד ומנתח תוצאות..."):
                   try:
                       img = Image.open(file)
                       model = init_gemini()
                      
                       if model:
                           prompt = f"""
                           משימה: פענוח כתב יד עברי ובדיקת מבחן עבור התלמיד {student_name}.
                           נושא המבחן: {subject}
                           מחוון תשובות: {st.session_state.rubric}
                          
                           ענה בעברית בפורמט הבא:
                           ## תוצאות עבור {student_name}
                           **ציון סופי:** [מספר]
                           **מה היה טוב:** [פירוט]
                           **נקודות לשיפור:** [פירוט]
                           **הטקסט שזוהה מהמבחן:** [הצג את תוכן התשובות]
                           """
                          
                           max_size = 2048
                           if img.size[0] > max_size or img.size[1] > max_size:
                               ratio = min(max_size / img.size[0], max_size / img.size[1])
                               img = img.resize((int(img.size[0] * ratio), int(img.size[1] * ratio)), Image.Resampling.LANCZOS)
                          
                           response = model.generate_content([prompt, img])
                          
                           if not response or not response.text:
                               st.error("❌ לא התקבלה תשובה מה-AI.")
                           else:
                               save_to_db(current_user, student_name, subject, response.text)
                               st.success("הניתוח הושלם!")
                               st.markdown("---")
                               st.markdown(response.text)
                   except Exception as e:
                       st.error(f"❌ שגיאה בניתוח המבחן: {str(e)}")
   st.markdown("</div>", unsafe_allow_html=True)

with tab2:
   st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
   st.subheader(f"ארכיון אישי - קוד {current_user}")
   df = load_from_db(current_user)
   if not df.empty:
       st.dataframe(df, use_container_width=True)
       csv = df.to_csv(index=False).encode('utf-8-sig')
       st.download_button("📥 הורד אקסל (CSV)", data=csv, file_name=f"grades_{current_user}.csv")
   else:
       st.info("הארכיון שלך ריק עדיין.")
   st.markdown("</div>", unsafe_allow_html=True)

with tab3:
   st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
   if st.button("🔴 מחיקת הארכיון האישי שלי"):
       conn = sqlite3.connect('results.db')
       table_name = f"exams_{current_user}"
       conn.execute(f"DELETE FROM {table_name}")
       conn.commit()
       conn.close()
       st.success("הארכיון האישי נמחק.")
       st.rerun()
   st.markdown("</div>", unsafe_allow_html=True)
