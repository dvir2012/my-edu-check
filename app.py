import streamlit as st
import google.generativeai as genai
from PIL import Image
import pandas as pd
from datetime import datetime

# --- 1. הגדרות API וקוד מורה ---
MY_API_KEY = "AIzaSyDJdiYe4VmudGKFQzoCI_MmngD26D4wm1Q" 
TEACHER_CODE = "1234" # שנה את הקוד הזה למה שתרצה
genai.configure(api_key=MY_API_KEY)

# --- 2. עיצוב "שקיעה" (Sunset Design) ---
st.set_page_config(page_title="EduCheck Sunset", layout="wide")

st.markdown(f"""
<style>
    /* רקע שקיעה מדורג */
    .stApp {{
        background: linear-gradient(180deg, #ff7e5f 0%, #feb47b 50%, #864ba2 100%);
        direction: rtl;
        text-align: right;
        color: white;
    }}
    
    /* כרטיסים לבנים שקופים */
    .glass-card {{
        background: rgba(255, 255, 255, 0.15);
        backdrop-filter: blur(10px);
        border-radius: 20px;
        padding: 25px;
        border: 1px solid rgba(255, 255, 256, 0.2);
        margin-bottom: 20px;
    }}
    
    h1, h2, h3, p, span, label {{ color: white !important; }}
    
    /* עיצוב שדות קלט */
    .stTextArea textarea, .stTextInput input {{
        background-color: rgba(255, 255, 255, 0.9) !important;
        color: #2d3436 !important;
        border-radius: 12px !important;
    }}
    
    /* כפתור בולט */
    .stButton>button {{
        background: #6c5ce7;
        color: white;
        border: none;
        padding: 15px 30px;
        border-radius: 15px;
        font-weight: bold;
        width: 100%;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }}
</style>
""", unsafe_allow_html=True)

# --- 3. ניהול מצב (Session State) ---
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'student_reports' not in st.session_state:
    st.session_state.student_reports = []

# --- 4. מסך כניסה (Login) ---
if not st.session_state.authenticated:
    st.markdown("<div style='text-align:center; padding:100px;'>", unsafe_allow_html=True)
    st.title("☀️ ברוכים הבאים ל-EduCheck")
    st.subheader("נא להזין קוד מורה לכניסה")
    input_code = st.text_input("קוד גישה:", type="password")
    if st.button("כניסה למערכת"):
        if input_code == TEACHER_CODE:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("קוד שגוי. נסה שוב.")
    st.markdown("</div>", unsafe_allow_html=True)

# --- 5. המערכת המרכזית (אחרי כניסה) ---
else:
    st.title("🌅 EduCheck AI - מרחב המורה")
    
    tab1, tab2 = st.tabs(["🔍 בדיקת מבחן חדש", "📊 דוח פדגוגי מסכם"])
    
    with tab1:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        
        with col1:
            student_name = st.text_input("שם התלמיד:")
            rubric = st.text_area("מחוון תשובות (מה נחשב נכון?):", height=150)
        
        with col2:
            img_file = st.file_uploader("העלה צילום מבחן", type=['png', 'jpg', 'jpeg'])
            camera_img = st.camera_input("או צלם ישירות")
        
        final_img = camera_img if camera_img else img_file
        
        if st.button("בצע בדיקה וניתוח ⚡"):
            if final_img and student_name:
                with st.spinner("ה-AI מנתח את התשובות..."):
                    try:
                        img = Image.open(final_img)
                        model = genai.GenerativeModel('gemini-1.5-flash')
                        
                        prompt = f"""
                        נתח את המבחן של {student_name} לפי המחוון: {rubric}.
                        ספק תשובה מובנית:
                        1. ציון סופי (0-100).
                        2. רשימת טעויות.
                        3. משוב פדגוגי אישי לתלמיד.
                        4. נקודות לחיזוק.
                        """
                        
                        response = model.generate_content([prompt, img])
                        analysis = response.text
                        
                        # שמירה לדוח הפדגוגי
                        st.session_state.student_reports.append({
                            "שם התלמיד": student_name,
                            "תאריך": datetime.now().strftime("%d/%m/%Y"),
                            "ניתוח פדגוגי": analysis
                        })
                        
                        st.success(f"הבדיקה עבור {student_name} הושלמה!")
                        st.markdown(f"<div style='background:white; color:black; padding:20px; border-radius:15px;'>{analysis}</div>", unsafe_allow_html=True)
                    except Exception as e:
                        st.error(f"שגיאה בתקשורת: {e}")
            else:
                st.warning("נא למלא שם ולהעלות תמונה.")
        st.markdown("</div>", unsafe_allow_html=True)

    with tab2:
        st.subheader("📋 דוח פדגוגי מסכם")
        if st.session_state.student_reports:
            df = pd.DataFrame(st.session_state.student_reports)
            
            for index, row in df.iterrows():
                with st.expander(f"👤 {row['שם התלמיד']} - {row['תאריך']}"):
                    st.write(row['ניתוח פדגוגי'])
            
            # כפתור הורדה
            csv = df.to_csv(index=False).encode('utf-8-sig')
            st.download_button("📥 הורד דוח פדגוגי מלא (Excel)", csv, "pedagogical_report.csv", "text/csv")
        else:
            st.write("עדיין לא נבדקו מבחנים.")
            
    if st.sidebar.button("יציאה מהמערכת (Logout)"):
        st.session_state.authenticated = False
        st.rerun()
