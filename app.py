import streamlit as st
import google.generativeai as genai
from PIL import Image
import io
import pandas as pd
from datetime import datetime

# --- 1. הגדרות API וחיבור למודל PRO ---
genai.configure(api_key="AIzaSyDJdiYe4VmudGKFQzoCI_MmngD26D4wm1Q")

ALLOWED_PASSWORDS = ["dvir2012", "Teacher2012", "Sunset2012", "מורה2012", "Dvir_2012!"]

SUBJECTS = [
    "תורה", "גמרא", "דינים", "היסטוריה", "מדעים", "עברית", "מתמטיקה", 
    "אנגלית", "גאוגרפיה", "ספרות", "אזרחות", "של''ח", "תנ''ך", "משנה",
    "הבעה", "ערבית", "פיזיקה", "כימיה", "ביולוגיה", "מחשבת ישראל", "אחר"
]

# --- 2. פונקציית Turbo להאצת העלאה ---
def process_image_turbo(upload_file):
    """מבצע דחיסה חכמה לתמונה כדי לשלוח אותה ל-AI במהירות שיא"""
    img = Image.open(upload_file)
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")
    
    # הקטנה לרזולוציה אופטימלית לזיהוי כתב יד מבלי להכביד
    img.thumbnail((2000, 2000)) 
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='JPEG', quality=85)
    return Image.open(img_byte_arr)

# --- 3. עיצוב הממשק (CSS) - הכל מודגש בלבן ---
st.set_page_config(page_title="EduCheck AI Pro - Full Version", layout="wide")

st.markdown("""
<style>
    .stApp { background: #0f172a; color: white; direction: rtl; text-align: right; }
    
    .glass-card { 
        background: rgba(30, 41, 49, 0.7); 
        border: 1px solid #38bdf8; 
        border-radius: 15px; 
        padding: 25px; 
        margin-top: 10px;
    }
    
    /* הוראות מודגשות בלבן בוהק */
    .instruction-text { 
        color: #ffffff !important; 
        font-weight: 900 !important; 
        font-size: 1.3rem; 
        margin-bottom: 15px;
        text-shadow: 2px 2px 4px #000000;
        display: block;
    }
    
    /* הפיכת כל הלייבלים והטקסטים ללבן מודגש */
    label, .stMarkdown p, .stRadio label { 
        color: #ffffff !important; 
        font-weight: 800 !important; 
        font-size: 1.15rem !important;
    }
    
    .main-title { 
        font-size: 2.8rem; font-weight: 800; text-align: center;
        background: linear-gradient(90deg, #38bdf8, #818cf8);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
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
    }
</style>
""", unsafe_allow_html=True)

# אתחול Session State
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'reports' not in st.session_state: st.session_state.reports = []
if 'rubric' not in st.session_state: st.session_state.rubric = ""
if 'students' not in st.session_state: st.session_state.students = []

# --- 4. מסך כניסה ---
if not st.session_state.logged_in:
    _, col, _ = st.columns([1, 1, 1])
    with col:
        st.markdown("<div class='glass-card' style='text-align: center;'>", unsafe_allow_html=True)
        st.markdown("<p class='instruction-text'>נא להזין קוד גישה:</p>", unsafe_allow_html=True)
        pwd = st.text_input("סיסמה:", type="password")
        if st.button("התחבר"):
            if pwd in ALLOWED_PASSWORDS:
                st.session_state.logged_in = True
                st.rerun()
            else: st.error("קוד שגוי")
        st.markdown("</div>", unsafe_allow_html=True)

