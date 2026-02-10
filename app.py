import streamlit as st
import google.generativeai as genai
from PIL import Image
import pandas as pd
from datetime import datetime

# --- 1. הגדרות API וסיסמאות ---
MY_API_KEY = "AIzaSyDJdiYe4VmudGKFQzoCI_MmngD26D4wm1Q" 
ALLOWED_PASSWORDS = [
    "dvir2012", "Teacher2012", "Sunset2012", "מורה2012", "Dvir_2012!",
    "2012EduCheck", "D2012V", "D@2012", "Dvir2012Pro", "Gold2012"
]
genai.configure(api_key=MY_API_KEY)

# --- 2. עיצוב Modern Tech UI ---
st.set_page_config(page_title="EduCheck AI", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Segoe+UI:wght@400;600;700&display=swap');

    /* רקע מודרני - אפור הייטק בהיר */
    .stApp {
        background-color: #f4f7f9;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        direction: rtl;
        text-align: right;
    }

    /* כרטיס מודרני לבן ונקי */
    .modern-card {
        background: #ffffff;
        border-radius: 12px;
        padding: 24px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
        border: 1px solid #e1e8ed;
        margin-bottom: 20px;
    }

    /* כותרת EduCheck AI */
    .app-title {
        color: #1a202c;
        font-weight: 700;
        font-size: 2.5rem;
        margin-bottom: 10px;
        text-align: center;
    }

    /* כפתורי פעולה מודרניים */
    .stButton>button {
        background-color: #3182ce;
        color: white !important;
        border-radius: 8px;
        border: none;
        padding: 10px 24px;
        font-weight: 600;
        width: 100%;
        transition: background 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #2b6cb0;
        box-shadow: 0 4px 12px rgba(49, 130, 206, 0.2);
    }

    /* עיצוב טאבים */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #edf2f7;
        padding: 6px;
        border-radius: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 45px;
        background-color: transparent;
        border-radius: 8px;
        color: #4a5568 !important;
        font-weight: 600;
    }
    .stTabs [data-baseweb="tab"]:hover {
        background-color: #ffffff;
    }

    /* תיבות קלט */
    .stTextInput input, .stSelectbox div, .stTextArea textarea {
        border-radius: 8px !important;
        border: 1px solid #e2e8f0 !important;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. ניהול Session State ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'reports' not in st.session_state: st.session_state.reports = []
if 'current_rubric' not in st.session_state: st.session_state.current_rubric = ""

# --- 4. מסך כניסה מודרני ---
if not st.session_state.logged_in:
    st.markdown("<div style='height: 20vh;'></div>", unsafe_allow_html=True)
    _, login_col, _ = st.columns([1, 1, 1])
    with login_col:
        st.markdown("<div class='modern-card'>", unsafe_allow_html=True)
        st.markdown("<h1 class='app-title'>EduCheck AI</h1>", unsafe_allow_html=True)
        st.write("<p style='text-align:center; color:#718096;'>מערכת חכמה לניהול ובדיקת מבחנים</p>", unsafe_allow_html=True)
        user_key = st.text_input("קוד גישה:", type="password", placeholder="הכנס סיסמה...")
        if st.button("כניסה למערכת"):
            if user_key in ALLOWED_PASSWORDS:
                st.session_state.logged_in = True
                st.rerun()
            else: st.error("סיסמה שגויה")
        st.markdown("</div>", unsafe_allow_html=True)

# --- 5. ממשק המערכת הראשי ---
else:
    st.markdown("<h1 class='app-title'>EduCheck AI</h1>", unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["🔍 ניתוח מבחן", "📊 דוחות וציונים"])

    with tab1:
        col_m, col_s = st.columns([2, 1])
        
        with col_m:
            st.markdown("<div class='modern-card'>", unsafe_allow_html=True)
            st.subheader("פרטי התלמיד")
            r1, r2, r3 = st.columns(3)
            with r1: name = st.text_input("שם מלא:")
            with r2: grade = st.text_input("כיתה:")
            with r3: 
                subs = ["תורה", "נביא", "גמרא", "משנה", "הלכה", "מדעים", "היסטוריה", "עברית/לשון", "אחר..."]
                subj = st.selectbox("מקצוע:", subs)
            
            st.divider()
            exam_file = st.file_uploader("העלה צילום מבחן", type=['png', 'jpg', 'jpeg'])
            cam_shot = st.camera_input("צילום מהיר")
            st.markdown("</div>", unsafe_allow_html=True)

        with col_s:
            st.markdown("<div class='modern-card'>", unsafe_allow_html=True)
            st.subheader("מחוון AI")
            rubric_f = st.file_uploader("העלה שאלון", type=['png', 'jpg', 'jpeg'])
            chat_cmd = st.text_input("הנחיה לתיקון המחוון:")
            if st.button("עדכן מחוון"):
                with st.spinner("יוצר..."):
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    res = model.generate_content([f"בנה מחוון ל{subj}: {chat_cmd}", Image.open(rubric_f) if rubric_f else ""])
                    st.session_state.current_rubric = res.text
            st.session_state.current_rubric = st.text_area("טקסט המחוון:", value=st.session_state.current_rubric, height=180)
            st.markdown("</div>", unsafe_allow_html=True)

        if st.button("🚀 הרץ בדיקה חכמה"):
            active = cam_shot if cam_shot else exam_file
            if active and name:
                with st.spinner("Gemini מנתח את התשובות..."):
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    prompt = f"נתח מבחן ב{subj} עבור {name}. מחוון: {st.session_state.current_rubric}. תן ציון מספרי בולט ומשוב פדגוגי."
                    resp = model.generate_content([prompt, Image.open(active)])
                    txt = resp.text
                    score = "".join(filter(str.isdigit, txt[:40])) or "100"
                    
                    st.session_state.reports.append({
                        "שם": name, "מקצוע": subj, "כיתה": grade,
                        "ציון": score, "תאריך": datetime.now().strftime("%d/%m/%Y"), "דוח": txt
                    })
                    st.success("הבדיקה הושלמה!")
                    st.markdown(f"<div class='modern-card' style='background:#f7fafc;'>{txt}</div>", unsafe_allow_html=True)

    with tab2:
        st.markdown("<div class='modern-card'>", unsafe_allow_html=True)
        st.subheader("ארכיון פדגוגי")
        f_subj = st.selectbox("סנן מקצוע:", ["הכל"] + subs)
        
        data = [r for r in st.session_state.reports if f_subj == "הכל" or r['מקצוע'] == f_subj]
        
        if data:
            for r in reversed(data):
                with st.expander(f"📄 {r['שם']} | {r['מקצוע']} | ציון: {r['ציון']}"):
                    st.write(f"תאריך: {r['תאריך']} | כיתה: {r['כיתה']}")
                    st.markdown(r['דוח'])
        else: st.info("אין דוחות זמינים כרגע.")
        st.markdown("</div>", unsafe_allow_html=True)

    if st.sidebar.button("Log out"):
        st.session_state.logged_in = False
        st.rerun()
