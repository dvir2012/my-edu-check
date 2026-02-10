import streamlit as st
import google.generativeai as genai
from PIL import Image
import pandas as pd
from datetime import datetime

# --- 1. הגדרות אבטחה ו-API ---
MY_API_KEY = "AIzaSyDJdiYe4VmudGKFQzoCI_MmngD26D4wm1Q" 

# רשימת 10 הסיסמאות המורשות (מבוססות 2012)
ALLOWED_PASSWORDS = [
    "dvir2012", "Teacher2012", "Sunset2012", "מורה2012", "Dvir_2012!",
    "2012EduCheck", "D2012V", "D@2012", "Dvir2012Pro", "Gold2012"
]

genai.configure(api_key=MY_API_KEY)

# --- 2. עיצוב הממשק (Sunset Deep UI) ---
st.set_page_config(page_title="EduCheck PRO - Sunset", layout="wide")

st.markdown(f"""
<style>
    [data-testid="stAppViewContainer"] {{
        background: linear-gradient(180deg, #42275a 0%, #734b6d 50%, #ba5370 100%);
        direction: rtl; text-align: right;
    }}
    .glass-card {{
        background: rgba(255, 255, 255, 0.12);
        backdrop-filter: blur(15px);
        border-radius: 20px; padding: 25px; border: 1px solid rgba(255, 255, 255, 0.2);
        margin-bottom: 20px; color: white;
    }}
    h1, h2, h3, label {{ color: #ffffff !important; font-family: 'Assistant', sans-serif; }}
    .stTextArea textarea, .stTextInput input {{
        background-color: rgba(255, 255, 255, 0.95) !important;
        color: #1e293b !important; border-radius: 10px !important;
    }}
    .stButton>button {{
        background: linear-gradient(90deg, #ff512f 0%, #dd2476 100%);
        color: white; border: none; padding: 12px 25px;
        border-radius: 12px; font-weight: 700; width: 100%; transition: 0.3s;
    }}
    .stButton>button:hover {{ transform: translateY(-2px); box-shadow: 0 8px 20px rgba(221, 36, 118, 0.4); }}
</style>
""", unsafe_allow_html=True)

# --- 3. ניהול מצב (Session State) ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'reports' not in st.session_state: st.session_state.reports = []
if 'current_rubric' not in st.session_state: st.session_state.current_rubric = ""

# --- 4. מסך כניסה (Login Screen) ---
if not st.session_state.logged_in:
    st.markdown("<div style='height: 20vh;'></div>", unsafe_allow_html=True)
    cols = st.columns([1, 1.5, 1])
    with cols[1]:
        st.markdown("<div class='glass-card' style='text-align: center;'>", unsafe_allow_html=True)
        st.title("🌅 כניסת מורים")
        st.write("הזן אחת מסיסמאות הגישה המורשות")
        user_key = st.text_input("סיסמה:", type="password")
        if st.button("כניסה למערכת 🔑"):
            # בדיקה אם הסיסמה שהוקלדה נמצאת ברשימת המורשים
            if user_key in ALLOWED_PASSWORDS:
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("סיסמה לא מוכרת. וודא שהשתמשת באחת מסיסמאות 2012.")
        st.markdown("</div>", unsafe_allow_html=True)

# --- 5. המערכת המרכזית (לאחר כניסה) ---
else:
    st.markdown("<h1 style='text-align: center; padding-top: 20px;'>EduCheck AI - בדיקה חכמה 🎓</h1>", unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["🔍 בדיקת מבחן ומחוון", "📊 דוחות פדגוגיים"])

    with tab1:
        # --- חלק א': בניית מחוון עם צ'אט ---
        with st.expander("🪄 יצירת מחוון מושלם (צ'אט עם Gemini)"):
            st.write("העלה שאלון ושפר את המחוון בעזרת הצ'אט:")
            rubric_file = st.file_uploader("העלה תמונת שאלון (אופציונלי)", type=['png', 'jpg', 'jpeg'], key="rub_upload")
            chat_input = st.text_input("כתוב ל-Gemini מה לעדכן במחוון:")
            
            if st.button("עדכן מחוון בעזרת ה-AI 💬"):
                with st.spinner("Gemini מעבד את הבקשה..."):
                    try:
                        model = genai.GenerativeModel('gemini-1.5-flash')
                        prompt_parts = ["אתה עוזר למורה לבנות מחוון תשובות מושלם."]
                        if st.session_state.current_rubric:
                            prompt_parts.append(f"זה המחוון הקיים: {st.session_state.current_rubric}")
                        if rubric_file:
                            prompt_parts.append(Image.open(rubric_file))
                        prompt_parts.append(f"הבקשה החדשה: {chat_input}. החזר רק את תוכן המחוון המעודכן.")
                        response = model.generate_content(prompt_parts)
                        st.session_state.current_rubric = response.text
                    except Exception as e: st.error(f"שגיאה: {e}")
            
            st.session_state.current_rubric = st.text_area("המחוון הנוכחי שלך (ניתן לערוך):", 
                                                        value=st.session_state.current_rubric, height=150)

        # --- חלק ב': בדיקת המבחן ---
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            student_name = st.text_input("שם התלמיד:")
            final_rubric = st.text_area("מחוון תשובות סופי לשימוש:", value=st.session_state.current_rubric, height=150)
        with col2:
            source = st.file_uploader("העלה את תשובות התלמיד", type=['png', 'jpg', 'jpeg'], key="exam_upload")
            cam = st.camera_input("או צלם")

        if st.button("נתח והפק דוח פדגוגי 🚀"):
            active_img = cam if cam else source
            if active_img and student_name and final_rubric:
                with st.spinner("ה-AI בודק את המבחן..."):
                    try:
                        img = Image.open(active_img)
                        model = genai.GenerativeModel('gemini-1.5-flash')
                        prompt = f"נתח את המבחן של {student_name} לפי המחוון: {final_rubric}. תן ציון ומשוב פדגוגי בעברית."
                        response = model.generate_content([prompt, img])
                        output = response.text
                        st.session_state.reports.append({"שם": student_name, "תאריך": datetime.now().strftime("%d/%m/%Y %H:%M"), "דוח": output})
                        st.success("הבדיקה הושלמה!")
                        st.markdown(f"<div style='background: white; color: black; padding: 20px; border-radius: 12px;'>{output}</div>", unsafe_allow_html=True)
                    except Exception as e: st.error(f"שגיאה בניתוח: {e}")
            else: st.warning("מלא את כל הפרטים.")
        st.markdown("</div>", unsafe_allow_html=True)

    with tab2:
        st.subheader("📋 ארכיון דוחות")
        if st.session_state.reports:
            for r in reversed(st.session_state.reports):
                with st.expander(f"👤 {r['שם']} | 📅 {r['תאריך']}"):
                    st.markdown(r['דוח'])
            df = pd.DataFrame(st.session_state.reports)
            csv = df.to_csv(index=False).encode('utf-8-sig')
            st.download_button("📥 הורד לאקסל (CSV)", csv, "reports.csv", "text/csv")

    if st.sidebar.button("🚪 יציאה"):
        st.session_state.logged_in = False
        st.rerun()
