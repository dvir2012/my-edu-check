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

# --- 2. עיצוב Cyber-Tech UI (ללא סרגלים וללא ZIP) ---
st.set_page_config(page_title="EduCheck AI - Unlimited", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
    [data-testid="stSidebar"] {display: none;}
    
    .stApp {
        background-color: #0d1117;
        color: #c9d1d9;
        direction: rtl;
        text-align: right;
    }

    .tech-card {
        background: #161b22;
        border-radius: 12px;
        padding: 25px;
        border: 1px solid #30363d;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        margin-bottom: 20px;
    }

    .app-title {
        background: linear-gradient(90deg, #58a6ff, #1f6feb);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        font-size: 3rem;
        text-align: center;
        padding: 20px;
    }

    .stButton>button {
        background: linear-gradient(135deg, #238636 0%, #2ea043 100%);
        color: white !important;
        border-radius: 6px;
        padding: 12px;
        font-weight: bold;
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. ניהול Session State ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'reports' not in st.session_state: st.session_state.reports = []
if 'current_rubric' not in st.session_state: st.session_state.current_rubric = ""

# --- 4. מסך כניסה ---
if not st.session_state.logged_in:
    st.markdown("<div style='height: 15vh;'></div>", unsafe_allow_html=True)
    _, login_col, _ = st.columns([1, 1.2, 1])
    with login_col:
        st.markdown("<div class='tech-card'>", unsafe_allow_html=True)
        st.markdown("<h1 class='app-title'>EduCheck AI</h1>", unsafe_allow_html=True)
        user_key = st.text_input("מפתח גישה למאגר המידע:", type="password", placeholder="הכנס סיסמה...")
        if st.button("אישור גישה"):
            if user_key in ALLOWED_PASSWORDS:
                st.session_state.logged_in = True
                st.rerun()
            else: st.error("גישה נדחתה")
        st.markdown("</div>", unsafe_allow_html=True)

# --- 5. ממשק ראשי מבוסס מאגרי ענן ---
else:
    st.markdown("<h1 class='app-title'>EduCheck AI PRO</h1>", unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["📡 ניתוח נתונים", "📊 ארכיון מערכת", "⚙️ ניהול חשבון"])

    with tab1:
        col_m, col_s = st.columns([2, 1])
        with col_m:
            st.markdown("<div class='tech-card'>", unsafe_allow_html=True)
            st.subheader("👤 פרטי התלמיד")
            r1, r2, r3 = st.columns(3)
            with r1: name = st.text_input("שם מלא:")
            with r2: grade = st.text_input("כיתה:")
            with r3: 
                subs = ["תורה", "נביא", "גמרא", "משנה", "הלכה", "מדעים", "היסטוריה", "עברית/לשון", "אחר..."]
                subj = st.selectbox("מקצוע:", subs)
            st.divider()
            st.subheader("📷 קלט סריקה למאגר")
            exam_file = st.file_uploader("העלה מבחן לניתוח AI", type=['png', 'jpg', 'jpeg'])
            cam_shot = st.camera_input("צילום חי מהשטח")
            st.markdown("</div>", unsafe_allow_html=True)

        with col_s:
            st.markdown("<div class='tech-card'>", unsafe_allow_html=True)
            st.subheader("⚙️ יצירת מחוון")
            rubric_f = st.file_uploader("העלה צילום שאלון (אופציונלי)", type=['png', 'jpg', 'jpeg'])
            if st.button("ייצר מחוון ממאגרי ידע"):
                with st.spinner("שואב נתונים ממאגרי גוגל..."):
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    res = model.generate_content([f"בנה מחוון תשובות מקצועי למבחן ב{subj}. השתמש במאגרי המידע שלך.", Image.open(rubric_f) if rubric_f else ""])
                    st.session_state.current_rubric = res.text
            st.session_state.current_rubric = st.text_area("תוכן המחוון לעריכה:", value=st.session_state.current_rubric, height=200)
            st.markdown("</div>", unsafe_allow_html=True)

        if st.button("🚀 הרץ ניתוח מול מאגרי גוגל"):
            active = cam_shot if cam_shot else exam_file
            if active and name:
                with st.spinner("מתחבר למאגרי מידע אינסופיים..."):
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    # הפרומפט שמפעיל את ה-AI כמאגר ידע
                    prompt = f"""
                    אתה משמש כמאגר מידע אינסופי לזיהוי כתב יד עברי. 
                    בצע ניתוח מעמיק למבחן המצורף של {name} במקצוע {subj}.
                    השווה את התשובות למחוון הבא: {st.session_state.current_rubric}.
                    השתמש בכל דגימות הכתב שברשותך במאגרי הענן של גוגל כדי להבין את הכתב בצורה מדויקת.
                    תחזיר תשובה בעברית: תמלול, ציון, ומשוב פדגוגי.
                    """
                    resp = model.generate_content([prompt, Image.open(active)])
                    txt = resp.text
                    st.session_state.reports.append({"שם": name, "מקצוע": subj, "כיתה": grade, "תאריך": datetime.now().strftime("%d/%m/%Y"), "דוח": txt})
                    st.markdown(f"<div class='tech-card' style='border-right: 5px solid #58a6ff;'>{txt}</div>", unsafe_allow_html=True)

    with tab2:
        st.markdown("<div class='tech-card'>", unsafe_allow_html=True)
        st.subheader("📊 ארכיון דוחות")
        for r in reversed(st.session_state.reports):
            with st.expander(f"📁 {r['תאריך']} | {r['שם']} | {r['מקצוע']}"):
                st.markdown(r['דוח'])
        st.markdown("</div>", unsafe_allow_html=True)

    with tab3:
        st.markdown("<div class='tech-card'>", unsafe_allow_html=True)
        st.subheader("⚙️ הגדרות מערכת")
        st.write("המערכת מחוברת כעת למאגרי המידע של Google Vision API.")
        if st.button("ניתוק ויציאה מהחשבון"):
            st.session_state.logged_in = False
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