# --- 5. המערכת המרכזית ---
else:
    st.markdown("<h1 class='main-title'>EduCheck AI Pro 🎓</h1>", unsafe_allow_html=True)
    
    tab_work, tab_archive, tab_settings = st.tabs(["📝 בדיקת מבחן", "📂 ארכיון ציונים", "⚙️ הגדרות כיתה"])

    with tab_work:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        col_inputs, col_preview = st.columns([1, 1])
        
        with col_inputs:
            st.markdown("<p class='instruction-text'>שלב 1: פרטי המבחן</p>", unsafe_allow_html=True)
            subject_active = st.selectbox("**בחר מקצוע:**", SUBJECTS)
            
            if st.session_state.students:
                s_name = st.selectbox("**בחר תלמיד:**", st.session_state.students)
            else:
                s_name = st.text_input("**הקלד שם תלמיד:**")
            
            st.divider()
            
            st.markdown("<p class='instruction-text'>שלב 2: הגדרת מחוון תשובות</p>", unsafe_allow_html=True)
            rubric_method = st.radio("**איך להזין תשובות נכונות?**", ["יצירה אוטומטית (AI)", "העלאת קובץ", "הקלדה ידנית"])
            
            if rubric_method == "יצירה אוטומטית (AI)":
                if st.button("✨ צור מחוון (PRO)"):
                    try:
                        model = genai.GenerativeModel('gemini-1.5-pro')
                        res = model.generate_content(f"צור מחוון מפורט למבחן ב{subject_active}")
                        st.session_state.rubric = res.text
                    except Exception as e: st.error(f"שגיאה: {e}")

            elif rubric_method == "העלאת קובץ":
                rubric_file = st.file_uploader("**העלה צילום תשובות:**", type=['jpg', 'png', 'pdf'])
                if rubric_file and st.button("🔍 סרוק מחוון"):
                    try:
                        img_rubric = process_image_turbo(rubric_file)
                        model = genai.GenerativeModel('gemini-1.5-pro')
                        res = model.generate_content(["תמלל את המחוון שבתמונה:", img_rubric])
                        st.session_state.rubric = res.text
                    except Exception as e: st.error(f"שגיאה: {e}")

            st.session_state.rubric = st.text_area("**תוכן המחוון לבדיקה:**", value=st.session_state.rubric, height=150)

        with col_preview:
            st.markdown("<p class='instruction-text'>שלב 3: העלאה ובדיקת המבחן</p>", unsafe_allow_html=True)
            up_file = st.file_uploader("**העלה את צילום המבחן (כתב יד):**", type=['jpg', 'png', 'jpeg', 'pdf'])
            
            if st.button("🚀 הרץ בדיקה פדגוגית מהירה"):
                if up_file and s_name and st.session_state.rubric:
                    with st.spinner(f"מעבד ומפענח כתב יד עבור {s_name}..."):
                        try:
                            # האצת העלאה
                            final_img = process_image_turbo(up_file)
                            
                            model = genai.GenerativeModel('gemini-1.5-pro')
                            prompt = f"""
                            אתה מורה מקצועי. נתח את המבחן ב{subject_active} של {s_name}.
                            השתמש במחוון: {st.session_state.rubric}.
                            עליך לפענח כתב יד בעברית בצורה מדויקת.
                            ספק ציון סופי, פירוט תשובות ומשוב מחזק.
                            """
                            
                            res = model.generate_content([prompt, final_img])
                            st.session_state.current_res = res.text
                            st.session_state.reports.append({
                                "שם": s_name, "שיעור": subject_active, "דוח": res.text, "זמן": datetime.now().strftime("%d/%m/%y %H:%M")
                            })
                        except Exception as e: st.error(f"שגיאה: {e}")
                else: st.warning("**חסרים נתונים להרצת הבדיקה!**")
            
            if 'current_res' in st.session_state:
                st.markdown("<p class='instruction-text'>תוצאת הבדיקה:</p>", unsafe_allow_html=True)
                st.markdown(f"<div class='result-box'>{st.session_state.current_res}</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with tab_archive:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.markdown("<p class='instruction-text'>ארכיון ציונים:</p>", unsafe_allow_html=True)
        for r in reversed(st.session_state.reports):
            with st.expander(f"📄 {r['שם']} - {r['שיעור']} ({r['זמן']})"):
                st.markdown(r['דוח'])
        st.markdown("</div>", unsafe_allow_html=True)

    with tab_settings:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.markdown("<p class='instruction-text'>ניהול רשימת כיתה:</p>", unsafe_allow_html=True)
        names_input = st.text_area("**הזן שמות תלמידים (מופרדים בפסיק):**", value=", ".join(st.session_state.students))
        if st.button("💾 שמור רשימה"):
            st.session_state.students = [n.strip() for n in names_input.split(",") if n.strip()]
            st.success("הרשימה עודכנה!")
        
        st.divider()
        if st.button("🚪 התנתק"):
            st.session_state.logged_in = False
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
