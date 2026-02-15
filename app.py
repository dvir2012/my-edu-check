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
    .stButton>button { 
        background: linear-gradient(135deg, #38bdf8 0%, #1d4ed8 100%); 
        color: white !important; border-radius: 10px; font-weight: 700; width: 100%;
    }
    .result-box { background: #1e293b; border-right: 5px solid #38bdf8; padding: 20px; border-radius: 10px; margin-top: 20px; white-space: pre-wrap; }
    .stTabs [data-baseweb="tab-list"] { gap: 20px; justify-content: center; }
    .stTabs [data-baseweb="tab"] { background-color: #1e293b; border-radius: 10px 10px 0 0; padding: 10px 30px; color: white; }
    .stTabs [aria-selected="true"] { background-color: #38bdf8 !important; color: #0f172a !important; }
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
        st.header("כניסה למערכת")
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
    
    tab_work, tab_archive, tab_settings = st.tabs(["📝 בדיקת מבחן ומחוון", "📂 ארכיון ציונים", "⚙️ הגדרות"])

    with tab_work:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        col_inputs, col_preview = st.columns([1, 1])
        
        with col_inputs:
            subject_active = st.selectbox("בחר מקצוע לבדיקה:", SUBJECTS)
            
            # בחירת תלמיד
            s_name = st.selectbox("בחר שם תלמיד:", st.session_state.students) if st.session_state.students else st.text_input("שם התלמיד:")
            
            st.write("---")
            st.subheader("⚙️ המחוון (Answer Key)")
            
            rubric_method = st.radio("איך תרצה להזין מחוון?", ["יצירה עם AI", "העלאת קובץ/תמונה", "הקלדה ידנית"])
            
            if rubric_method == "יצירה עם AI":
                if st.button("✨ צור מחוון אוטומטי"):
                    try:
                        model = genai.GenerativeModel('gemini-1.5-flash')
                        res = model.generate_content(f"צור מחוון תשובות מפורט למבחן ב{subject_active}.")
                        st.session_state.rubric = res.text
                        st.success("המחוון נוצר!")
                    except Exception as e:
                        st.error(f"שגיאה ביצירת מחוון: {e}")

            elif rubric_method == "העלאת קובץ/תמונה":
                rubric_file = st.file_uploader("העלה צילום מחוון או PDF:", type=['jpg', 'png', 'jpeg', 'pdf'], key="rubric_up")
                if rubric_file and st.button("🔍 סרוק מחוון"):
                    try:
                        img_rubric = Image.open(rubric_file)
                        model = genai.GenerativeModel('gemini-1.5-flash')
                        res = model.generate_content(["פענח את המחוון שבתמונה והפוך אותו לטקסט ברור לבדיקה:", img_rubric])
                        st.session_state.rubric = res.text
                        st.success("המחוון נסרק בהצלחה!")
                    except Exception as e:
                        st.error(f"שגיאה בסריקת הקובץ: {e}")

            st.session_state.rubric = st.text_area("תוכן המחוון הסופי:", value=st.session_state.rubric, height=150)

        with col_preview:
            st.subheader("🚀 בדיקת המבחן")
            up_file = st.file_uploader("העלה צילום מבחן תלמיד:", type=['jpg', 'png', 'jpeg'])
            
            if st.button("🏁 הרץ בדיקה פדגוגית"):
                if up_file and s_name and st.session_state.rubric:
                    with st.spinner(f"מנתח את המבחן של {s_name}..."):
                        try:
                            img_pil = Image.open(up_file)
                            model = genai.GenerativeModel('gemini-1.5-flash')
                            prompt = f"""
                            אתה מורה ל{subject_active}. נתח את המבחן של {s_name}.
                            המחוון לבדיקה: {st.session_state.rubric}
                            
                            דרישות:
                            1. השווה בין תשובות התלמיד למחוון.
                            2. תן ציון סופי (0-100).
                            3. תן משוב מפורט בעברית על נקודות חוזק וחולשה.
                            """
                            res = model.generate_content([prompt, img_pil])
                            
                            st.session_state.current_res = res.text
                            st.session_state.reports.append({
                                "שם": s_name, "שיעור": subject_active, "דוח": res.text, "זמן": datetime.now().strftime("%d/%m %H:%M")
                            })
                        except Exception as e:
                            st.error(f"שגיאה בתהליך הבדיקה: {e}")
                else: st.warning("מלא את כל הפרטים (שם, מחוון ותמונה)")
            
            if 'current_res' in st.session_state:
                st.markdown("<div class='result-box'>", unsafe_allow_html=True)
                st.write(st.session_state.current_res)
                st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with tab_archive:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        filter_sub = st.selectbox("סנן לפי מקצוע:", ["הכל"] + SUBJECTS)
        display_data = st.session_state.reports if filter_sub == "הכל" else [r for r in st.session_state.reports if r['שיעור'] == filter_sub]
        for r in reversed(display_data):
            with st.expander(f"{r['שם']} - {r['שיעור']} ({r['זמן']})"):
                st.markdown(r['דוח'])
        st.markdown("</div>", unsafe_allow_html=True)

    with tab_settings:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.subheader("👥 ניהול כיתה")
        names_input = st.text_area("הזן שמות תלמידים (מופרדים בפסיק):", value=", ".join(st.session_state.students))
        if st.button("שמור רשימה"):
            st.session_state.students = [n.strip() for n in names_input.split(",") if n.strip()]
            st.success("הרשימה עודכנה!")
        
        if st.button("🚪 התנתק"):
            st.session_state.logged_in = False
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
