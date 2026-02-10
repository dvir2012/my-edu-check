import streamlit as st
import google.generativeai as genai
from PIL import Image
import pandas as pd
from datetime import datetime

# --- 1. הגדרות אבטחה ו-API ---
MY_API_KEY = "AIzaSyDJdiYe4VmudGKFQzoCI_MmngD26D4wm1Q" 
ALLOWED_PASSWORDS = [
    "dvir2012", "Teacher2012", "Sunset2012", "מורה2012", "Dvir_2012!",
    "2012EduCheck", "D2012V", "D@2012", "Dvir2012Pro", "Gold2012"
]
genai.configure(api_key=MY_API_KEY)

# --- 2. עיצוב שקיעה עמוקה ---
st.set_page_config(page_title="EduCheck Class Management", layout="wide")

st.markdown(f"""
<style>
    [data-testid="stAppViewContainer"] {{
        background: linear-gradient(180deg, #42275a 0%, #734b6d 50%, #ba5370 100%);
        direction: rtl; text-align: right;
    }}
    .glass-card {{
        background: rgba(255, 255, 255, 0.12);
        backdrop-filter: blur(15px);
        border-radius: 20px; padding: 25px; border: 1px solid rgba(255, 255, 255, 0.2);
        margin-bottom: 20px; color: white;
    }}
    h1, h2, h3, label, .stMarkdown {{ color: #ffffff !important; }}
    .stTextArea textarea, .stTextInput input, .stSelectbox select {{
        background-color: rgba(255, 255, 255, 0.95) !important;
        color: #1e293b !important; border-radius: 10px !important;
    }}
    .stButton>button {{
        background: linear-gradient(90deg, #ff512f 0%, #dd2476 100%);
        color: white; border: none; padding: 12px 25px; border-radius: 12px; font-weight: 700; width: 100%;
    }}
</style>
""", unsafe_allow_html=True)

# --- 3. ניהול מצב (Session State) ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'reports' not in st.session_state: st.session_state.reports = []
if 'current_rubric' not in st.session_state: st.session_state.current_rubric = ""

# --- 4. מסך כניסה ---
if not st.session_state.logged_in:
    st.markdown("<div style='height: 20vh;'></div>", unsafe_allow_html=True)
    cols = st.columns([1, 1.5, 1])
    with cols[1]:
        st.markdown("<div class='glass-card' style='text-align: center;'>", unsafe_allow_html=True)
        st.title("🌅 כניסת מורים")
        user_key = st.text_input("מילה סודית:", type="password")
        if st.button("כניסה למערכת 🔑"):
            if user_key in ALLOWED_PASSWORDS:
                st.session_state.logged_in = True
                st.rerun()
            else: st.error("סיסמה שגויה.")
        st.markdown("</div>", unsafe_allow_html=True)

# --- 5. המערכת המרכזית ---
else:
    st.title("EduCheck AI - ניהול פדגוגי כיתתי 🎓")
    
    tab1, tab2 = st.tabs(["🔍 בדיקה חדשה", "📊 ארכיון ודוחות"])

    with tab1:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📋 פרטי השיעור והכיתה")
            # בחירת מקצוע
            subject_list = ["תורה", "נביא", "גמרא", "משנה", "הלכה", "מדעים", "היסטוריה", "עברית/לשון", "אחר..."]
            subject = st.selectbox("בחר מקצוע:", subject_list)
            if subject == "אחר...":
                subject = st.text_input("כתוב את שם המקצוע:")
            
            grade_level = st.text_input("איזו כיתה? (למשל: ח'2):")
            num_students = st.number_input("כמות תלמידים בכיתה:", min_value=1, value=30)
            student_name = st.text_input("שם התלמיד הנבדק:")

        with col2:
            st.subheader("🪄 יצירת מחוון")
            rubric_file = st.file_uploader("העלה צילום שאלון (אופציונלי)", type=['png', 'jpg', 'jpeg'])
            chat_input = st.text_input("צ'אט עם Gemini לשיפור המחוון:")
            if st.button("עדכן מחוון 💬"):
                model = genai.GenerativeModel('gemini-1.5-flash')
                prompt = f"צור או עדכן מחוון למקצוע {subject}. בקשה: {chat_input}"
                res = model.generate_content([prompt, Image.open(rubric_file) if rubric_file else ""])
                st.session_state.current_rubric = res.text
            
            final_rubric = st.text_area("מחוון סופי:", value=st.session_state.current_rubric, height=100)

        st.divider()
        st.subheader("📸 בדיקת התשובות")
        exam_img = st.file_uploader("העלה את המבחן", type=['png', 'jpg', 'jpeg'], key="exam")
        cam_img = st.camera_input("או צלם")
        
        active_img = cam_img if cam_img else exam_img

        if st.button("בדוק ושמור דוח 🚀") and active_img and student_name:
            with st.spinner("מנתח..."):
                model = genai.GenerativeModel('gemini-1.5-flash')
                prompt = f"נתח מבחן ב{subject} עבור {student_name} מכיתה {grade_level}. השתמש במחוון: {final_rubric}. תן ציון מספרי מודגש ומשוב."
                response = model.generate_content([prompt, Image.open(active_img)])
                output = response.text
                
                # חילוץ ציון פשוט (חיפוש מספר)
                score = "".join(filter(str.isdigit, output[:20])) # לוקח מספר מהתחלה
                
                st.session_state.reports.append({
                    "שם": student_name,
                    "מקצוע": subject,
                    "כיתה": grade_level,
                    "ציון": score if score else "נבדק",
                    "תאריך": datetime.now().strftime("%d/%m/%Y"),
                    "דוח": output
                })
                st.success("הבדיקה נשמרה בארכיון!")
                st.markdown(f"<div style='background: white; color: black; padding: 20px; border-radius: 12px;'>{output}</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with tab2:
        st.subheader("🔎 סינון דוחות לפי מקצוע")
        filter_subject = st.selectbox("בחר מקצוע לצפייה:", ["הכל"] + subject_list)
        
        filtered_data = st.session_state.reports
        if filter_subject != "הכל":
            filtered_data = [r for r in st.session_state.reports if r['מקצוע'] == filter_subject]

        if filtered_data:
            for r in reversed(filtered_data):
                with st.expander(f"📘 {r['מקצוע']} | {r['שם']} | ציון: {r['ציון']} | {r['תאריך']}"):
                    st.write(f"**כיתה:** {r['כיתה']}")
                    st.markdown(r['דוח'])
            
            df = pd.DataFrame(filtered_data)
            st.download_button("📥 הורד נתוני מקצוע זה לאקסל", df.to_csv(index=False).encode('utf-8-sig'), "report.csv")
        else:
            st.info("לא נמצאו דוחות למקצוע הנבחר.")

    if st.sidebar.button("🚪 יציאה"):
        st.session_state.logged_in = False
        st.rerun()
