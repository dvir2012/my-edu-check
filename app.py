import streamlit as st
import google.generativeai as genai
from PIL import Image
import pandas as pd
from datetime import datetime
import io

# --- 1. הגדרות API וחיבור למודל PRO ---
# שימוש במפתח ה-API שלך וחיבור למודל החזק ביותר להבנת עברית וכתב יד
genai.configure(api_key="AIzaSyDJdiYe4VmudGKFQzoCI_MmngD26D4wm1Q")

ALLOWED_PASSWORDS = ["dvir2012", "Teacher2012", "Sunset2012", "מורה2012", "Dvir_2012!"]

SUBJECTS = [
    "תורה", "גמרא", "דינים", "היסטוריה", "מדעים", "עברית", "מתמטיקה", 
    "אנגלית", "גאוגרפיה", "ספרות", "אזרחות", "של''ח", "תנ''ך", "משנה",
    "הבעה", "ערבית", "פיזיקה", "כימיה", "ביולוגיה", "מחשבת ישראל", "אחר"
]

# --- 2. עיצוב הממשק (CSS) - לבן מודגש וברור על רקע כהה ---
st.set_page_config(page_title="EduCheck AI Pro", layout="wide")

st.markdown("""
<style>
    /* רקע כהה ועיצוב כללי */
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
        margin-bottom: 20px;
    }
    
    /* הוראות מודגשות בלבן - קריאות מקסימלית */
    .instruction-text { 
        color: #ffffff !important; 
        font-weight: 900 !important; 
        font-size: 1.3rem; 
        margin-bottom: 15px;
        text-shadow: 2px 2px 4px #000000;
        display: block;
    }
    
    /* הפיכת כל הלייבלים והטקסטים ללבן מודגש */
    label, .stMarkdown p, .stRadio label, .stSelectbox label { 
        color: #ffffff !important; 
        font-weight: 800 !important; 
        font-size: 1.15rem !important;
        text-shadow: 1px 1px 2px #000000;
    }
    
    .stButton>button { 
        background: linear-gradient(135deg, #38bdf8 0%, #1d4ed8 100%); 
        color: white !important; border-radius: 10px; font-weight: 700; width: 100%;
        border: none; padding: 12px;
    }
    
    .result-box { 
        background: #1e293b; 
        border-right: 5px solid #38bdf8; 
        padding: 25px; 
        border-radius: 10px; 
        margin-top: 20px; 
        white-space: pre-wrap; 
        color: #ffffff;
        font-size: 1.1rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
</style>
""", unsafe_allow_html=True)

# אתחול משתני מערכת
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'reports' not in st.session_state: st.session_state.reports = []
if 'rubric' not in st.session_state: st.session_state.rubric = ""
if 'students' not in st.session_state: st.session_state.students = []

# --- 3. מסך כניסה (Login) ---
if not st.session_state.logged_in:
    _, col, _ = st.columns([1, 1, 1])
    with col:
        st.markdown("<div class='glass-card' style='text-align: center;'>", unsafe_allow_html=True)
        st.markdown("<p class='instruction-text'>נא להזין קוד גישה:</p>", unsafe_allow_html=True)
        pwd = st.text_input("סיסמה:", type="password")
        if st.button("התחבר למערכת"):
            if pwd in ALLOWED_PASSWORDS:
                st.session_state.logged_in = True
                st.rerun()
            else: st.error("קוד שגוי")
        st.markdown("</div>", unsafe_allow_html=True)

