import streamlit as st
import google.generativeai as genai
from PIL import Image
import pandas as pd
from datetime import datetime
import io

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
    }
    /* תיקון צבע ההוראות ללבן מודגש וקריא */
    .instruction-text { 
        color: #ffffff !important; 
        font-weight: 900 !important; 
        font-size: 1.2rem; 
        margin-bottom: 12px;
        text-shadow: 1px 1px 2px #000000; /* צל שחור עדין לשיפור הקריאות */
    }
    .stButton>button { 
        background: linear-gradient(135deg, #38bdf8 0%, #1d4ed8 100%); 
        color: white !important; border-radius: 10px; font-weight: 700; width: 100%;
    }
    .result-box { background: #1e293b; border-right: 5px solid #38bdf8; padding: 20px; border-radius: 10px; margin-top: 20px; white-space: pre-wrap; color: #ffffff; }
    label { color: #ffffff !important; font-weight: bold !important; } /* הפיכת כל הלייבלים ללבן מודגש */
</style>
""", unsafe_allow_html=True)

# אתחול Session
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'reports' not in st.session_state: st.session_state.reports = []
if 'rubric' not in st.session_state: st.session_state.rubric = ""
if 'students' not in st.session_state: st.session_state.students = []

# --- 3. מסך כניסה ---
if not st.session_state.logged_in:
    _, col, _ = st.columns([1, 1, 1])
    with col:
        st.markdown("<div class='glass-card' style='text-align: center;'>", unsafe_allow_html=True)
        st.markdown("<p class='instruction-text'>**נא להזין קוד גישה כדי להתחיל:**</p>", unsafe_allow_html=True)
        pwd = st.text_input("קוד גישה:", type="password")
        if st.button("התחבר"):
            if pwd in ALLOWED_PASSWORDS:
                st.session_state.logged_in = True
                st.rerun()
            else: st.error("קוד שגוי")
        st.markdown("</div>", unsafe_allow_html=True)

# --- 4. המערכת המרכזית ---
else:
    st.markdown("<h1 class='main-title'>EduCheck AI Pro 🎓</h1>", unsafe_allow_html=True)
    
    tab_work, tab_archive, tab_settings = st.tabs(["📝 בדיקה ומחוון", "📂 ארכיון", "⚙️ הגדרות"])

    with tab_work:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        col_inputs, col_preview = st.columns([1, 1])
        
        with col_inputs:
            st.markdown("<p class='instruction-text'>**שלב 1: בחירת מקצוע ושם תלמיד**</p>", unsafe_allow_html=True)
            subject_active = st.selectbox("**בחר מקצוע:**", SUBJECTS)
            
            if st.session_state.students:
                s_name = st.selectbox("**בחר תלמיד מהרשימה:**", st.session_state.students)
            else:
                s_name = st.text_input("**הקלד שם תלמיד (או הגדר כיתה בהגדרות):**")
            
            st.divider()
            st.markdown("<p class='instruction-text'>**שלב 2: הגדרת מחוון התשובות**</p>", unsafe_allow_html=True)
            rubric_method = st.radio("**בחר שיטה להזנת תשובות נכונות:**", ["יצירה אוטומטית (AI)", "העלאת קובץ/תמונה", "הקלדה ידנית"])
            
            if rubric_method == "יצירה אוטומטית (AI)":
                if st.button("✨ צור מחוון עכשיו"):
                    try:
                        model = genai.GenerativeModel('gemini-1.5-flash')
                        res = model.generate_content(f"צור מחוון תשובות למבחן ב{subject_active}.")
                        st.session_state.rubric = res.text
                    except Exception as e: st.error(f"שגיאה: {e}")

            elif rubric_method == "העלאת קובץ/תמונה":
                st.markdown("<p style='color:white; font-weight:bold;'>**העלה תמונה של דף התשובות שלך:**</p>", unsafe_allow_html=True)
                rubric_file = st.file_uploader("**בחר קובץ מחוון:**", type=['jpg', 'png', 'pdf'])
                if rubric_file and st.button("🔍 סרוק קובץ"):
                    try:
                        img_rubric = Image.open(rubric_file)
                        model = genai.GenerativeModel('gemini-1.5-flash')
                        res = model.generate_content(["תמלל את המחוון שבתמונה:", img_rubric])
                        st.session_state.rubric = res.text
                    except Exception as e: st.error(f"שגיאה בסריקה: {e}")

            st.session_state.rubric = st.text_area("**ערוך/אשר את המחוון הסופי:**", value=st.session_state.rubric, height=150)

        with col_preview:
            st.markdown("<p class='instruction-text'>**שלב 3: העלאת מבחן ובדיקה**</p>", unsafe_allow_html=True)
            st.markdown("<p style='color:white; font-weight:bold;'>**העלה את צילום המבחן של התלמיד כאן:**</p>", unsafe_allow_html=True)
            up_file = st.file_uploader("**צילום המבחן:**", type=['jpg', 'png', 'jpeg'])
            
            if st.button("🚀 הרץ בדיקה וקבל ציון"):
                if up_file and s_name and st.session_state.rubric:
                    with st.spinner(f"בודק את המבחן של {s_name}..."):
                        try:
                            img_pil = Image.open(up_file)
                            model = genai.GenerativeModel('gemini-1.5-flash')
                            prompt = f"נתח את המבחן ב{subject_active} של {s_name} לפי המחוון: {st.session_state.rubric}. תן ציון ומשוב."
                            res = model.generate_content([prompt, img_pil])
                            st.session_state.current_res = res.text
                            st.session_state.reports.append({
                                "שם": s_name, "שיעור": subject_active, "דוח": res.text, "זמן": datetime.now().strftime("%d/%m %H:%M")
                            })
                        except Exception as e: st.error(f"שגיאה בבדיקה: {e}")
                else: st.warning("**נא לוודא שכל השלבים הקודמים הושלמו!**")
            
            if 'current_res' in st.session_state:
                st.markdown("<p class='instruction-text'>**תוצאת הבדיקה:**</p>", unsafe_allow_html=True)
                st.markdown(f"<div class='result-box'>{st.session_state.current_res}</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with tab_archive:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.markdown("<p class='instruction-text'>**צפייה בציונים שנשמרו:**</p>", unsafe_allow_html=True)
        filter_sub = st.selectbox("**סנן לפי מקצוע:**", ["הכל"] + SUBJECTS)
        display_data = st.session_state.reports if filter_sub == "הכל" else [r for r in st.session_state.reports if r['שיעור'] == filter_sub]
        for r in reversed(display_data):
            with st.expander(f"{r['שם']} - {r['שיעור']}"):
                st.write(f"**זמן בדיקה:** {r['זמן']}")
                st.markdown(r['דוח'])
        st.markdown("</div>", unsafe_allow_html=True)

    with tab_settings:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.markdown("<p class='instruction-text'>**ניהול רשימת כיתה:**</p>", unsafe_allow_html=True)
        names_input = st.text_area("**הזן שמות תלמידים (מופרדים בפסיק):**", value=", ".join(st.session_state.students))
        if st.button("שמור רשימת תלמידים"):
            st.session_state.students = [n.strip() for n in names_input.split(",") if n.strip()]
            st.success("הרשימה עודכנה בהצלחה!")
        
        st.divider()
        if st.button("🚪 התנתק מהמערכת"):
            st.session_state.logged_in = False
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
