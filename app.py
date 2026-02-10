import streamlit as st
import google.generativeai as genai
from PIL import Image
import pandas as pd
from datetime import datetime

# --- 1. הגדרות אבטחה ---
MY_API_KEY = "AIzaSyDJdiYe4VmudGKFQzoCI_MmngD26D4wm1Q" 
ALLOWED_PASSWORDS = [
    "dvir2012", "Teacher2012", "Sunset2012", "מורה2012", "Dvir_2012!",
    "2012EduCheck", "D2012V", "D@2012", "Dvir2012Pro", "Gold2012"
]
genai.configure(api_key=MY_API_KEY)

# --- 2. עיצוב UI צבעוני ותוסס (Vibrant & Colorful) ---
st.set_page_config(page_title="EduCheck Color Party!", layout="wide")

st.markdown("""
<style>
    /* רקע צבעוני מדורג שזז */
    .stApp {
        background: linear-gradient(-45deg, #ee7752, #e73c7e, #23a6d5, #23d5ab);
        background-size: 400% 400%;
        animation: gradient 15s ease infinite;
        direction: rtl;
        text-align: right;
    }
    @keyframes gradient {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }

    /* כרטיסים צבעוניים עם שקיפות */
    .color-card {
        background: rgba(255, 255, 255, 0.2);
        backdrop-filter: blur(10px);
        border-radius: 25px;
        padding: 25px;
        border: 2px solid rgba(255, 255, 255, 0.3);
        margin-bottom: 20px;
        color: white;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
    }

    /* כותרות בולטות */
    h1, h2, h3 {
        color: white !important;
        text-shadow: 2px 2px 10px rgba(0,0,0,0.2);
        font-family: 'Assistant', sans-serif;
    }

    /* כפתור בצבע ניאון */
    .stButton>button {
        background: #ffff00;
        color: #e73c7e !important;
        border-radius: 50px;
        padding: 15px 40px;
        font-weight: 900;
        font-size: 1.3rem;
        border: none;
        box-shadow: 0 5px 15px rgba(255, 255, 0, 0.4);
        transition: 0.3s;
    }
    .stButton>button:hover {
        transform: scale(1.05) rotate(1deg);
        background: white;
    }

    /* טאבים צבעוניים */
    .stTabs [data-baseweb="tab-list"] {
        background: rgba(255, 255, 255, 0.3);
        border-radius: 20px;
        padding: 5px;
    }
    .stTabs [data-baseweb="tab"] {
        color: white !important;
        font-weight: bold;
    }

    /* תיבות קלט */
    input, textarea, select {
        background: rgba(255, 255, 255, 0.9) !important;
        border-radius: 15px !important;
        color: #333 !important;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. ניהול מצב ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'reports' not in st.session_state: st.session_state.reports = []
if 'current_rubric' not in st.session_state: st.session_state.current_rubric = ""

# --- 4. מסך כניסה צבעוני ---
if not st.session_state.logged_in:
    st.markdown("<div style='height: 15vh;'></div>", unsafe_allow_html=True)
    _, login_col, _ = st.columns([1, 1.5, 1])
    with login_col:
        st.markdown("<div class='color-card' style='text-align: center;'>", unsafe_allow_html=True)
        st.markdown("<h1 style='font-size: 3rem;'>🎨 EduCheck</h1>", unsafe_allow_html=True)
        st.write("### הכניסו את המילה הסודית ונתחיל בחגיגה!")
        user_key = st.text_input("", type="password", placeholder="כאן כותבים את הסיסמה...")
        if st.button("בואו נשתגע! ✨"):
            if user_key in ALLOWED_PASSWORDS:
                st.session_state.logged_in = True
                st.rerun()
            else: st.error("זה לא הקוד... נסו שוב באנרגיה!")
        st.markdown("</div>", unsafe_allow_html=True)

# --- 5. המערכת המרכזית ---
else:
    st.markdown("<h1 style='text-align: center; font-size: 3.5rem;'>מרכז הלמידה הצבעוני 🌈</h1>", unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["🚀 בדיקה מהירה", "📊 היסטוריה וציונים"])

    with tab1:
        c_right, c_left = st.columns([1.5, 1])
        
        with c_right:
            st.markdown("<div class='color-card' style='background: rgba(255,255,255,0.1);'>", unsafe_allow_html=True)
            st.subheader("📝 פרטי המבחן")
            col_a, col_b = st.columns(2)
            with col_a:
                name = st.text_input("שם התלמיד:")
                grade = st.text_input("כיתה:")
            with col_b:
                subjects = ["תורה", "נביא", "גמרא", "משנה", "הלכה", "מדעים", "היסטוריה", "עברית/לשון", "אחר..."]
                subj = st.selectbox("בחר מקצוע:", subjects)
            
            st.divider()
            exam_img = st.file_uploader("העלה את המבחן (תמונה)", type=['png', 'jpg', 'jpeg'])
            cam_img = st.camera_input("צילום ישיר")
            st.markdown("</div>", unsafe_allow_html=True)

        with c_left:
            st.markdown("<div class='color-card' style='background: rgba(79, 70, 229, 0.3);'>", unsafe_allow_html=True)
            st.subheader("🪄 מחולל מחוון AI")
            rubric_f = st.file_uploader("צילום שאלון למחוון", type=['png', 'jpg', 'jpeg'])
            chat_cmd = st.text_input("הוראה ל-AI (למשל: 'היה נדיב בציון'):")
            if st.button("צור מחוון ⚡"):
                model = genai.GenerativeModel('gemini-1.5-flash')
                res = model.generate_content([f"צור מחוון צבעוני וברור ל{subj}: {chat_cmd}", Image.open(rubric_f) if rubric_f else ""])
                st.session_state.current_rubric = res.text
            st.session_state.current_rubric = st.text_area("המחוון שלך:", value=st.session_state.current_rubric, height=120)
            st.markdown("</div>", unsafe_allow_html=True)

        if st.button("בדוק עכשיו! 🎊"):
            active = cam_img if cam_img else exam_img
            if active and name:
                with st.spinner("ה-AI רוקד על המבחן..."):
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    prompt = f"נתח מבחן ב{subj} לתלמיד {name}. מחוון: {st.session_state.current_rubric}. תן ציון ענק ומשוב שמח!"
                    resp = model.generate_content([prompt, Image.open(active)])
                    txt = resp.text
                    score = "".join(filter(str.isdigit, txt[:30]))
                    
                    st.session_state.reports.append({
                        "שם": name, "מקצוע": subj, "כיתה": grade,
                        "ציון": score if score else "100!", "תאריך": datetime.now().strftime("%d/%m/%Y"), "דוח": txt
                    })
                    st.success("נהדר! הבדיקה הסתיימה בהצלחה!")
                    st.markdown(f"<div class='color-card' style='background:white; color:black; font-weight:bold;'>{txt}</div>", unsafe_allow_html=True)

    with tab2:
        st.markdown("<div class='color-card'>", unsafe_allow_html=True)
        st.subheader("📂 כל הציונים והדוחות")
        f_subj = st.selectbox("סנן לפי מקצוע:", ["הכל"] + subjects)
        
        data = st.session_state.reports
        if f_subj != "הכל":
            data = [r for r in data if r['מקצוע'] == f_subj]

        if data:
            for r in reversed(data):
                with st.expander(f"⭐ {r['מקצוע']} | {r['שם']} | ציון: {r['ציון']}"):
                    st.markdown(r['דוח'])
        else:
            st.info("עדיין אין דוחות. בואו ניצור כמה!")
        st.markdown("</div>", unsafe_allow_html=True)

    if st.sidebar.button("🚪 Logout"):
        st.session_state.logged_in = False
        st.rerun()
