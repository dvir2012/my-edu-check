import streamlit as st
import google.generativeai as genai
from PIL import Image
import io
from datetime import datetime
import os

# --- חיבור ל-API בצורה בטוחה ---
# אל תשאיר את המפתח בקוד! השתמש ב־environment variable
# local: export GEMINI_API_KEY=your-key-here
# Streamlit Cloud: הוסף ב־Secrets
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

if not os.getenv("GEMINI_API_KEY"):
    st.error("חסר מפתח API. הגדר GEMINI_API_KEY בסביבה או ב־Secrets")
    st.stop()

ALLOWED_PASSWORDS = ["dvir2012", "Teacher2012", "Sunset2012", "מורה2012", "Dvir_2012!"]

SUBJECTS = [
    "תורה", "גמרא", "דינים", "היסטוריה", "מדעים", "עברית", "מתמטיקה",
    "אנגלית", "גאוגרפיה", "ספרות", "אזרחות", "של''ח", "תנ''ך", "משנה",
    "הבעה", "ערבית", "פיזיקה", "כימיה", "ביולוגיה", "מחשבת ישראל", "אחר"
]

# ────────────────────────────────────────────────
#  טיפול בתמונות + PDF
# ────────────────────────────────────────────────
def process_image_turbo(upload_file):
    """דחיסה חכמה + תמיכה ב־PDF (דורש pip install pdf2image)"""
    try:
        from pdf2image import convert_from_bytes
    except ImportError:
        st.error("חסר pdf2image → התקן: pip install pdf2image")
        st.stop()

    bytes_data = upload_file.read()
    upload_file.seek(0)

    if upload_file.type == "application/pdf":
        images = convert_from_bytes(bytes_data)
        if not images:
            raise ValueError("קובץ PDF ריק")
        img = images[0]  # לוקחים עמוד ראשון בלבד (אפשר לשפר)
    else:
        img = Image.open(io.BytesIO(bytes_data))

    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")

    img.thumbnail((2000, 2000))
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='JPEG', quality=85)
    img_byte_arr.seek(0)
    return Image.open(img_byte_arr)

# ────────────────────────────────────────────────
#  עיצוב + RTL
# ────────────────────────────────────────────────
st.set_page_config(page_title="EduCheck AI Pro", layout="wide")

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
    .instruction-text {
        color: #ffffff !important;
        font-weight: 900 !important;
        font-size: 1.3rem;
        margin-bottom: 15px;
        text-shadow: 2px 2px 4px #000;
    }
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

# ────────────────────────────────────────────────
#  Session State
# ────────────────────────────────────────────────
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'reports' not in st.session_state:
    st.session_state.reports = []
if 'rubric' not in st.session_state:
    st.session_state.rubric = ""
if 'students' not in st.session_state:
    st.session_state.students = []
if 'current_res' not in st.session_state:
    st.session_state.current_res = None

# ────────────────────────────────────────────────
#  מסך כניסה
# ────────────────────────────────────────────────
if not st.session_state.logged_in:
    _, col, _ = st.columns([1, 1, 1])
    with col:
        st.markdown("<div class='glass-card' style='text-align: center;'>", unsafe_allow_html=True)
        st.markdown("<p class='instruction-text'>נא להזין קוד גישה:</p>", unsafe_allow_html=True)
        pwd = st.text_input("סיסמה:", type="password", key="login_pwd")
        if st.button("התחבר"):
            if pwd in ALLOWED_PASSWORDS:
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("קוד שגוי")
        st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# ────────────────────────────────────────────────
#  המערכת הראשית
# ────────────────────────────────────────────────
st.markdown("<h1 class='main-title'>EduCheck AI Pro 🎓</h1>", unsafe_allow_html=True)

tab_work, tab_archive, tab_settings = st.tabs(["📝 בדיקת מבחן", "📂 ארכיון ציונים", "⚙️ הגדרות כיתה"])

