import streamlit as st
import google.generativeai as genai
from PIL import Image
import pandas as pd
from datetime import datetime
import sqlite3

# ==========================================
# 0. מנגנון 100 סיסמאות
# ==========================================
PASSWORDS = [str(i) for i in range(1000, 10000)]

if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

def login_screen():
    st.markdown("<h2 style='text-align:center; color:white;'>כניסה למערכת EduCheck</h2>", unsafe_allow_html=True)
    pwd = st.text_input("הזן סיסמה:", type="password")
    if st.button("התחבר"):
        if pwd in PASSWORDS:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("סיסמה שגויה")

if not st.session_state.authenticated:
    login_screen()
    st.stop()

# רשימת מקצועות לבחירה
SUBJECTS_LIST = ["תורה", "נביא", "הלכה", "גמרא", "חשבון", "אנגלית", "שפה","כישורי חיים", "מחשבת ישראל", "היסטוריה", "מדעים", "אזרחות", "אחר"]

# ==========================================
# 1. בסיס נתונים (SQLite)
# ==========================================
def init_db():
   conn = sqlite3.connect('results.db',check_same_thread=False)
   c = conn.cursor()
   c.execute('''CREATE TABLE IF NOT EXISTS exams
               (id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT, student_name TEXT, subject TEXT, result TEXT)''')
   conn.commit()
   conn.close()

def save_to_db(name, subject, result):
   conn = sqlite3.connect('results.db',check_same_thread=False)
   c = conn.cursor()
   date_now = datetime.now().strftime("%d/%m/%Y %H:%M")
   c.execute("INSERT INTO exams (date, student_name, subject, result) VALUES (?, ?, ?, ?)",
            (date_now, name, subject, result))
   conn.commit()
   conn.close()

def load_from_db(subject_filter="הכל"):
   conn = sqlite3.connect('results.db',check_same_thread=False)
   if subject_filter == "הכל":
       df = pd.read_sql_query("SELECT date, student_name, subject, result FROM exams", conn)
   else:
       df = pd.read_sql_query(f"SELECT date, student_name, subject, result FROM exams WHERE subject = '{subject_filter}'", conn)
   conn.close()
   return df

