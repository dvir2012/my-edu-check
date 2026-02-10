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

# --- 2. עיצוב UI מתקדם ---
st.set_page_config(page_title="EduCheck Premium", layout="wide")

st.markdown("""
<style>
    /* רקע שקיעה חי */
    .stApp {
        background: linear-gradient(rgba(0,0,0,0.4), rgba(0,0,0,0.4)), 
                    url('https://images.unsplash.com/photo-1472214103451-9374bd1c798e?ixlib=rb-4.0.3&auto=format&fit=crop&w=1920&q=80');
        background-size: cover;
        background-attachment: fixed;
        direction: rtl;
        text-align: right;
    }

    /* כרטיסי זכוכית (Glassmorphism) */
    .glass-card {
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 25px;
        padding: 30px;
        color: white;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
        margin-bottom: 25px;
    }

    /* כותרות */
    h1, h2, h3, label, p {
        color: white !important;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }

    /* עיצוב טאבים */
    .stTabs [data-baseweb="tab-list"] {
        background: rgba(0, 0, 0, 0.2);
        padding: 10px;
        border-radius: 15px;
    }
    .stTabs [data-baseweb="tab"] {
        color: white !important;
        font-weight: bold;
    }

    /* כפתורי פרימיום */
    .stButton>button {
        background: linear-gradient(45deg, #ff512f, #dd2476);
        color: white;
        border: none;
        padding: 15px 30px;
        border-radius: 15px;
        font-weight: bold;
        font-size: 1.1rem;
        transition: 0.4s ease;
        box-shadow: 0 4px 15px rgba(221, 36, 118, 0.3);
    }
    .stButton>button:hover {
        transform: scale(1.03);
        box-shadow: 0 6px 20px rgba(221, 36, 118, 0.5);
    }

    /* תיבות קלט */
    .stTextInput input, .stTextArea textarea, .stSelectbox div {
        background: rgba(255, 255, 255, 0.9) !important;
        color: #2c3e50 !important;
        border-radius: 12px !important;
        border: none !important;
        font-weight: 500;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. ניהול מצב ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'reports' not in st.session_state: st.session_state.reports = []
if 'current_rubric' not in st.session_state: st.session_state.current_rubric = ""

# --- 4. מסך כניסה (Premium Login) ---
if not st.session_state.logged_in:
    st.markdown("<div style='height: 20vh;'></div>", unsafe_allow_html=True)
    c1, login_col, c3 = st.columns([1, 1.2, 1])
    with login_col:
        st.markdown("<div class='glass-card' style='text-align: center;'>", unsafe_allow_html=True)
        st.markdown("<h1>🌅 EduCheck Login</h1>", unsafe_allow_html=True)
        st.write("נא להזין את המילה הסודית")
        user_key = st.text_input("", type="password", placeholder="הכנס סיסמה...")
        if st.button("כניסה למערכת 🔑"):
            if user_key in ALLOWED_PASSWORDS:
                st.session_state.logged_in = True
                st.rerun()
            else: st.error("גישה נדחתה. נסה שוב.")
        st.markdown("</div>", unsafe_allow_html=True)

# --- 5. המערכת המרכזית ---
else:
    st.markdown("<h1 style='text-align: center; font-size: 3rem;'>EduCheck Premium 🎓</h1>", unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["🔍 ניהול בדיקה", "📊 ארכיון ציונים"])

    with tab1:
        # פריסה של 2 עמודות - מחוון ובדיקה
        col_side, col_main = st.columns([1, 1.8])
        
        with col_side:
            st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
            st.subheader("🪄 מחולל מחוון AI")
            rubric_img = st.file_uploader("העלאת שאלון", type=['png', 'jpg', 'jpeg'], key="rubric")
            chat_cmd = st.text_input("הוראה ל-Gemini:")
            if st.button("בנה/עדכן מחוון"):
                with st.spinner("יוצר..."):
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    res = model.generate_content([f"צור מחוון מקצועי: {chat_cmd}", Image.open(rubric_img) if rubric_img else ""])
                    st.session_state.current_rubric = res.text
            
            st.session_state.current_rubric = st.text_area("טיוטת מחוון:", value=st.session_state.current_rubric, height=200)
            st.markdown("</div>", unsafe_allow_html=True)

        with col_main:
            st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
            st.subheader("👤 פרטי התלמיד")
            c1, c2, c3 = st.columns(3)
            with c1: name = st.text_input("שם מלא:")
            with c2: grade = st.text_input("כיתה:")
            with c3: 
                subjects = ["תורה", "נביא", "גמרא", "משנה", "הלכה", "מדעים", "היסטוריה", "עברית/לשון", "אחר..."]
                subj = st.selectbox("מקצוע:", subjects)
            
            st.divider()
            st.subheader("📸 העלאת תשובות")
            exam_file = st.file_uploader("בחר קובץ מבחן", type=['png', 'jpg', 'jpeg'])
            cam_file = st.camera_input("או צלם")
            
            active = cam_file if cam_file else exam_file
            
            if st.button("🚀 בצע בדיקה וניתוח פדגוגי"):
                if active and name:
                    with st.spinner("ה-AI מנתח..."):
                        model = genai.GenerativeModel('gemini-1.5-flash')
                        prompt = f"נתח מבחן ב{subj} לתלמיד {name}. מחוון: {st.session_state.current_rubric}. תן ציון בולט ומשוב מפורט."
                        resp = model.generate_content([prompt, Image.open(active)])
                        txt = resp.text
                        score = "".join(filter(str.isdigit, txt[:30]))
                        
                        st.session_state.reports.append({
                            "שם": name, "מקצוע": subj, "כיתה": grade,
                            "ציון": score if score else "נבדק", "תאריך": datetime.now().strftime("%d/%m/%Y"), "דוח": txt
                        })
                        st.success("הבדיקה נשמרה בהצלחה!")
                        st.markdown(f"<div style='background:rgba(255,255,255,0.9); color:black; padding:20px; border-radius:15px;'>{txt}</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

    with tab2:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.subheader("📊 סינון וניהול ציונים")
        f_subj = st.selectbox("בחר מקצוע לצפייה:", ["הכל"] + subjects)
        
        data = st.session_state.reports
        if f_subj != "הכל":
            data = [r for r in data if r['מקצוע'] == f_subj]

        if data:
            for r in reversed(data):
                with st.expander(f"📔 {r['מקצוע']} | {r['שם']} | ציון: {r['ציון']}"):
                    st.write(f"תאריך: {r['תאריך']} | כיתה: {r['כיתה']}")
                    st.markdown(r['דוח'])
        else:
            st.info("אין דוחות להצגה.")
        st.markdown("</div>", unsafe_allow_html=True)

    if st.sidebar.button("🚪 Logout"):
        st.session_state.logged_in = False
        st.rerun()
