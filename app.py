import streamlit as st
import google.generativeai as genai
from PIL import Image
import pandas as pd

# --- 1. הגדרות API ---
# הערה: אם המפתח לא עובד, בדוק אם אין בו רווחים מיותרים
MY_API_KEY = "AIzaSyDJdiYe4VmudGKFQzoCI_MmngD26D4wm1Q" 
genai.configure(api_key=MY_API_KEY)

# --- 2. עיצוב הממשק (שילוב בהיר-כהה) ---
st.set_page_config(page_title="EduCheck AI PRO", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #f8fafc; direction: rtl; text-align: right; }
    .main-header { 
        background: #1e293b; color: white; padding: 1.5rem; 
        border-radius: 15px; text-align: center; margin-bottom: 2rem;
    }
    .stTextArea textarea, .stTextInput input {
        background-color: #ffffff !important; color: #1e293b !important;
        border: 1px solid #cbd5e1 !important; border-radius: 8px !important;
    }
    .stButton>button {
        background: linear-gradient(90deg, #2563eb, #7c3aed);
        color: white; border: none; border-radius: 10px;
        font-weight: bold; width: 100%; height: 3rem;
    }
    .status-box { background: #e2e8f0; padding: 10px; border-radius: 10px; margin-bottom: 10px; }
</style>
""", unsafe_allow_html=True)

# --- 3. לוגיקה ותוכן ---
st.markdown("<div class='main-header'><h1>EduCheck AI PRO 🧠</h1></div>", unsafe_allow_html=True)

tab1, tab2 = st.tabs(["🔍 בדיקת מבחן", "📝 דף תרגול א-ת"])

with tab1:
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("📝 פרטי המבחן")
        student_name = st.text_input("שם התלמיד:", placeholder="הכנס שם...")
        rubric = st.text_area("מחוון תשובות (מה התשובה הנכונה?):", height=150)

    with col2:
        st.subheader("📸 העלאת המבחן")
        img_file = st.file_uploader("העלה תמונה", type=['png', 'jpg', 'jpeg'])
        camera_img = st.camera_input("או צלם")

    final_img = camera_img if camera_img else img_file

    if st.button("בדוק מבחן ונתן ציון ⚡"):
        if final_img and student_name:
            with st.spinner("ה-AI מנתח..."):
                try:
                    img = Image.open(final_img)
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    prompt = f"נתח את המבחן של {student_name} לפי המחוון: {rubric}. תמלל תשובות, תן ציון ומשוב בעברית."
                    response = model.generate_content([prompt, img])
                    
                    st.markdown("### 🏁 תוצאות הבדיקה:")
                    st.info(response.text)
                except Exception as e:
                    st.error("ה-API של גוגל לא זמין כרגע, בדוק את מפתח ה-API שלך.")
        else:
            st.warning("נא למלא את כל השדות ולהעלות תמונה.")

with tab2:
    st.subheader("דף איסוף כתב יד להדפסה")
    st.write("הדפס את המשבצות הבאות:")
    letters = ['א','ב','ג','ד','ה','ו','ז','ח','ט','י','כ','ך','ל','מ','ם','נ','ן','ס','ע','פ','ף','צ','ץ','ק','ר','ש','ת']
    
    # תצוגה של רשת משבצות
    grid = st.columns(4)
    for i, l in enumerate(letters):
        grid[i % 4].markdown(f"""
            <div style="border: 2px solid #334155; padding: 20px; text-align: center; margin-bottom: 10px; background: white; color: black; font-size: 20px;">
                {l} = 
            </div>
        """, unsafe_allow_html=True)
