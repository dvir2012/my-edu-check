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

# --- 2. עיצוב Cyber-Tech UI (Dark Theme) ---
st.set_page_config(page_title="EduCheck AI - Pro Tech", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap');

    /* רקע כהה וטכנולוגי */
    .stApp {
        background-color: #0d1117;
        color: #c9d1d9;
        direction: rtl;
        text-align: right;
    }

    /* כרטיסי טכנולוגיה צפים */
    .tech-card {
        background: #161b22;
        border-radius: 12px;
        padding: 25px;
        border: 1px solid #30363d;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        margin-bottom: 20px;
    }

    /* כותרות זוהרות */
    .app-title {
        background: linear-gradient(90deg, #58a6ff, #1f6feb);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        font-size: 3rem;
        text-align: center;
        letter-spacing: -1px;
    }

    /* כפתורי Cyber */
    .stButton>button {
        background: linear-gradient(135deg, #238636 0%, #2ea043 100%);
        color: white !important;
        border: none;
        border-radius: 6px;
        padding: 12px;
        font-weight: bold;
        text-transform: uppercase;
        transition: 0.3s all;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 0 15px rgba(46, 160, 67, 0.4);
    }

    /* טאבים בסגנון טכני */
    .stTabs [data-baseweb="tab-list"] {
        background-color: #0d1117;
        border-bottom: 2px solid #30363d;
    }
    .stTabs [data-baseweb="tab"] {
        color: #8b949e !important;
        font-family: 'JetBrains Mono', monospace;
    }
    .stTabs [data-baseweb="tab--active"] {
        color: #58a6ff !important;
        border-bottom-color: #58a6ff !important;
    }

    /* שדות קלט כהים */
    input, textarea, select {
        background-color: #0d1117 !important;
        color: white !important;
        border: 1px solid #30363d !important;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. ניהול Session State ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'reports' not in st.session_state: st.session_state.reports = []
if 'current_rubric' not in st.session_state: st.session_state.current_rubric = ""
if 'letter_library' not in st.session_state: st.session_state.letter_library = []

# --- 4. מסך כניסה Cyber ---
if not st.session_state.logged_in:
    st.markdown("<div style='height: 15vh;'></div>", unsafe_allow_html=True)
    _, login_col, _ = st.columns([1, 1.2, 1])
    with login_col:
        st.markdown("<div class='tech-card'>", unsafe_allow_html=True)
        st.markdown("<h1 class='app-title'>EduCheck AI</h1>", unsafe_allow_html=True)
        st.write("<p style='text-align:center; color:#8b949e;'>CORE SYSTEM ACCESS REQUIRED</p>", unsafe_allow_html=True)
        user_key = st.text_input("ACCESS KEY:", type="password", placeholder="PASSWORD...")
        if st.button("AUTHORIZE"):
            if user_key in ALLOWED_PASSWORDS:
                st.session_state.logged_in = True
                st.rerun()
            else: st.error("ACCESS DENIED")
        st.markdown("</div>", unsafe_allow_html=True)

# --- 5. ממשק המערכת הראשי ---
else:
    # סרגל צדי טכנולוגי
    with st.sidebar:
        st.markdown("### 🛠️ MODULES")
        st.divider()
        st.subheader("📦 DATABASE LOADER")
        st.write("הזרקת מאגר אותיות מסיבי (ZIP)")
        zip_file = st.file_uploader("", type=['zip'], key="sidebar_zip")
        
        if zip_file and not st.session_state.letter_library:
            with st.spinner("PROCESSING DATASET..."):
                with zipfile.ZipFile(zip_file, 'r') as z:
                    all_imgs = [f for f in z.namelist() if f.lower().endswith(('png', 'jpg', 'jpeg'))]
                    for i in range(0, len(all_imgs), 15):
                        with z.open(all_imgs[i]) as f:
                            img = Image.open(io.BytesIO(f.read())).convert("RGB")
                            letter_type = all_imgs[i].split('/')[0]
                            st.session_state.letter_library.append(f"PATTERN_{letter_type}")
                            st.session_state.letter_library.append(img)
                st.success(f"SYSTEM READY: {len(all_imgs)} SAMPLES LOADED")

        st.divider()
        if st.button("TERMINATE SESSION"):
            st.session_state.logged_in = False
            st.rerun()

    st.markdown("<h1 class='app-title'>EduCheck AI PRO</h1>", unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["📡 NEURAL ANALYSIS", "💾 ARCHIVE DATA"])

    with tab1:
        col_m, col_s = st.columns([2, 1])
        
        with col_m:
            st.markdown("<div class='tech-card'>", unsafe_allow_html=True)
            st.subheader("👤 STUDENT METADATA")
            r1, r2, r3 = st.columns(3)
            with r1: name = st.text_input("שם מלא:")
            with r2: grade = st.text_input("כיתה:")
            with r3: 
                subs = ["תורה", "נביא", "גמרא", "משנה", "הלכה", "מדעים", "היסטוריה", "עברית/לשון", "אחר..."]
                subj = st.selectbox("מקצוע:", subs)
            
            st.divider()
            st.subheader("📷 SCANNER INPUT")
            exam_file = st.file_uploader("UPLOAD EXAM", type=['png', 'jpg', 'jpeg'])
            cam_shot = st.camera_input("LIVE CAPTURE")
            st.markdown("</div>", unsafe_allow_html=True)

        with col_s:
            st.markdown("<div class='tech-card'>", unsafe_allow_html=True)
            st.subheader("⚙️ LOGIC RUBRIC")
            rubric_f = st.file_uploader("UPLOAD QUESTIONNAIRE", type=['png', 'jpg', 'jpeg'])
            chat_cmd = st.text_input("PROMPT REFINEMENT:")
            if st.button("GENERATE LOGIC"):
                with st.spinner("AI COMPILING..."):
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    res = model.generate_content([f"בנה מחוון טכני ל{subj}: {chat_cmd}", Image.open(rubric_f) if rubric_f else ""])
                    st.session_state.current_rubric = res.text
            st.session_state.current_rubric = st.text_area("RUBRIC CONTENT:", value=st.session_state.current_rubric, height=180)
            st.markdown("</div>", unsafe_allow_html=True)

        if st.button("🚀 EXECUTE FULL SCAN"):
            active = cam_shot if cam_shot else exam_file
            if active and name:
                with st.spinner("AI NEURAL PROCESSING..."):
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    
                    final_prompt = [
                        "אתה מערכת AI לניתוח כתב יד עברי. השתמש במאגר הדגימות המצורף לזיהוי אותיות במבחן:",
                        *st.session_state.letter_library,
                        f"בצע בדיקה לסטודנט {name} במקצוע {subj}. השווה למחוון: {st.session_state.current_rubric}.",
                        "החזר דוח טכני הכולל: פענוח טקסט, ציון סופי, וניתוח שגיאות פדגוגי.",
                        Image.open(active)
                    ]
                    
                    resp = model.generate_content(final_prompt)
                    txt = resp.text
                    score = "".join(filter(str.isdigit, txt[:40])) or "100"
                    
                    st.session_state.reports.append({
                        "שם": name, "מקצוע": subj, "כיתה": grade,
                        "ציון": score, "תאריך": datetime.now().strftime("%d/%m/%Y"), "דוח": txt
                    })
                    st.success("SCAN COMPLETE")
                    st.markdown(f"<div class='tech-card' style='background:#1c2128; border-left: 5px solid #2ea043;'>{txt}</div>", unsafe_allow_html=True)

    with tab2:
        st.markdown("<div class='tech-card'>", unsafe_allow_html=True)
        st.subheader("📊 SYSTEM ARCHIVE")
        f_subj = st.selectbox("FILTER BY MODULE:", ["ALL"] + subs)
        data = [r for r in st.session_state.reports if f_subj == "ALL" or r['מקצוע'] == f_subj]
        
        if data:
            for r in reversed(data):
                with st.expander(f"📁 {r['תאריך']} | {r['שם']} | SCORE: {r['ציון']}"):
                    st.markdown(r['דוח'])
        else: st.info("NO ARCHIVED DATA FOUND.")
        st.markdown("</div>", unsafe_allow_html=True)