# --- 4. המערכת המרכזית (לאחר התחברות) ---
else:
    st.markdown("<h1 class='main-title'>EduCheck AI Pro 🎓</h1>", unsafe_allow_html=True)
    
    tab_work, tab_archive, tab_settings = st.tabs(["📝 בדיקה ומחוון", "📂 ארכיון ציונים", "⚙️ הגדרות"])

    with tab_work:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        col_inputs, col_preview = st.columns([1, 1])
        
        with col_inputs:
            st.markdown("<p class='instruction-text'>שלב 1: בחירת מקצוע ותלמיד</p>", unsafe_allow_html=True)
            subject_active = st.selectbox("**בחר מקצוע:**", SUBJECTS)
            
            if st.session_state.students:
                s_name = st.selectbox("**בחר תלמיד:**", st.session_state.students)
            else:
                s_name = st.text_input("**הקלד שם תלמיד:**")
            
            st.divider()
            
            st.markdown("<p class='instruction-text'>שלב 2: הגדרת מחוון (התשובות הנכונות)</p>", unsafe_allow_html=True)
            rubric_method = st.radio("**איך להזין תשובות?**", ["יצירה עם AI", "העלאת קובץ/תמונה", "הקלדה ידנית"])
            
            if rubric_method == "יצירה עם AI":
                if st.button("✨ צור מחוון אוטומטי (PRO)"):
                    try:
                        model = genai.GenerativeModel('gemini-1.5-pro')
                        res = model.generate_content(f"צור מחוון תשובות מפורט למבחן ב{subject_active}. הפלט חייב להיות בעברית ברורה.")
                        st.session_state.rubric = res.text
                    except Exception as e: st.error(f"שגיאה: {e}")

            elif rubric_method == "העלאת קובץ/תמונה":
                st.markdown("**העלה צילום מחוון (תומך בקבצים גדולים):**")
                rubric_file = st.file_uploader("**בחר קובץ מחוון:**", type=['jpg', 'png', 'jpeg', 'pdf'])
                if rubric_file and st.button("🔍 סרוק מחוון"):
                    try:
                        img_rubric = Image.open(rubric_file)
                        model = genai.GenerativeModel('gemini-1.5-pro')
                        res = model.generate_content(["פענח את המחוון שבתמונה והפוך אותו לטקסט בדיקה:", img_rubric])
                        st.session_state.rubric = res.text
                    except Exception as e: st.error(f"שגיאה בסריקה: {e}")

            st.session_state.rubric = st.text_area("**ערוך את המחוון כאן:**", value=st.session_state.rubric, height=150)

        with col_preview:
            st.markdown("<p class='instruction-text'>שלב 3: העלאת מבחן ובדיקה</p>", unsafe_allow_html=True)
            st.markdown("**העלה את המבחן (כתב יד או מודפס):**")
            up_file = st.file_uploader("**צילום המבחן:**", type=['jpg', 'png', 'jpeg', 'pdf'])
            
            if st.button("🚀 הרץ בדיקה פדגוגית חכמה"):
                if up_file and s_name and st.session_state.rubric:
                    with st.spinner(f"מודל ה-PRO מפענח כתב יד עבור {s_name}..."):
                        try:
                            img_pil = Image.open(up_file)
                            model = genai.GenerativeModel('gemini-1.5-pro')
                            
                            # פרומפט משופר שפותר את בעיית ה"לא מבין"
                            prompt = f"""
                            אתה מורה מקצועי ל{subject_active}. 
                            לפניך תמונה של מבחן של התלמיד/ה {s_name}.
                            המשימה שלך היא לפענח את כתב היד בעברית בצורה מדויקת, גם אם הוא מאתגר.
                            
                            השתמש במחוון הבא כדי לתת ציון: {st.session_state.rubric}
                            
                            נא להחזיר:
                            1. ציון סופי (0-100).
                            2. פירוט התשובות שזוהו והשוואה למחוון.
                            3. משוב אישי ומעודד בעברית.
                            אם יש מילה לא ברורה, נסה להסיק אותה מהקשר המשפט.
                            """
                            
                            res = model.generate_content([prompt, img_pil])
                            st.session_state.current_res = res.text
                            st.session_state.reports.append({
                                "שם": s_name, "שיעור": subject_active, "דוח": res.text, "זמן": datetime.now().strftime("%d/%m/%y %H:%M")
                            })
                        except Exception as e: st.error(f"שגיאה בבדיקה: {e}")
                else: st.warning("**חסרים נתונים: וודא שיש שם, מחוון וקובץ מבחן.**")
            
            if 'current_res' in st.session_state:
                st.markdown("<p class='instruction-text'>תוצאת הבדיקה:</p>", unsafe_allow_html=True)
                st.markdown(f"<div class='result-box'>{st.session_state.current_res}</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with tab_archive:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.markdown("<p class='instruction-text'>ארכיון בדיקות קודמות:</p>", unsafe_allow_html=True)
        filter_sub = st.selectbox("**סנן לפי מקצוע:**", ["הכל"] + SUBJECTS)
        
        display_data = st.session_state.reports if filter_sub == "הכל" else [r for r in st.session_state.reports if r['שיעור'] == filter_sub]
        
        for r in reversed(display_data):
            with st.expander(f"📄 {r['שם']} - {r['שיעור']} ({r['זמן']})"):
                st.markdown(r['דוח'])
        st.markdown("</div>", unsafe_allow_html=True)

    with tab_settings:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.markdown("<p class='instruction-text'>ניהול רשימת תלמידים:</p>", unsafe_allow_html=True)
        names_input = st.text_area("**הזן שמות (מופרדים בפסיק):**", value=", ".join(st.session_state.students))
        if st.button("שמור רשימה"):
            st.session_state.students = [n.strip() for n in names_input.split(",") if n.strip()]
            st.success("הרשימה עודכנה!")
        
        st.divider()
        if st.button("🚪 התנתק"):
            st.session_state.logged_in = False
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
