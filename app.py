import streamlit as st
import google.generativeai as genai
from PIL import Image
import pandas as pd
from datetime import datetime
from handwriting_logic import FCN32s, prepare_image
import torch

# --- הגדרות API ---
MY_API_KEY = "AIzaSyDJdiYe4VmudGKFQzoCI_MmngD26D4wm1Q" 
genai.configure(api_key=MY_API_KEY)

# טעינת המודל מהגיטהאב
@st.cache_resource
def load_hw_model():
    model = FCN32s(n_class=2)
    model.eval()
    return model

hw_model = load_hw_model()

# --- עיצוב דף ---
st.set_page_config(page_title="EduCheck AI Pro", layout="wide")
st.markdown("""
<style>
    .stApp { background: #0f172a; color: white; direction: rtl; text-align: right; }
    .card { background: rgba(30, 41, 59, 0.7); border-radius: 15px; padding: 20px; border: 1px solid #334155; }
    h1, h2 { color: #38bdf8 !important; }
</style>
""", unsafe_allow_html=True)

if 'reports' not in st.session_state: st.session_state.reports = []
if 'rubric' not in st.session_state: st.session_state.rubric = ""

st.title("EduCheck AI - ניהול פדגוגי חכם 🎓")

tab1, tab2 = st.tabs(["🔍 בדיקת מבחן", "📂 ארכיון"])

with tab1:
    col1, col2 = st.columns([1.5, 1])
    
    with col1:
        st.subheader("פרטי התלמיד והמבחן")
        name = st.text_input("שם התלמיד:")
        subject = st.selectbox("מקצוע:", ["תורה", "גמרא", "מדעים", "אנגלית", "אחר"])
        exam_img = st.file_uploader("העלה צילום מבחן", type=['jpg', 'png', 'jpeg'])
        cam_img = st.camera_input("או צלם")

    with col2:
        st.subheader("מחוון (Rubric)")
        chat_in = st.text_input("הנחיה ל-AI ליצירת מחוון:")
        if st.button("עדכן מחוון ✨"):
            model = genai.GenerativeModel('gemini-1.5-flash')
            res = model.generate_content(f"צור מחוון למקצוע {subject}: {chat_in}")
            st.session_state.rubric = res.text
        st.session_state.rubric = st.text_area("המחוון הנוכחי:", value=st.session_state.rubric, height=150)

    if st.button("🚀 הרץ בדיקה חכמה (כולל זיהוי כתב יד)"):
        active = cam_img if cam_img else exam_img
        if active and name:
            with st.spinner("מנתח כתב יד ונותן משוב..."):
                # 1. עיבוד תמונה במודל הגיטהאב (FCN)
                img_pil = Image.open(active)
                input_tensor = prepare_image(img_pil)
                with torch.no_grad():
                    hw_output = hw_model(input_tensor) # המודל מזהה אזורי טקסט
                
                # 2. שליחה ל-Gemini לניתוח סופי
                gemini = genai.GenerativeModel('gemini-1.5-flash')
                prompt = f"נתח את המבחן של {name} ב{subject}. מחוון: {st.session_state.rubric}. פתור את כתב היד ותן ציון מספרי מודגש."
                response = gemini.generate_content([prompt, img_pil])
                
                # שמירה
                st.session_state.reports.append({
                    "שם": name, "ציון": "נבדק", "דוח": response.text, "תאריך": datetime.now().strftime("%d/%m")
                })
                st.markdown(f"<div class='card'>{response.text}</div>", unsafe_allow_html=True)

with tab2:
    st.subheader("ארכיון מבחנים")
    for r in reversed(st.session_state.reports):
        with st.expander(f"{r['שם']} | {r['תאריך']}"):
            st.write(r['דוח'])
