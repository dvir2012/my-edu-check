import streamlit as st
import google.generativeai as genai
from PIL import Image
import pandas as pd
from datetime import datetime
import zipfile
import io

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
    .stApp { background-color: #f4f7f9; font-family: 'Segoe UI', sans-serif; direction: rtl; text-align: right; }
    .modern-card { background: #ffffff; border-radius: 12px; padding: 24px; box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05); border: 1px solid #e1e8ed; margin-bottom: 20px; color: black; }
    .app-title { color: #1a202c; font-weight: 700; font-size: 2.5rem; text-align: center; }
    .stButton>button { background-color: #3182ce; color: white !important; border-radius: 8px; font-weight: 600; width: 100%; }
</style>
""", unsafe_allow_html=True)

# --- 3. ניהול Session State (הוספת מאגר האותיות) ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'reports' not in st.session_state: st.session_state.reports = []
if 'current_rubric' not in st.session_state: st.session_state.current_rubric = ""
if 'letter_library' not in st.session_state: st.session_state.letter_library = [] # כאן נשמר המאגר

# --- 4. מסך כניסה ---
if not st.session_state.logged_in:
    st.markdown("<div style='height: 20vh;'></div>", unsafe_allow_html=True)
    _, login_col, _ = st.columns([1, 1, 1])
    with login_col:
        st.markdown("<div class='modern-card'>", unsafe_allow_html=True)
        st.markdown("<h1 class='app-title'>EduCheck AI</h1>", unsafe_allow_html=True)
        user_key = st.text_input("קוד גישה:", type="password")
        if st.button("כניסה למערכת"):
            if user_key in ALLOWED_PASSWORDS:
                st.session_state.logged_in = True
                st.rerun()
            else: st.error("סיסמה שגויה")
        st.markdown("</div>", unsafe_allow_html=True)

# --- 5. ממשק המערכת הראשי ---
else:
    # --- סרגל צדי לניהול המאגר המסיבי ---
    with st.sidebar:
        st.header("📦 מאגר אותיות (ZIP)")
        st.write("העלה קובץ ZIP מהמחשב עם אלפי דוגמאות לכתב יד.")
        zip_file = st.file_uploader("טען מאגר אותיות:", type=['zip'])
        
        if zip_file and not st.session_state.letter_library:
            with st.spinner("מעבד מאגר נתונים..."):
                with zipfile.ZipFile(zip_file, 'r') as z:
                    all_imgs = [f for f in z.namelist() if f.lower().endswith(('png', 'jpg', 'jpeg'))]
                    # לוקח דגימות מהמאגר כדי לא להעמיס על ה-AI (דגימה כל 15 תמונות)
                    for i in range(0, len(all_imgs), 15):
                        with z.open(all_imgs[i]) as f:
                            img = Image.open(io.BytesIO(f.read())).convert("RGB")
                            letter_type = all_imgs[i].split('/')[0] # שם התיקייה בתוך ה-ZIP
                            st.session_state.letter_library.append(f"דוגמה לאות {letter_type}")
                            st.session_state.letter_library.append(img)
                st.success(f"נטענו {len(all_imgs)} דוגמאות!")

        if st.sidebar.button("Log out"):
            st.session_state.logged_in = False
            st.rerun()

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
                with st.spinner("Gemini מנתח לפי המאגר המסיבי..."):
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    
                    # בניית הפרומפט המשולב (מאגר ZIP + המבחן)
                    final_prompt = [
                        "אתה מומחה לזיהוי כתב יד. השתמש בדוגמאות המצורפות מהמאגר כדי לזהות את האותיות במבחן:",
                        *st.session_state.letter_library,
                        f"נתח את המבחן של {name} במקצוע {subj}. מחוון: {st.session_state.current_rubric}. תן ציון בולט ומשוב פדגוגי.",
                        Image.open(active)
                    ]
                    
                    resp = model.generate_content(final_prompt)
                    txt = resp.text
                    score = "".join(filter(str.isdigit, txt[:40])) or "100"
                    
                    st.session_state.reports.append({
                        "שם": name, "מקצוע": subj, "כיתה": grade,
                        "ציון": score, "תאריך": datetime.now().strftime("%d/%m/%Y"), "דוח": txt
                    })
                    st.success("הבדיקה הושלמה!")
                    st.markdown(f"<div class='modern-card' style='background:#f7fafc; color:black;'>{txt}</div>", unsafe_allow_html=True)

    with tab2:
        st.markdown("<div class='modern-card'>", unsafe_allow_html=True)
        st.subheader("ארכיון פדגוגי")
        f_subj = st.selectbox("סנן מקצוע:", ["הכל"] + subs)
        data = [r for r in st.session_state.reports if f_subj == "הכל" or r['מקצוע'] == f_subj]
        if data:
            for r in reversed(data):
                with st.expander(f"📄 {r['שם']} | {r['מקצוע']} | ציון: {r['ציון']}"):
                    st.markdown(r['דוח'])
        else: st.info("אין דוחות זמינים כרגע.")
        st.markdown("</div>", unsafe_allow_html=True)