with tab_work:
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    col_inputs, col_preview = st.columns([1, 1])

    with col_inputs:
        st.markdown("<p class='instruction-text'>שלב 1: פרטי המבחן</p>", unsafe_allow_html=True)
        subject_active = st.selectbox("**בחר מקצוע:**", SUBJECTS, key="subject")

        if st.session_state.students:
            s_name = st.selectbox("**בחר תלמיד:**", st.session_state.students, key="student_select")
        else:
            s_name = st.text_input("**הקלד שם תלמיד:**", key="student_text")
            st.info("תוכל להוסיף תלמידים בלשונית 'הגדרות כיתה'")

        st.divider()
        st.markdown("<p class='instruction-text'>שלב 2: הגדרת מחוון תשובות</p>", unsafe_allow_html=True)

        rubric_method = st.radio("**איך להזין תשובות נכונות?**",
                                ["יצירה אוטומטית (AI)", "העלאת קובץ", "הקלדה ידנית"],
                                key="rubric_method")

        if rubric_method == "יצירה אוטומטית (AI)":
            if st.button("✨ צור מחוון (PRO)"):
                with st.spinner("מייצר מחוון..."):
                    try:
                        model = genai.GenerativeModel('gemini-1.5-pro')
                        res = model.generate_content(f"צור מחוון הערכה מפורט ומקצועי למבחן בכיתה ז'-י" + 
                                                     f"במקצוע {subject_active}. כתוב בעברית בלבד.")
                        st.session_state.rubric = res.text
                        st.success("נוצר מחוון!")
                    except Exception as e:
                        st.error(f"שגיאה: {e}")

        elif rubric_method == "העלאת קובץ":
            rubric_file = st.file_uploader("**העלה צילום/סריקה של המחוון:**", 
                                          type=['jpg','png','jpeg','pdf'], key="rubric_upload")
            if rubric_file and st.button("🔍 סרוק מחוון"):
                with st.spinner("מפענח את המחוון..."):
                    try:
                        img_rubric = process_image_turbo(rubric_file)
                        model = genai.GenerativeModel('gemini-1.5-pro')
                        res = model.generate_content(["תמלל בדיוק את כל הטקסט שבתמונה (מחוון הערכה):", img_rubric])
                        st.session_state.rubric = res.text
                        st.success("המחוון נסרק!")
                    except Exception as e:
                        st.error(f"שגיאה בסריקה: {e}")

        st.session_state.rubric = st.text_area("**תוכן המחוון לבדיקה:**",
                                              value=st.session_state.rubric,
                                              height=180, key="rubric_edit")

    with col_preview:
        st.markdown("<p class='instruction-text'>שלב 3: העלאה ובדיקה</p>", unsafe_allow_html=True)
        up_file = st.file_uploader("**העלה צילום המבחן (כתב יד)**", 
                                  type=['jpg','png','jpeg','pdf'], key="exam_upload")

        if st.button("🚀 הרץ בדיקה פדגוגית"):
            if not (up_file and s_name and st.session_state.rubric.strip()):
                st.warning("חסרים נתונים: תמונה + שם תלמיד + מחוון")
            else:
                with st.spinner(f"מעבד כתב יד עבור {s_name}..."):
                    try:
                        final_img = process_image_turbo(up_file)

                        prompt = f"""
אתה מורה ישראלי מנוסה מאוד. לפניך צילום מבחן בכתב יד בעברית של התלמיד/ה {s_name} במקצוע {subject_active}.

פענח את הכתב יד בצורה המדויקת ביותר האפשרית – גם אם חלק מהאותיות לא ברורות.
השתמש **רק** במחוון הבא:

{st.session_state.rubric}

מבנה התשובה חובה (בעברית בלבד):
1. ציון סופי: XX/100
2. פירוט לפי שאלות:
   • מספר שאלה | תשובת התלמיד (תמלול קצר) | נקודות שקיבל | הסבר קצר מדוע
3. משוב מחזק ומעודד (2–4 משפטים)
4. הצעות לשיפור (אם יש צורך)

אל תמציא תשובות. כתוב רק על סמך מה שרואים בתמונה.
"""

                        model = genai.GenerativeModel('gemini-1.5-pro')
                        res = model.generate_content([prompt, final_img])

                        st.session_state.current_res = res.text
                        st.session_state.reports.append({
                            "שם": s_name,
                            "שיעור": subject_active,
                            "דוח": res.text,
                            "זמן": datetime.now().strftime("%d/%m/%y %H:%M")
                        })
                        st.rerun()

                    except Exception as e:
                        st.error(f"שגיאה בעיבוד: {str(e)}")

        if st.session_state.current_res:
            st.markdown("<p class='instruction-text'>תוצאת הבדיקה:</p>", unsafe_allow_html=True)
            st.markdown(f"<div class='result-box'>{st.session_state.current_res}</div>", unsafe_allow_html=True)

            st.download_button(
                label="⬇️ הורד דוח כטקסט",
                data=st.session_state.current_res,
                file_name=f"דוח_{s_name.replace(' ','_')}_{subject_active}.txt",
                mime="text/plain"
            )

    st.markdown("</div>", unsafe_allow_html=True)

with tab_archive:
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    st.markdown("<p class='instruction-text'>ארכיון ציונים:</p>", unsafe_allow_html=True)

    if not st.session_state.reports:
        st.info("עדיין אין דוחות שנשמרו")
    else:
        for r in reversed(st.session_state.reports):
            with st.expander(f"📄 {r['שם']} – {r['שיעור']} ({r['זמן']})"):
                st.markdown(r['דוח'])
    st.markdown("</div>", unsafe_allow_html=True)

with tab_settings:
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    st.markdown("<p class='instruction-text'>ניהול רשימת כיתה:</p>", unsafe_allow_html=True)

    names_input = st.text_area("**שמות תלמידים (מופרדים בפסיק):**",
                              value=", ".join(st.session_state.students),
                              height=120, key="students_input")

    if st.button("💾 שמור רשימת תלמידים"):
        st.session_state.students = [n.strip() for n in names_input.split(",") if n.strip()]
        st.success(f"נשמרו {len(st.session_state.students)} תלמידים!")

    st.divider()
    if st.button("🚪 התנתק"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)
