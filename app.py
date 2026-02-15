import streamlit as st
import google.generativeai as genai
from PIL import Image
import pandas as pd
from datetime import datetime

# --- 1. הגדרות API וסיסמאות ---
genai.configure(api_key="AIzaSyDJdiYe4VmudGKFQzoCI_MmngD26D4wm1Q")

ALLOWED_PASSWORDS = ["dvir2012", "Teacher2012", "Sunset2012", "מורה2012", "Dvir_2012!"]

SUBJECTS = [
    "תורה", "גמרא", "דינים", "היסטוריה", "מדעים", "עברית", "מתמטיקה", 
    "אנגלית", "גאוגרפיה", "ספרות", "אזרחות", "של''ח", "תנ''ך", "משנה",
    "הבעה", "ערבית", "פיזיקה", "כימיה", "ביולוגיה", "מחשבת ישראל", "אחר"
]

# --- 2. עיצוב הממשק ---
st.set_page_config(page_title="EduCheck AI Pro", layout="wide")
st.markdown("""
<style>
    .stApp { background: #0f172a; color: white; direction: rtl; text-align: right; }
    .glass-card { 
        background: rgba(30, 41, 59, 0.7); 
        border: 1px solid #38bdf8; 
        border-radius: 15px; 
        padding: 25px; 
        margin-top: 10px;
    }
    .main-title { 
        font-size: 2.5rem; font-weight: 800; text-align: center;
        background: linear-gradient(90deg, #38bdf8, #818cf8);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        margin-bottom: 10px;
    }
    .stButton>button { 
        background: linear-gradient(135deg, #38bdf8 0%, #1d4ed8 100%); 
        color: white !important; border-radius: 10px; font-weight: 700; width: 100%;
    }
    .result-box { background: #1e293b; border-right: 5px solid #38bdf8; padding: 20px; border-radius: 10px; margin-top: 20px; }
    .stTabs [data-baseweb="tab-list"] { gap: 20px; justify-content: center; }
    .stTabs [data-baseweb="tab"] { 
        background-color: #1e293b; border-radius: 10px 10px 0 0; padding: 10px 30px; color: white;
    }
    .stTabs [aria-selected="true"] { background-color: #38bdf8 !important; color: #0f172a !important; }
    .settings-row { border-bottom: 1px solid #334155; padding: 15px 0; }
</style>
""", unsafe_allow_html=True)

# אתחול Session
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'reports' not in st.session_state: st.session_state.reports = []
if 'rubric' not in st.session_state: st.session_state.rubric = ""
if 'students' not in st.session_state: st.session_state.students = []
if 'current_user' not in st.session_state: st.session_state.current_user = ""

# --- 3. מסך כניסה ---
if not st.session_state.logged_in:
    _, col, _ = st.columns([1, 1, 1])
    with col:
        st.markdown("<div class='glass-card' style='text-align: center;'>", unsafe_allow_html=True)
        st.header("כניסה למערכת")
        pwd = st.text_input("קוד גישה:", type="password")
        if st.button("התחבר"):
            if pwd in ALLOWED_PASSWORDS:
                st.session_state.logged_in = True
                st.session_state.current_user = pwd
                st.rerun()
            else: st.error("קוד שגוי")
        st.markdown("</div>", unsafe_allow_html=True)

