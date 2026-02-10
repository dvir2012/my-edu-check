import streamlit as st
import google.generativeai as genai
from PIL import Image
import pandas as pd
from datetime import datetime

# --- 1. הגדרות אבטחה ו-API ---
MY_API_KEY = "AIzaSyDJdiYe4VmudGKFQzoCI_MmngD26D4wm1Q" 
SECRET_WORD = "שקיעה2024"  # <-- כאן אתה משנה את המילה הסודית שלך
genai.configure(api_key=MY_API_KEY)

# --- 2. עיצוב שקיעה (Sunset UI) ---
st.set_page_config(page_title="EduCheck Sunset PRO", layout="wide")

st.markdown(f"""
<style>
    /* רקע שקיעה פוטוגני */
    .stApp {{
        background: linear-gradient(135deg, #2c3e50 0%, #000000 100%); /* רקע כהה בסיסי */
    }}
    [data-testid="stAppViewContainer"] {{
        background: linear-gradient(180deg, #ff5e62 0%, #ff9966 40%, #7f00ff 100%);
        direction: rtl;
        text-align: right;
    }}
    
    /* כרטיסי זכוכית (Glassmorphism) */
    .glass-card {{
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(15px);
        border-radius: 25px;
        padding: 30px;
        border: 1px solid rgba(255, 255, 255, 0.2);
        margin-bottom: 25px;
        color: white;
    }}

    /* כותרות */
    h1, h2, h3, label {{ color: white !important; font-family: 'Assistant', sans-serif; }}

    /* עיצוב שדות קלט לבנים ונקיים */
    .stTextArea textarea, .stTextInput input {{
        background-color: rgba(255, 255, 255, 0.95) !important;
        color: #1e293b !important;
        border-radius: 12px !important;
        font-size: 1.1rem !important;
    }}

    /* כפתור "שקיעה" סגול */
    .stButton>button {{
        background: linear-gradient(90deg, #6a11cb 0%, #2575fc 100%);
        color: white;
        border: none;
        padding: 15px 0px;
        border-radius: 15px;
        font-weight: 800;
        font-size: 1.2rem;
        transition: 0.3s all;
    }}
    .stButton>button:hover {{
        transform: scale(1.02);
        box-shadow: 0 10px 20px rgba(0,0,0,0.3);
    }}
</style>
""", unsafe_allow_html=True)

# --- 3. ניהול כניסה (Auth) ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'reports' not in st.session_state:
    st.session_state.reports = []

# --- 4. מסך כניסה ---
if not st.session_state.logged_in:
    cols = st.columns([1, 2, 1])
    with cols[1]:
        st.markdown("<div style='height: 100px;'></div>", unsafe_allow_html=True)
        st.markdown("<div class='glass-card' style='text-align: center;'>", unsafe_allow_html=True)
        st.title("🌅 EduCheck Login")
        st.write("נא להזין את המילה הסודית לכניסה למרחב המורה")
        
        user_input = st.text_input("מילה סודית:", type="password")
        if st.button("כניסה למערכת 🔑"):
            if user_input == SECRET_WORD:
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("המילה הסודית שגויה. נסה שוב.")
        st.markdown("</div>", unsafe_allow_html=True)

# --- 5. ממשק המורה המרכזי ---
else:
    st.markdown("<h1 style='text-align: center;'>EduCheck AI - ניהול פדגוגי 🎓</h1>", unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["🔍 בדיקת מבחן", "📊 דוחות פדגוגיים"])

    with tab1:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        
        with c1:
            st.subheader("📝 פרטי המשימה")
            st_name = st.text_input("שם התלמיד:")
            st_rubric = st.text_area("מחוון תשובות (מה נחשב תשובה נכונה?):", height=180)
        
        with c2:
            st.subheader("📸 העלאת המבחן")
            file = st.file_uploader("בחר קובץ תמונה", type=['png', 'jpg', 'jpeg'])
            cam = st.camera_input("או צלם בזמן אמת")
            
        active_img = cam if cam else file

        if st.button("נתח מבחן והפק דוח פדגוגי ✨") and active_img:
            with st.spinner("מנתח כתב יד ומחשב תוצאות..."):
                try:
                    img = Image.open(active_img)
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    
                    prompt = f"""
                    בתור מורה בוחן, נתח את המבחן של {st_name}.
                    השתמש במחוון: {st_rubric}
                    ספק דוח מפורט בעברית הכולל:
                    1. ציון סופי.
                    2. תמלול תשובות עיקריות.
                    3. משוב פדגוגי: מה התלמיד הבין ואיפה הוא מתקשה.
                    4. המלצה לשיפור.
                    """
                    
                    resp = model.generate_content([prompt, img])
                    output = resp.text
                    
                    # שמירה להיסטוריה
                    st.session_state.reports.append({
                        "שם": st_name,
                        "תאריך": datetime.now().strftime("%d/%m/%Y %H:%M"),
                        "דוח": output
                    })
                    
                    st.success("הבדיקה הסתיימה בהצלחה!")
                    st.markdown(f"<div style='background: white; color: black; padding: 25px; border-radius: 15px; border-right: 8px solid #7f00ff;'>{output}</div>", unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"אירעה שגיאה בניתוח: {e}")
        st.markdown("</div>", unsafe_allow_html=True)

    with tab2:
        st.subheader("📈 ריכוז דוחות פדגוגיים")
        if st.session_state.reports:
            # הצגת דוחות בצורה יפה
            for idx, r in enumerate(reversed(st.session_state.reports)):
                with st.expander(f"👤 {r['שם']} | 📅 {r['תאריך']}"):
                    st.markdown(r['דוח'])
            
            # אפשרות הורדה
            df = pd.DataFrame(st.session_state.reports)
            csv = df.to_csv(index=False).encode('utf-8-sig')
            st.download_button("📥 הורד את כל הנתונים לאקסל", csv, "pedagogical_reports.csv", "text/csv")
        else:
            st.info("עדיין לא נבדקו מבחנים. התוצאות יופיעו כאן לאחר הבדיקה הראשונה.")

    # Sidebar ליציאה
    st.sidebar.title("EduCheck Menu")
    if st.sidebar.button("🚪 התנתקות מהמערכת"):
        st.session_state.logged_in = False
        st.rerun()
