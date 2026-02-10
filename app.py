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
st.set_page_config(page_title="EduCheck PRO Chat", layout="wide")

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
    .chat-box {
        background: rgba(0, 0, 0, 0.2); border-radius: 10px; padding: 15px; margin-top: 10px;
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
if 'current_rubric' not in st.session_state: st.session_state.current_rubric = ""

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
        # --- חלק א': בניית מחוון עם צ'אט ---
        with st.expander("🪄 יצירת מחוון מושלם (צ'אט עם Gemini)"):
            st.write("העלה שאלון ושפר את המחוון בעזרת הצ'אט:")
            rubric_file = st.file_uploader("העלה תמונת שאלון (אופציונלי)", type=['png', 'jpg', 'jpeg'])
            
            chat_input = st.text_input("כתוב ל-Gemini מה לעדכן במחוון (למשל: 'הפוך את המחוון ליותר קפדני'):")
            
            if st.button("עדכן מחוון בעזרת ה-AI 💬"):
                with st.spinner("Gemini מעבד את הבקשה שלך..."):
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    
                    # בניית הפרומפט - שילוב של התמונה (אם יש), המחוון הקיים והבקשה החדשה
                    prompt_parts = ["אתה עוזר למורה לבנות מחוון מושלם."]
                    if st.session_state.current_rubric:
                        prompt_parts.append(f"זה המחוון הקיים: {st.session_state.current_rubric}")
                    if rubric_file:
                        prompt_parts.append(Image.open(rubric_file))
                    prompt_parts.append(f"זו הבקשה החדשה של המורה: {chat_input}")
                    prompt_parts.append("החזר רק את תוכן המחוון המעודכן והמפורט.")
                    
                    response = model.generate_content(prompt_parts)
                    st.session_state.current_rubric = response.text
            
            st.markdown("<div class='chat-box'>", unsafe_allow_html=True)
            edited_rubric = st.text_area("המחוון הנוכחי שלך (ניתן לערוך ידנית):", 
                                        value=st.session_state.current_rubric, height=200)
            st.session_state.current_rubric = edited_rubric
            st.markdown("</div>", unsafe_allow_html=True)

        # --- חלק ב': בדיקת המבחן ---
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            student_name = st.text_input("שם התלמיד:")
            final_rubric = st.text_area("מחוון תשובות סופי לשימוש:", value=st.session_state.current_rubric, height=150)
        
        with col2:
            source = st.file_uploader("העלה את תשובות התלמיד", type=['png', 'jpg', 'jpeg'])
            cam = st.camera_input("או צלם")

        if st.button("נתח והפק דוח פדגוגי 🚀"):
            active_img = cam if cam else source
            if active_img and student_name and final_rubric:
                with st.spinner("בודק מבחן..."):
                    img = Image.open(active_img)
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    prompt = f"נתח את המבחן של {student_name} לפי המחוון: {final_rubric}. תן ציון ודוח פדגוגי בעברית."
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