# --- 4. המערכת המרכזית ---
else:
    st.markdown("<h1 class='main-title'>EduCheck AI Pro 🎓</h1>", unsafe_allow_html=True)
    
    # שלוש כרטיסיות: בדיקה, ארכיון והגדרות
    tab_work, tab_archive, tab_settings = st.tabs(["📝 בדיקת מבחן ומחוון", "📂 ארכיון ציונים", "⚙️ הגדרות"])

    # --- כרטיסייה 1: עבודה ---
    with tab_work:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        col_inputs, col_preview = st.columns([1, 1])
        
        with col_inputs:
            subject_active = st.selectbox("בחר מקצוע לבדיקה:", SUBJECTS)
            
            if st.session_state.students:
                s_name = st.selectbox("בחר שם תלמיד מהרשימה:", st.session_state.students)
            else:
                s_name = st.text_input("שם התלמיד (הכנס ידנית או הגדר כיתה בהגדרות):")
            
            st.write("**ניהול מחוון:**")
            if st.button("✨ צור מחוון אוטומטי"):
                with st.spinner("Gemini בונה מחוון..."):
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    res = model.generate_content(f"צור מחוון תשובות מפורט למבחן ב{subject_active}.")
                    st.session_state.rubric = res.text
            st.session_state.rubric = st.text_area("ערוך את המחוון כאן:", value=st.session_state.rubric, height=150)

        with col_preview:
            st.write("**העלאת המבחן ובדיקה:**")
            up_file = st.file_uploader("העלה צילום מבחן:", type=['jpg', 'png', 'jpeg'])
            
            if st.button("🚀 הרץ בדיקה פדגוגית"):
                if up_file and s_name and st.session_state.rubric:
                    with st.spinner(f"מנתח את המבחן של {s_name}..."):
                        img_pil = Image.open(up_file)
                        model = genai.GenerativeModel('gemini-1.5-flash')
                        prompt = f"נתח את המבחן ב{subject_active} של {s_name} לפי המחוון: {st.session_state.rubric}. תן ציון ומשוב מפורט."
                        res = model.generate_content([prompt, img_pil])
                        
                        st.session_state.current_res = res.text
                        st.session_state.reports.append({
                            "שם": s_name, "שיעור": subject_active, "דוח": res.text, "זמן": datetime.now().strftime("%d/%m %H:%M")
                        })
                else: st.warning("נא לוודא שכל הפרטים מולאו.")
            
            if 'current_res' in st.session_state:
                st.markdown("### תוצאה:")
                st.markdown(f"<div class='result-box'>{st.session_state.current_res}</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # --- כרטיסייה 2: ארכיון ---
    with tab_archive:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        filter_sub = st.selectbox("סנן ארכיון לפי מקצוע:", ["הצג הכל"] + SUBJECTS)
        st.write("---")
        
        display_data = st.session_state.reports if filter_sub == "הצג הכל" else [r for r in st.session_state.reports if r['שיעור'] == filter_sub]
        
        if display_data:
            for r in reversed(display_data):
                with st.expander(f"{r['שם']} - {r['שיעור']} ({r['זמן']})"):
                    st.markdown(r['דוח'])
        else:
            st.info("לא נמצאו ציונים שמורים.")
        st.markdown("</div>", unsafe_allow_html=True)

    # --- כרטיסייה 3: הגדרות (ניהול חשבון וכיתה) ---
    with tab_settings:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.subheader("⚙️ הגדרות מערכת")
        
        # ניהול משתמש
        st.markdown("<div class='settings-row'>", unsafe_allow_html=True)
        st.write(f"**מחובר כרגע עם קוד:** `{st.session_state.current_user}`")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🚪 התנתק מהחשבון"):
                st.session_state.logged_in = False
                st.rerun()
        with col2:
            if st.button("🔄 החלף משתמש (נקה הכל)"):
                st.session_state.logged_in = False
                st.session_state.reports = []
                st.session_state.students = []
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

        # ניהול כיתה (עבר לכאן כדי לא להפריע בבדיקה)
        st.markdown("<div class='settings-row'>", unsafe_allow_html=True)
        st.subheader("👥 ניהול רשימת כיתה")
        temp_names = st.text_area("הזן שמות תלמידים (מופרדים בפסיק או שורה חדשה):", 
                                 value=", ".join(st.session_state.students) if st.session_state.students else "")
        if st.button("שמור רשימת תלמידים"):
            if temp_names:
                st.session_state.students = [s.strip() for s in temp_names.replace('\n', ',').split(',') if s.strip()]
                st.success(f"רשימת הכיתה עודכנה! ({len(st.session_state.students)} תלמידים)")
        st.markdown("</div>", unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)
