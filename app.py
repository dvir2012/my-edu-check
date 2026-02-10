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

# --- 2. עיצוב UI מאיר פנים ומזמין ---
st.set_page_config(page_title="EduCheck - Welcome Home", layout="wide")

st.markdown("""
<style>
    /* רקע בהיר ומאיר פנים עם איורים עדינים */
    .stApp {
        background-color: #fdfbf7;
        background-image: url('https://www.transparenttextures.com/patterns/notebook.png'); /* מרקם של נייר מחברת */
        direction: rtl;
        text-align: right;
    }

    /* כרטיסים מעוגלים ורכים */
    .welcome-card {
        background: white;
        border-radius: 30px;
        padding: 35px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.05);
        border: 2px solid #f1f5f9;
        margin-bottom: 25px;
        color: #334155;
    }

    /* כותרות בצבעים חמים */
    h1 {
        color: #f97316 !important; /* כתום חם */
        font-family: 'Assistant', sans-serif;
        font-weight: 800;
    }
    h3 {
        color: #0d9488 !important; /* ירוק מנטה עמוק */
    }

    /* כפתור גדול ומזמין */
    .stButton>button {
        background: linear-gradient(135deg, #0d9488 0%, #2dd4bf 100%);
        color: white !important;
        border: none;
        padding: 15px 30px;
        border-radius: 20px;
        font-weight: 700;
        font-size: 1.2rem;
        width: 100%;
        transition: 0.3s all;
    }
    .stButton>button:hover {
        transform: scale(1.02);
        box-shadow: 0 8px 20px rgba(13, 148, 136, 0.3);
    }

    /* תיבות טקסט נקיות */
    .stTextInput input, .stTextArea textarea, .stSelectbox div {
        background: #f8fafc !important;
        border: 1px solid #e2e8f0 !important;
        border-radius: 15px !important;
        padding: 12px !important;
    }

    /* עיצוב טאבים */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        padding: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        background: #f1f5f9;
        border-radius: 15px 15px 0 0;
        padding: 10px 25px;
        color: #475569 !important;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. ניהול מצב ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'reports' not in st.session_state: st.session_state.reports = []
if 'current_rubric' not in st.session_state: st.session_state.current_rubric = ""

# --- 4. מסך כניסה מאיר פנים ---
if not st.session_state.logged_in:
    st.markdown("<div style='height: 10vh;'></div>", unsafe_allow_html=True)
    _, login_col, _ = st.columns([1, 1.2, 1])
    with login_col:
        st.markdown("<div class='welcome-card' style='text-align: center;'>", unsafe_allow_html=True)
        st.image("https://cdn-icons-png.flaticon.com/512/3429/3429156.png", width=100) # איור של מורה
        st.markdown("<h1>שלום מורה יקר/ה! ✨</h1>", unsafe_allow_html=True)
        st.write("כמה טוב שבאת. איזה כיף להתחיל לעבוד ביחד.")
        user_key = st.text_input("הזינו את קוד הגישה האישי:", type="password")
        if st.button("בואו נתחיל! 🚀"):
            if user_key in ALLOWED_PASSWORDS:
                st.session_state.logged_in = True
                st.rerun()
            else: st.error("הקוד לא מדויק, נסו שוב בחיוך 😊")
        st.markdown("</div>", unsafe_allow_html=True)

# --- 5. המערכת המרכזית ---
else:
    st.markdown("<div style='text-align: center; padding: 20px;'><h1>המרחב הפדגוגי שלך 🌿</h1></div>", unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["📋 בדיקה חדשה", "📁 תיקי תלמידים"])

    with tab1:
        st.markdown("<div class='welcome-card'>", unsafe_allow_html=True)
        col_main, col_side = st.columns([2, 1])
        
        with col_main:
            st.subheader("📝 פרטי המשימה")
            c1, c2, c3 = st.columns(3)
            with c1: name = st.text_input("שם התלמיד:")
            with c2: grade = st.text_input("כיתה:")
            with c3: 
                subjects = ["תורה", "נביא", "גמרא", "משנה", "הלכה", "מדעים", "היסטוריה", "עברית/לשון", "אחר..."]
                subj = st.selectbox("מקצוע:", subjects)
            
            st.divider()
            exam_file = st.file_uploader("העלאת צילום התשובות", type=['png', 'jpg', 'jpeg'])
            cam_file = st.camera_input("או צלמו עכשיו")
        
        with col_side:
            st.subheader("🪄 יצירת מחוון")
            rubric_img = st.file_uploader("צילום השאלות", type=['png', 'jpg', 'jpeg'])
            chat_cmd = st.text_input("הנחיות ל-AI:")
            if st.button("בנה מחוון חכם"):
                model = genai.GenerativeModel('gemini-1.5-flash')
                res = model.generate_content([f"צור מחוון תשובות ברור: {chat_cmd}", Image.open(rubric_img) if rubric_img else ""])
                st.session_state.current_rubric = res.text
            st.session_state.current_rubric = st.text_area("טיוטת המחוון:", value=st.session_state.current_rubric, height=150)

        if st.button("שלח לבדיקה וניתוח 🚀"):
            active = cam_file if cam_file else exam_file
            if active and name:
                with st.spinner("ה-AI בודק במקצועיות..."):
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    prompt = f"נתח מבחן ב{subj} לתלמיד {name}. מחוון: {st.session_state.current_rubric}. תן משוב מעודכן ומאיר פנים."
                    resp = model.generate_content([prompt, Image.open(active)])
                    txt = resp.text
                    score = "".join(filter(str.isdigit, txt[:30]))
                    
                    st.session_state.reports.append({
                        "שם": name, "מקצוע": subj, "כיתה": grade,
                        "ציון": score if score else "בוצע", "תאריך": datetime.now().strftime("%d/%m/%Y"), "דוח": txt
                    })
                    st.success("נהדר! הבדיקה נשמרה בארכיון.")
                    st.markdown(f"<div style='background:#f0fdf4; color:#166534; padding:20px; border-radius:15px; border-right: 5px solid #2dd4bf;'>{txt}</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with tab2:
        st.markdown("<div class='welcome-card'>", unsafe_allow_html=True)
        st.subheader("📊 סיכום הישגים כיתתי")
        f_subj = st.selectbox("סנן לפי מקצוע:", ["הכל"] + subjects)
        
        data = st.session_state.reports
        if f_subj != "הכל":
            data = [r for r in data if r['מקצוע'] == f_subj]

        if data:
            for r in reversed(data):
                with st.expander(f"📔 {r['מקצוע']} | {r['שם']} | ציון: {r['ציון']}"):
                    st.markdown(r['דוח'])
        else:
            st.info("עדיין אין דוחות שמורים. בואו נתחיל לבדוק!")
        st.markdown("</div>", unsafe_allow_html=True)

    if st.sidebar.button("🚪 יציאה"):
        st.session_state.logged_in = False
        st.rerun()
