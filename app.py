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

# --- 2. עיצוב UI סמכותי ואקדמי ---
st.set_page_config(page_title="EduCheck Academic", layout="wide")

st.markdown("""
<style>
    /* רקע ספרייה אקדמית יוקרתית */
    .stApp {
        background: linear-gradient(rgba(15, 23, 42, 0.85), rgba(15, 23, 42, 0.85)), 
                    url('https://images.unsplash.com/photo-1507842217343-583bb7270b66?ixlib=rb-4.0.3&auto=format&fit=crop&w=1920&q=80');
        background-size: cover;
        background-attachment: fixed;
        direction: rtl;
        text-align: right;
    }

    /* כרטיסי ניהול סמכותיים */
    .auth-card {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 215, 0, 0.3); /* נגיעה של זהב */
        border-radius: 15px;
        padding: 30px;
        color: white;
        box-shadow: 0 15px 35px rgba(0, 0, 0, 0.5);
        margin-bottom: 25px;
    }

    /* כותרות בסגנון אקדמי */
    h1, h2, h3, label {
        color: #F1F5F9 !important;
        font-family: 'Times New Roman', serif;
        letter-spacing: 1px;
    }

    /* כפתור "זהב" סמכותי */
    .stButton>button {
        background: linear-gradient(45deg, #B8860B, #FFD700);
        color: #0F172A !important;
        border: none;
        padding: 12px 30px;
        border-radius: 8px;
        font-weight: 900;
        text-transform: uppercase;
        transition: 0.3s;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(255, 215, 0, 0.4);
    }

    /* תיבות קלט נקיות */
    .stTextInput input, .stTextArea textarea, .stSelectbox div {
        background: #F8FAFC !important;
        color: #1E293B !important;
        border-radius: 5px !important;
        border: 2px solid #CBD5E1 !important;
    }
    
    /* טאבים */
    .stTabs [data-baseweb="tab-list"] {
        gap: 15px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: rgba(255,255,255,0.05);
        border: 1px solid rgba(255,255,255,0.1);
        padding: 10px 30px;
        border-radius: 10px 10px 0 0;
        color: white !important;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. ניהול מצב ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'reports' not in st.session_state: st.session_state.reports = []
if 'current_rubric' not in st.session_state: st.session_state.current_rubric = ""

# --- 4. מסך כניסה סמכותי ---
if not st.session_state.logged_in:
    st.markdown("<div style='height: 20vh;'></div>", unsafe_allow_html=True)
    _, login_col, _ = st.columns([1, 1, 1])
    with login_col:
        st.markdown("<div class='auth-card' style='text-align: center;'>", unsafe_allow_html=True)
        st.markdown("<h1 style='color:#FFD700 !important;'>מערכת ניהול פדגוגית</h1>", unsafe_allow_html=True)
        st.write("נא להזדהות באמצעות קוד הגישה")
        user_key = st.text_input("", type="password", placeholder="הזן מילה סודית...")
        if st.button("כניסה למערכת 🔒"):
            if user_key in ALLOWED_PASSWORDS:
                st.session_state.logged_in = True
                st.rerun()
            else: st.error("סיסמה שגויה. הגישה נחסמה.")
        st.markdown("</div>", unsafe_allow_html=True)

# --- 5. המערכת המרכזית ---
else:
    st.markdown("<h1 style='text-align: center; border-bottom: 2px solid #FFD700; padding-bottom: 10px;'>EduCheck AI - Academic Space</h1>", unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["🏛️ מרחב בדיקה", "📈 תיק תלמיד"])

    with tab1:
        col_side, col_main = st.columns([1, 2])
        
        with col_side:
            st.markdown("<div class='auth-card'>", unsafe_allow_html=True)
            st.subheader("🛠️ הגדרת מחוון")
            rubric_img = st.file_uploader("צילום שאלון", type=['png', 'jpg', 'jpeg'])
            chat_cmd = st.text_input("הנחיות ל-AI:")
            if st.button("ייצור מחוון אקדמי"):
                with st.spinner("מעבד..."):
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    res = model.generate_content([f"בנה מחוון תשובות אקדמי ומדויק: {chat_cmd}", Image.open(rubric_img) if rubric_img else ""])
                    st.session_state.current_rubric = res.text
            st.session_state.current_rubric = st.text_area("תוכן המחוון:", value=st.session_state.current_rubric, height=200)
            st.markdown("</div>", unsafe_allow_html=True)

        with col_main:
            st.markdown("<div class='auth-card'>", unsafe_allow_html=True)
            st.subheader("📝 בדיקת מבחן")
            c1, c2, c3 = st.columns(3)
            with c1: name = st.text_input("שם התלמיד:")
            with c2: grade = st.text_input("כיתה:")
            with c3: 
                subjects = ["תורה", "נביא", "גמרא", "משנה", "הלכה", "מדעים", "היסטוריה", "עברית/לשון", "אחר..."]
                subj = st.selectbox("מקצוע הלימוד:", subjects)
            
            st.divider()
            exam_file = st.file_uploader("העלה צילום תשובות", type=['png', 'jpg', 'jpeg'])
            if st.button("בצע ניתוח פדגוגי ⚖️"):
                if exam_file and name:
                    with st.spinner("מנתח בסטנדרט גבוה..."):
                        model = genai.GenerativeModel('gemini-1.5-flash')
                        prompt = f"נתח מבחן ב{subj} לתלמיד {name}. מחוון: {st.session_state.current_rubric}. ספק ציון סופי ומשוב מנומק."
                        resp = model.generate_content([prompt, Image.open(exam_file)])
                        txt = resp.text
                        score = "".join(filter(str.isdigit, txt[:30]))
                        
                        st.session_state.reports.append({
                            "שם": name, "מקצוע": subj, "כיתה": grade,
                            "ציון": score if score else "נבדק", "תאריך": datetime.now().strftime("%d/%m/%Y"), "דוח": txt
                        })
                        st.success("הבדיקה נרשמה בהצלחה.")
                        st.markdown(f"<div style='background:white; color:#0F172A; padding:20px; border-radius:10px;'>{txt}</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

    with tab2:
        st.markdown("<div class='auth-card'>", unsafe_allow_html=True)
        st.subheader("📊 סיכום הישגים")
        f_subj = st.selectbox("בחר מקצוע:", ["הכל"] + subjects)
        
        data = st.session_state.reports
        if f_subj != "הכל":
            data = [r for r in data if r['מקצוע'] == f_subj]

        if data:
            for r in reversed(data):
                with st.expander(f"📜 {r['מקצוע']} | {r['שם']} | ציון: {r['ציון']}"):
                    st.markdown(r['דוח'])
        else:
            st.info("אין נתונים רשומים.")
        st.markdown("</div>", unsafe_allow_html=True)

    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()
