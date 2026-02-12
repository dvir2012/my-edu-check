import streamlit as st
import google.generativeai as genai
from PIL import Image
import pandas as pd
from datetime import datetime
import torch
import numpy as np
import io

# ייבוא הלוגיקה של המודל מהקובץ השני שיצרנו
from handwriting_logic import FCN32s, prepare_image

# --- 1. הגדרות אבטחה ו-API ---
MY_API_KEY = "AIzaSyDJdiYe4VmudGKFQzoCI_MmngD26D4wm1Q" 
genai.configure(api_key=MY_API_KEY)

ALLOWED_PASSWORDS = ["dvir2012", "Teacher2012", "מורה2012"]

# --- 2. טעינת מודל ה-AI (FCN) לזיכרון ---
@st.cache_resource
def load_handwriting_model():
    # יצירת המבנה וטעינה למצב הערכה
    model = FCN32s(n_class=2) 
    # הערה: אם יהיה לנו קובץ משקולות (weights.pth), נטען אותו כאן
    model.eval()
    return model

hw_model = load_handwriting_model()

# --- 3. עיצוב הממשק (UI Customization) ---
st.set_page_config(page_title="EduCheck AI Pro", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
    .stApp {
        background: radial-gradient(circle at center, #1e293b, #0f172a);
        color: #f8fafc;
        direction: rtl;
        text-align: right;
    }
    .glass-card {
        background: rgba(30, 41, 59, 0.7);
        border: 1px solid rgba(56, 189, 248, 0.3);
        border-radius: 20px;
        padding: 25px;
        margin-bottom: 20px;
    }
    .main-title {
        font-size: 3rem;
        font-weight: 800;
        background: linear-gradient(90deg, #38bdf8, #818cf8);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
    }
    .stButton>button {
        background: linear-gradient(135deg, #38bdf8 0%, #1d4ed8 100%);
        color: white !important;
        border: none; border-radius: 12px;
        padding: 12px 24px; font-weight: 700; width: 100%;
    }
</style>
""", unsafe_allow_html=True)

# --- 4. ניהול מצב המערכת (Session State) ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'reports' not in st.session_state: st.session_state.reports = []
if 'rubric' not in st.session_state: st.session_state.rubric = ""

# --- 5. מסך כניסה ---
if not st.session_state.logged_in:
    st.markdown("<div style='height: 20vh;'></div>", unsafe_allow_html=True)
    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        st.markdown("<div class='glass-card' style='text-align: center;'>", unsafe_allow_html=True)
        st.markdown("<h1 style='color: white;'>כניסת מורים</h1>", unsafe_allow_html=True)
        pwd = st.text_input("קוד גישה:", type="password")
        if st.button("התחבר"):
            if pwd in ALLOWED_PASSWORDS:
                st.session_state.logged_in = True
                st.rerun()
            else: st.error("קוד שגוי")
        st.markdown("</div>", unsafe_allow_html=True)

# --- 6. המערכת המרכזית ---
else:
    st.markdown("<h1 class='main-title'>EduCheck AI Pro</h1>", unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["🔍 בדיקה חכמה", "📊 ארכיון ודוחות", "⚙️ הגדרות מחוון"])

    # --- טאב הגדרות מחוון ---
    with tab3:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.subheader("עריכת מחוון (Rubric)")
        subj = st.selectbox("בחר מקצוע:", ["תורה", "נביא", "גמרא", "משנה", "מדעים", "עברית", "אחר"])
        instructions = st.text_area("הוראות מיוחדות (למשל: דגש על הבנה ולא רק ציטוט):")
        
        if st.button("ייצר מחוון בסיסי עם AI"):
            with st.spinner("יוצר..."):
                model = genai.GenerativeModel('gemini-1.5-flash')
                res = model.generate_content(f"צור מחוון מפורט למבחן ב{subj}. הנחיות: {instructions}")
                st.session_state.rubric = res.text
        
        st.session_state.rubric = st.text_area("טקסט המחוון הסופי:", value=st.session_state.rubric, height=200)
        st.markdown("</div>", unsafe_allow_html=True)

    # --- טאב בדיקה ---
    with tab1:
        col_r, col_l = st.columns([1.5, 1])
        
        with col_r:
            st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
            st.subheader("פרטי התלמיד")
            s_name = st.text_input("שם התלמיד:")
            s_class = st.text_input("כיתה:")
            
            st.divider()
            st.subheader("העלאת המבחן")
            up_file = st.file_uploader("בחר קובץ תמונה:", type=['jpg', 'jpeg', 'png'])
            cam_file = st.camera_input("צילום מהיר")
            st.markdown("</div>", unsafe_allow_html=True)

        with col_l:
            st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
            st.subheader("סטטוס וניתוח")
            active_img = cam_file if cam_file else up_file
            
            if st.button("🚀 הרץ בדיקה פדגוגית"):
                if active_img and s_name:
                    with st.spinner("מנתח כתב יד ונותן משוב..."):
                        # א. עיבוד תמונה במודל ה-FCN (מהקובץ השני)
                        img_pil = Image.open(active_img)
                        input_tensor = prepare_image(img_pil)
                        
                        # הפעלת המודל המקומי
                        with torch.no_grad():
                            hw_features = hw_model(input_tensor)
                        
                        # ב. ניתוח באמצעות Gemini
                        gemini_model = genai.GenerativeModel('gemini-1.5-flash')
                        prompt = f"""
                        אתה מורה מקצועי. נתח את המבחן המצורף של התלמיד {s_name} במקצוע {subj}.
                        המחוון לבדיקה: {st.session_state.rubric}
                        שים לב: הטקסט הוא כתב יד עברי. פענח אותו בזהירות.
                        תן ציון סופי מספרי מודגש בראש הדוח, ולאחר מכן פירוט נקודות חוזק ושיפור.
                        """
                        response = gemini_model.generate_content([prompt, img_pil])
                        
                        # ג. שמירה
                        report = {
                            "תאריך": datetime.now().strftime("%d/%m/%Y %H:%M"),
                            "שם": s_name, "כיתה": s_class, "מקצוע": subj,
                            "דוח": response.text
                        }
                        st.session_state.reports.append(report)
                        st.success("הבדיקה הושלמה!")
                        st.markdown(f"<div style='background: #1e293b; padding: 15px; border-radius: 10px; border-right: 5px solid #38bdf8;'>{response.text}</div>", unsafe_allow_html=True)
                else:
                    st.error("אנא מלא שם תלמיד והעלה תמונה.")
            st.markdown("</div>", unsafe_allow_html=True)

    # --- טאב ארכיון ---
    with tab2:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        if st.session_state.reports:
            df = pd.DataFrame(st.session_state.reports)
            st.subheader("היסטוריית בדיקות")
            
            for i, r in enumerate(reversed(st.session_state.reports)):
                with st.expander(f"📄 {r['שם']} - {r['מקצוע']} ({r['תאריך']})"):
                    st.markdown(r['דוח'])
            
            # אפשרות להורדה
            csv = df.to_csv(index=False).encode('utf-8-sig')
            st.download_button("📥 הורד את כל הנתונים לאקסל", csv, "educheck_reports.csv", "text/csv")
        else:
            st.info("עדיין אין דוחות בארכיון.")
        st.markdown("</div>", unsafe_allow_html=True)

    # כפתור התנתקות בסרגל הצד
    if st.sidebar.button("התנתק 🚪"):
        st.session_state.logged_in = False
        st.rerun()
