import streamlit as st
import google.generativeai as genai
from PIL import Image
import pandas as pd
from datetime import datetime

# --- 1. הגדרות אבטחה ו-API ---
MY_API_KEY = "AIzaSyDJdiYe4VmudGKFQzoCI_MmngD26D4wm1Q" 
SECRET_WORD = "dvir2012" 
genai.configure(api_key=MY_API_KEY)

# --- 2. עיצוב שקיעה עמוקה ---
st.set_page_config(page_title="EduCheck PRO", layout="wide")

st.markdown("""
<style>
    [data-testid="stAppViewContainer"] {
        background: linear-gradient(180deg, #42275a 0%, #734b6d 50%, #ba5370 100%);
        direction: rtl; text-align: right;
    }
    .glass-card {
        background: rgba(255, 255, 255, 0.12);
        backdrop-filter: blur(15px);
        border-radius: 20px; padding: 25px; margin-bottom: 20px; color: white;
    }
    .stTextArea textarea { background-color: white !important; color: black !important; }
    .stTextInput input { background-color: white !important; color: black !important; }
    .stButton>button {
        background: linear-gradient(90deg, #ff512f 0%, #dd2476 100%);
        color: white; border-radius: 12px; font-weight: 700; width: 100%;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. ניהול מצב (Session State) ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'reports' not in st.session_state: st.session_state.reports = []
if 'temp_rubric' not in st.session_state: st.session_state.temp_rubric = ""

# --- 4. מסך כניסה ---
if not st.session_state.logged_in:
    st.markdown("<div style='height: 20vh;'></div>", unsafe_allow_html=True)
    cols = st.columns([1, 1.5, 1])
    with cols[1]:
        st.markdown("<div class='glass-card' style='text-align: center;'>", unsafe_allow_html=True)
        st.title("🌅 כניסת מורים")
        user_key = st.text_input("סיסמה:", type="password")
        if st.button("כניסה למערכת 🔑"):
            if user_key == SECRET_WORD:
                st.session_state.logged_in = True
                st.rerun()
            else: st.error("סיסמה שגויה.")
        st.markdown("</div>", unsafe_allow_html=True)

# --- 5. המערכת המרכזית ---
else:
    st.title("EduCheck AI - בדיקה חכמה 🎓")
    tab1, tab2 = st.tabs(["🔍 בדיקת מבחן", "📊 דוחות פדגוגיים"])

    with tab1:
        # --- חלק א': יצירת מחוון אוטומטי ---
        with st.expander("🪄 מחולל מחוון אוטומטי (לפי צילום שאלון)"):
            st.write("העלה את דף השאלות וה-AI יבנה מחוון תשובות עבורך:")
            rubric_file = st.file_uploader("העלה תמונת שאלון", type=['png', 'jpg', 'jpeg'], key="rubric_gen")
            if st.button("צור מחוון מהתמונה ⚡"):
                if rubric_file:
                    with st.spinner("מנתח שאלות ומייצר תשובות..."):
                        img_r = Image.open(rubric_file)
                        model = genai.GenerativeModel('gemini-1.5-flash')
                        res = model.generate_content(["נתח את דף השאלות הזה וצור מחוון תשובות מפורט וקצר עבור מורה.", img_r])
                        st.session_state.temp_rubric = res.text
                else: st.warning("נא להעלות תמונה של השאלות.")
            
            if st.session_state.temp_rubric:
                st.text_area("המחוון שנוצר (ניתן לערוך):", value=st.session_state.temp_rubric, height=150, key="edit_rubric")
                if st.button("✅ אשר והשתמש במחוון זה"):
                    st.session_state.final_rubric = st.session_state.edit_rubric
                    st.success("המחוון עודכן בהצלחה!")

        # --- חלק ב': בדיקת המבחן ---
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            student_name = st.text_input("שם התלמיד:")
            # המחוון נמשך מהמחולל או מהקלדה ידנית
            current_rubric = st.text_area("מחוון תשובות סופי:", 
                                         value=st.session_state.get('final_rubric', ""), 
                                         height=150)
        with col2:
            source = st.file_uploader("העלה את תשובות התלמיד", type=['png', 'jpg', 'jpeg'])
            cam = st.camera_input("או צלם")

        if st.button("נתח והפק דוח פדגוגי 🚀"):
            active_img = cam if cam else source
            if active_img and student_name and current_rubric:
                with st.spinner("בודק מבחן..."):
                    img = Image.open(active_img)
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    prompt = f"נתח את המבחן של {student_name} לפי המחוון: {current_rubric}. תן ציון ודוח פדגוגי בעברית."
                    response = model.generate_content([prompt, img])
                    output = response.text
                    st.session_state.reports.append({"שם": student_name, "תאריך": datetime.now().strftime("%d/%m/%Y"), "דוח": output})
                    st.markdown(f"<div style='background: white; color: black; padding: 20px; border-radius: 12px;'>{output}</div>", unsafe_allow_html=True)
            else: st.warning("וודא שיש שם, מחוון ותמונת מבחן.")
        st.markdown("</div>", unsafe_allow_html=True)

    with tab2:
        st.subheader("📋 היסטוריית דוחות")
        for r in reversed(st.session_state.reports):
            with st.expander(f"📄 {r['שם']} | {r['תאריך']}"):
                st.markdown(r['דוח'])

    if st.sidebar.button("🚪 יציאה"):
        st.session_state.logged_in = False
        st.rerun()
