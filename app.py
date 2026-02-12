import streamlit as st
import google.generativeai as genai
from PIL import Image
import pandas as pd
from datetime import datetime
import torch
import numpy as np
import io

# ייבוא הלוגיקה של המודל מהקובץ השני
from handwriting_logic import FCN32s, prepare_image

# --- 1. הגדרות API ורשימת 10 הסיסמאות המורשות ---
MY_API_KEY = "AIzaSyDJdiYe4VmudGKFQzoCI_MmngD26D4wm1Q" 
genai.configure(api_key=MY_API_KEY)

# רשימת 10 הסיסמאות שביקשת
ALLOWED_PASSWORDS = [
    "dvir2012", "Teacher2012", "Sunset2012", "מורה2012", "Dvir_2012!",
    "2012EduCheck", "D2012V", "D@2012", "Dvir2012Pro", "Gold2012"
]

# --- 2. טעינת מודל ה-AI (FCN) ---
@st.cache_resource
def load_handwriting_model():
    model = FCN32s(n_class=2) 
    model.eval()
    return model

hw_model = load_handwriting_model()

# --- 3. עיצוב הממשק (UI) ---
st.set_page_config(page_title="EduCheck AI Pro", layout="wide")

st.markdown("""
<style>
    .stApp { background: #0f172a; color: #f8fafc; direction: rtl; text-align: right; }
    .glass-card { background: rgba(30, 41, 59, 0.7); border: 1px solid #38bdf8; border-radius: 15px; padding: 25px; margin-bottom: 20px; }
    .main-title { font-size: 2.5rem; font-weight: 800; color: #38bdf8; text-align: center; }
</style>
""", unsafe_allow_html=True)

# --- 4. ניהול מצב המערכת ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'reports' not in st.session_state: st.session_state.reports = []
if 'rubric' not in st.session_state: st.session_state.rubric = ""

# --- 5. מסך כניסה (עם בדיקת 10 הסיסמאות) ---
if not st.session_state.logged_in:
    st.markdown("<div style='height: 20vh;'></div>", unsafe_allow_html=True)
    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        st.markdown("<div class='glass-card' style='text-align: center;'>", unsafe_allow_html=True)
        st.markdown("<h2>כניסת מורה מורשה</h2>", unsafe_allow_html=True)
        pwd = st.text_input("הזן קוד גישה:", type="password")
        if st.button("התחבר"):
            if pwd in ALLOWED_PASSWORDS:
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("קוד גישה לא מוכר. הגישה נחסמה.")
        st.markdown("</div>", unsafe_allow_html=True)

# --- 6. הממשק המרכזי (לאחר התחברות) ---
else:
    st.markdown("<h1 class='main-title'>EduCheck AI Pro</h1>", unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["🔍 בדיקת מבחן", "📊 ארכיון", "⚙️ מחוון"])

    with tab3: # הגדרות מחוון
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        subj = st.selectbox("מקצוע:", ["תורה", "גמרא", "מדעים", "עברית", "אחר"])
        if st.button("ייצר מחוון אוטומטי"):
            model = genai.GenerativeModel('gemini-1.5-flash')
            res = model.generate_content(f"צור מחוון למבחן ב{subj}")
            st.session_state.rubric = res.text
        st.session_state.rubric = st.text_area("טקסט המחוון:", value=st.session_state.rubric, height=200)
        st.markdown("</div>", unsafe_allow_html=True)

    with tab1: # בדיקת מבחן
        col_r, col_l = st.columns([1.5, 1])
        with col_r:
            st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
            s_name = st.text_input("שם התלמיד:")
            up_file = st.file_uploader("העלה תמונה:", type=['jpg', 'png'])
            cam_file = st.camera_input("צילום")
            st.markdown("</div>", unsafe_allow_html=True)

        with col_l:
            st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
            active_img = cam_file if cam_file else up_file
            if st.button("🚀 הרץ בדיקה"):
                if active_img and s_name:
                    with st.spinner("מנתח..."):
                        img_pil = Image.open(active_img)
                        # שימוש במודל ה-FCN מהגיטהאב
                        input_tensor = prepare_image(img_pil)
                        with torch.no_grad():
                            _ = hw_model(input_tensor)
                        
                        # ניתוח Gemini
                        gemini = genai.GenerativeModel('gemini-1.5-flash')
                        res = gemini.generate_content([f"נתח מבחן ב{subj} עבור {s_name}. מחוון: {st.session_state.rubric}", img_pil])
                        
                        st.session_state.reports.append({"שם": s_name, "דוח": res.text, "תאריך": datetime.now().strftime("%d/%m")})
                        st.markdown(res.text)
                else: st.error("חסרים נתונים")
            st.markdown("</div>", unsafe_allow_html=True)

    with tab2: # ארכיון
        for r in reversed(st.session_state.reports):
            with st.expander(f"{r['שם']} - {r['תאריך']}"):
                st.write(r['דוח'])

    if st.sidebar.button("התנתק"):
        st.session_state.logged_in = False
        st.rerun()