# ==========================================
# 2. הגדרות AI (עם רשימת המודלים המדויקת שביקשת)
# ==========================================
def init_gemini():
   if "GEMINI_API_KEY" not in st.secrets:
       st.error("🔑מפתח API חסר ב-Secrets!")
       return None
  
   api_key = st.secrets["GEMINI_API_KEY"]
   if not api_key or len(api_key) < 20:
       st.error("🔑מפתח API לא תקין!")
       return None
  
   try:
       genai.configure(api_key=api_key)
       # רשימת המודלים בדיוק כפי שביקשת:
       model_names =[
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
      
       st.error(f"❌ שגיאה בחיבור למודלים: {last_error}")
       return None
      
   except Exception as e:
      st.error(f"❌ שגיאה כללית: {str(e)}")
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
  .stButton>button { background: linear-gradient(135deg, #38bdf8 0%, #1d4ed8 100%); color: white !important; font-weight: 700; border-radius: 10px; border: none; width: 100%; height: 3em; }
   label, p, .stMarkdown { color: white !important; font-weight: 600; }
   .stTabs [data-baseweb="tab"] { color: white !important; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

init_db()

# ==========================================
# 4. הממשק המרכזי
# ==========================================
st.markdown("<h1 class='white-bold' style='text-align: center;'>EduCheck AI Pro 🎓</h1>", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["📄 בדיקת מבחן", "📊 ארכיון ציונים", "⚙️הגדרות"])

if 'rubric' not in st.session_state:
   st.session_state.rubric ="בדוק את התשובות על פי הבנה עמוקה של החומר, דיוק בפרטים ושימוש במושגים נכונים."

with tab1:
   st.markdown("<div class='glass-card'>",unsafe_allow_html=True)
   col1, col2 = st.columns(2)
  
   with col1:
       student_name = st.text_input("שם התלמיד:")
       subject = st.selectbox("מקצוע:", SUBJECTS_LIST)
      
       rubric_file = st.file_uploader("העלה קובץ מחוון תשובות (אופציונלי):", type=['jpg', 'jpeg', 'png', 'pdf'])
       if rubric_file and st.button("🔍 פענח מחוון מהקובץ"):
           model = init_gemini()
           if model:
               with st.spinner("מפענח מחוון..."):
                   img_r = Image.open(rubric_file)
                   res_r = model.generate_content(["פענח את הטקסט מהקובץ והפוך אותו למחוון תשובות:", img_r])
                   st.session_state.rubric = res_r.text
                   st.success("המחוון עודכן!")

       if st.button("✨ צור מחוון אוטומטי"):
          model = init_gemini()
          if model:
              with st.spinner("מייצר מחוון..."):
                  res = model.generate_content(f"צור מחוון תשובות מפורט למבחן בנושא {subject} בעברית.")
                  st.session_state.rubric = res.text
                  st.success("✅ מחוון נוצר!")

       st.session_state.rubric = st.text_area("מחוון הבדיקה:", value=st.session_state.rubric, height=200)
  
   with col2:
       upload_method = st.radio("בחר שיטת העלאת מבחן:", ["העלאת קובץ", "צילום במצלמה"])
       if upload_method == "העלאת קובץ":
           file = st.file_uploader("העלה צילום מבחן (כתב יד):", type=['jpg', 'jpeg', 'png'])
       else:
           file = st.camera_input("צלם את המבחן:")
      
       if st.button("🚀בדוק מבחן"):
           if not file or not student_name:
               st.warning("נא להזין שם תלמיד ולהעלות קובץ.")
           else:
               with st.spinner(" בודק מבחן"):
                   try:
                       img = Image.open(file)
                       model = init_gemini()
                       if model:
                           # הפרומפט המעודכן שלא מציג את הטקסט המפוענח
                           prompt = f"""
                           משימה: פענח את כתב היד בתמונה עבור {student_name}, השווה למחוון וקבע ציון.
                           נושא: {subject}
                           מחוון: {st.session_state.rubric}
                           
                           הוראה חשובה: בצע את פענוח כתב היד בלב. אל תציג את הטקסט שזיהית למורה בתשובה הסופית.
                           השתמש בפענוח רק כדי לקבוע את התוצאות הבאות:
                           
                           ענה בעברית בפורמט הבא בלבד:
                           ## תוצאות עבור {student_name}
                           **ציון סופי:** [מספר]
                           **מה היה טוב:** [פירוט]
                           **נקודות לשיפור:** [פירוט]
                           """
                           
                           max_size = 2048
                           if img.size[0] > max_size or img.size[1] > max_size:
                               ratio = min(max_size/ img.size[0], max_size / img.size[1])
                               img = img.resize((int(img.size[0]* ratio),int(img.size[1]* ratio)), Image.Resampling.LANCZOS)
                          
                           response = model.generate_content([prompt, img])
                           save_to_db(student_name, subject, response.text)
                           st.success("הבדיקה הושלמה!")
                           st.markdown(response.text)
                   except Exception as e:
                       st.error(f"❌ שגיאה בניתוח: {e}")
   st.markdown("</div>", unsafe_allow_html=True)

with tab2:
   st.markdown("<div class='glass-card'>",unsafe_allow_html=True)
   filter_sub = st.selectbox("סנן לפי מקצוע:", ["הכל"] + SUBJECTS_LIST)
   df = load_from_db(filter_sub)
   if not df.empty:
       st.dataframe(df, use_container_width=True)
       st.download_button("📥 הורד אקסל (CSV)", data=df.to_csv(index=False).encode('utf-8-sig'), file_name="grades.csv")
   else:
       st.info("אין נתונים בארכיון.")
   st.markdown("</div>", unsafe_allow_html=True)

with tab3:
   st.markdown("<div class='glass-card'>",unsafe_allow_html=True)
   if st.button("🔓 התנתקות מהמערכת"):
       st.session_state.authenticated = False
       st.rerun()
   st.markdown("---")
   if st.button("🔴 מחיקת כל הארכיון"):
       conn = sqlite3.connect('results.db'); conn.execute("DELETE FROM exams"); conn.commit(); conn.close()
       st.success("הארכיון נמחק."); st.rerun()
   st.markdown("</div>", unsafe_allow_html=True)
