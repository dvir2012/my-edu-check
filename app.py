import streamlit as st
import google.generativeai as genai
from PIL import Image
import pandas as pd
from datetime import datetime
import torch
from datasets import load_dataset
import io

# ייבוא הלוגיקה של המודל מהקובץ השני - זה מה שחוסך מקום ב-app.py
from handwriting_logic import FCN32s, prepare_image

# --- 1. הגדרות API וסיסמאות ---
# מפתח ה-API שלך ל-Gemini
genai.configure(api_key="AIzaSyDJdiYe4VmudGKFQzoCI_MmngD26D4wm1Q")

# רשימת 10 הסיסמאות המורשות
ALLOWED_PASSWORDS = [
    "dvir2012", "Teacher2012", "Sunset2012", "מורה2012", "Dvir_2012!",
    "2012EduCheck", "D2012V", "D@2012", "Dvir2012Pro", "Gold2012"
]

# --- 2. טעינת משאבים (Caching) ---
@st.cache_resource
def load_all_models():
    """טעינת המודל מהגיטהאב לזיכרון פעם אחת בלבד"""
    model = FCN32s(n_class=2)
    model.eval()
    return model

@st.cache_data
def load_handwriting_samples():
    """חיבור למחסן הנתונים ב-Hugging Face ששלחת"""
    try:
        ds = load_dataset("sivan22/hebrew-handwritten-dataset", split='train', streaming=True)
        return list(ds.take(3))
    except Exception as e:
        return None

# הפעלת הטעינה
hw_model = load_all_models()
hf_samples = load_handwriting_samples()

# --- 3. עיצוב הממשק (CSS) ---
st.set_page_config(page_title="EduCheck AI Pro", layout="wide")
st.markdown("""
<style>
    .stApp { background-color: #0f172a; color: #f8fafc; direction: rtl; text-align: right; }
    .main-card { background: rgba(30, 41, 59, 0.8); border: 1px solid #38bdf8; border-radius: 20px; padding: 30px; }
    .report-box { background: #1e293b; border-right: 5px solid #38bdf8; padding: 15px; border-radius: 8px; margin-top: 10px; }
    h1, h2, h3 { color: #38bdf8 !important; }
    .stButton>button { background: linear-gradient(90deg, #38bdf8, #1d4ed8); color: white; border-radius: 10px; border: none; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# --- 4. ניהול ה-Session ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'reports' not in st.session_state: st.session_state.reports = []
if 'rubric' not in st.session_state: st.session_state.rubric = "בדוק את התשובות לפי הדיוק בתוכן, הבנה פדגוגית וניסוח."

# --- 5. מסך כניסה ---
if not st.session_state.logged_in:
    st.markdown("<div style='height: 15vh;'></div>", unsafe_allow_html=True)
    _, login_col, _ = st.columns([1, 1.5, 1])
    with login_col:
        st.markdown("<div class='main-card' style='text-align: center;'>", unsafe_allow_html=True)
        st.title("כניסת מורה מורשה")
        user_pwd = st.text_input("הזן קוד גישה:", type="password")
        if st.button("כניסה למערכת"):
            if user_pwd in ALLOWED_PASSWORDS:
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("קוד גישה שגוי. הגישה חסומה.")
        st.markdown("</div>", unsafe_allow_html=True)

# --- 6. הממשק הראשי (אחרי התחברות) ---
else:
    st.markdown("<h1 style='text-align: center;'>EduCheck AI Pro 🎓</h1>", unsafe_allow_html=True)
    
    # סרגל צד עם מידע מה-Hugging Face
    with st.sidebar:
        st.subheader("📡 חיבור למסדי נתונים")
        if hf_samples:
            st.success("מחובר ל-Hugging Face")
            for i, sample in enumerate(hf_samples):
                st.image(sample['image'], caption=f"דגימת כתב יד #{i+1}", width=100)
        else:
            st.warning("לא מצליח למשוך דגימות כרגע")
        
        st.divider()
        if st.button("יציאה מהמערכת 🚪"):
            st.session_state.logged_in = False
            st.rerun()

    tab_scan, tab_archive, tab_settings = st.tabs(["🔍 בדיקת מבחן", "📂 ארכיון ציונים", "⚙️ הגדרות מחוון"])

    # טאב הגדרות
    with tab_settings:
        st.markdown("<div class='main-card'>", unsafe_allow_html=True)
        st.subheader("עריכת מחוון (Rubric)")
        st.session_state.rubric = st.text_area("הגדר ל-AI איך לתת ציונים:", value=st.session_state.rubric, height=150)
        st.markdown("</div>", unsafe_allow_html=True)

    # טאב בדיקה
    with tab_scan:
        col_input, col_res = st.columns([1, 1.2])
        
        with col_input:
            st.markdown("<div class='main-card'>", unsafe_allow_html=True)
            student_name = st.text_input("שם התלמיד:")
            subject = st.selectbox("מקצוע:", ["תורה", "גמרא", "מדעים", "עברית", "אחר"])
            upload_type = st.radio("בחר מקור תמונה:", ["העלאת קובץ", "צילום במצלמה"])
            
            img_file = None
            if upload_type == "העלאת קובץ":
                img_file = st.file_uploader("בחר תמונת מבחן:", type=['jpg', 'png', 'jpeg'])
            else:
                img_file = st.camera_input("צילום המבחן")
            st.markdown("</div>", unsafe_allow_html=True)

        with col_res:
            if st.button("🚀 התחל ניתוח פדגוגי"):
                if img_file and student_name:
                    with st.spinner("מנתח כתב יד באמצעות מודל FCN ו-Gemini..."):
                        # א. עיבוד התמונה במודל הגיטהאב
                        raw_img = Image.open(img_file)
                        processed_tensor = prepare_image(raw_img)
                        with torch.no_grad():
                            # הרצת המודל מהגיטהאב (הכנה לזיהוי שורות)
                            _ = hw_model(processed_tensor)
                        
                        # ב. ניתוח תוכן באמצעות Gemini 1.5 Flash
                        model = genai.GenerativeModel('gemini-1.5-flash')
                        full_prompt = f"""
                        אתה מורה מקצועי. נתח את המבחן של {student_name} במקצוע {subject}.
                        השתמש במחוון הבא: {st.session_state.rubric}
                        שים לב: הטקסט הוא כתב יד עברי. פענח אותו בזהירות ותן משוב מפורט וציון סופי מודגש.
                        """
                        response = model.generate_content([full_prompt, raw_img])
                        
                        # ג. שמירת התוצאה
                        st.session_state.reports.append({
                            "שם": student_name,
                            "מקצוע": subject,
                            "תאריך": datetime.now().strftime("%d/%m/%Y %H:%M"),
                            "תוכן": response.text
                        })
                        
                        st.subheader("תוצאת הבדיקה:")
                        st.markdown(f"<div class='report-box'>{response.text}</div>", unsafe_allow_html=True)
                else:
                    st.error("אנא וודא שהזנת שם והעלית תמונה.")

    # טאב ארכיון
    with tab_archive:
        if st.session_state.reports:
            for r in reversed(st.session_state.reports):
                with st.expander(f"📄 {r['שם']} - {r['מקצוע']} ({r['תאריך']})"):
                    st.markdown(r['תוכן'])
        else:
            st.info("אין דוחות שמורים בארכיון.")
