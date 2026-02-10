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

# --- 2. עיצוב "למידה חכמה" (Smart Learning UI) ---
st.set_page_config(page_title="EduCheck AI - Dashboard", layout="wide")

st.markdown("""
<style>
    /* רקע כללי של למידה */
    .stApp {
        background-color: #f0f2f6;
        background-image: radial-gradient(#d1d5db 1px, transparent 1px);
        background-size: 20px 20px; /* נראה כמו דף משובץ/נקודות */
        direction: rtl;
        text-align: right;
    }
    
    /* כותרת עליונה בסגנון האפליקציה */
    .main-header {
        background: linear-gradient(90deg, #4f46e5, #7c3aed);
        color: white;
        padding: 1.5rem;
        border-radius: 0 0 30px 30px;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        margin-bottom: 2rem;
    }

    /* כרטיסי מידע (Cards) */
    .info-card {
        background: white;
        border-radius: 20px;
        padding: 20px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.05);
        border: 1px solid #e5e7eb;
        margin-bottom: 20px;
    }

    /* עיצוב שדות קלט */
    .stTextInput input, .stTextArea textarea, .stSelectbox select {
        border-radius: 12px !important;
        border: 1px solid #d1d5db !important;
        padding: 10px !important;
    }

    /* כפתורים */
    .stButton>button {
        background: #4f46e5;
        color: white;
        border-radius: 12px;
        padding: 10px 24px;
        font-weight: 600;
        border: none;
        width: 100%;
        transition: 0.3s;
    }
    .stButton>button:hover {
        background: #4338ca;
        box-shadow: 0 5px 15px rgba(79, 70, 229, 0.4);
    }

    /* טאבים */
    .stTabs [data-baseweb="tab-list"] {
        gap: 20px;
        justify-content: center;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: white;
        border-radius: 10px 10px 0 0;
        padding: 10px 20px;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. ניהול מצב (Session State) ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'reports' not in st.session_state: st.session_state.reports = []
if 'current_rubric' not in st.session_state: st.session_state.current_rubric = ""

# --- 4. מסך כניסה ---
if not st.session_state.logged_in:
    st.markdown("<div style='height: 15vh;'></div>", unsafe_allow_html=True)
    cols = st.columns([1, 1.2, 1])
    with cols[1]:
        st.markdown("<div class='info-card' style='text-align: center;'>", unsafe_allow_html=True)
        st.image("https://cdn-icons-png.flaticon.com/512/3429/3429156.png", width=80)
        st.title("כניסת מורים")
        user_key = st.text_input("הזן מילה סודית:", type="password")
        if st.button("התחבר למערכת"):
            if user_key in ALLOWED_PASSWORDS:
                st.session_state.logged_in = True
                st.rerun()
            else: st.error("סיסמה שגויה")
        st.markdown("</div>", unsafe_allow_html=True)

# --- 5. המערכת המרכזית ---
else:
    st.markdown("<div class='main-header'><h1>EduCheck AI - Class Management 🎓</h1></div>", unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["📝 בדיקת מבחן", "📊 דוחות וציונים"])

    with tab1:
        col_main, col_side = st.columns([2, 1])
        
        with col_main:
            st.markdown("<div class='info-card'><h3>🔍 פרטי התלמיד והמבחן</h3>", unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            with c1:
                student_name = st.text_input("שם התלמיד:")
                grade_name = st.text_input("כיתה (למשל: ז'3):")
            with c2:
                subjects = ["תורה", "נביא", "גמרא", "משנה", "הלכה", "מדעים", "היסטוריה", "עברית/לשון", "אחר..."]
                subj = st.selectbox("מקצוע:", subjects)
                if subj == "אחר...": subj = st.text_input("פרט מקצוע:")
            
            st.divider()
            exam_img = st.file_uploader("העלה את המבחן", type=['png', 'jpg', 'jpeg'])
            cam_img = st.camera_input("צילום מהיר")
            st.markdown("</div>", unsafe_allow_html=True)

        with col_side:
            st.markdown("<div class='info-card'><h3>🪄 מחוון AI</h3>", unsafe_allow_html=True)
            rubric_img = st.file_uploader("צילום שאלון למחוון", type=['png', 'jpg', 'jpeg'])
            chat_cmd = st.text_input("בקשה ל-Gemini:")
            if st.button("בנה מחוון"):
                model = genai.GenerativeModel('gemini-1.5-flash')
                res = model.generate_content([f"צור מחוון לשיעור {subj}: {chat_cmd}", Image.open(rubric_img) if rubric_img else ""])
                st.session_state.current_rubric = res.text
            
            st.session_state.current_rubric = st.text_area("המחוון הפעיל:", value=st.session_state.current_rubric, height=150)
            st.markdown("</div>", unsafe_allow_html=True)

        if st.button("🚀 בצע בדיקה פדגוגית"):
            active = cam_img if cam_img else exam_img
            if active and student_name:
                with st.spinner("מנתח תוצאות..."):
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    prompt = f"נתח מבחן ב{subj} לתלמיד {student_name}. מחוון: {st.session_state.current_rubric}. החזר ציון מספרי מודגש בראש התשובה."
                    resp = model.generate_content([prompt, Image.open(active)])
                    
                    # חילוץ ציון
                    txt = resp.text
                    score = "".join(filter(str.isdigit, txt[:30]))
                    
                    st.session_state.reports.append({
                        "שם": student_name, "מקצוע": subj, "כיתה": grade_name,
                        "ציון": score if score else "--", "תאריך": datetime.now().strftime("%d/%m/%Y"), "דוח": txt
                    })
                    st.success("הבדיקה נשמרה!")
                    st.markdown(f"<div class='info-card' style='color:black;'>{txt}</div>", unsafe_allow_html=True)

    with tab2:
        st.markdown("<div class='info-card'><h3>📊 ארכיון ציונים</h3>", unsafe_allow_html=True)
        filter_subj = st.selectbox("סנן לפי מקצוע:", ["הכל"] + subjects)
        
        data = st.session_state.reports
        if filter_subj != "הכל":
            data = [r for r in data if r['מקצוע'] == filter_subj]

        if data:
            for r in reversed(data):
                with st.expander(f"📌 {r['מקצוע']} | {r['שם']} | כיתה {r['כיתה']} | ציון: {r['ציון']}"):
                    st.markdown(r['דוח'])
        else: st.info("אין דוחות להצגה")
        st.markdown("</div>", unsafe_allow_html=True)

    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()
