import streamlit as st
import google.generativeai as genai
from PIL import Image
import pandas as pd
from datetime import datetime

# --- 1. הגדרות אבטחה ו-API ---
MY_API_KEY = "AIzaSyDJdiYe4VmudGKFQzoCI_MmngD26D4wm1Q" 
SECRET_WORD = "dvir2012"  # המילה הסודית המעודכנת שלך
genai.configure(api_key=MY_API_KEY)

# --- 2. עיצוב שקיעה עמוקה (Sunset Deep UI) ---
st.set_page_config(page_title="EduCheck PRO - Sunset", layout="wide")

st.markdown(f"""
<style>
    /* רקע שקיעה מדורג */
    [data-testid="stAppViewContainer"] {{
        background: linear-gradient(180deg, #42275a 0%, #734b6d 50%, #ba5370 100%);
        direction: rtl;
        text-align: right;
    }}
    
    /* כרטיסי זכוכית שקופים */
    .glass-card {{
        background: rgba(255, 255, 255, 0.12);
        backdrop-filter: blur(15px);
        border-radius: 20px;
        padding: 25px;
        border: 1px solid rgba(255, 255, 255, 0.2);
        margin-bottom: 20px;
        color: white;
    }}

    /* כותרות לבנות */
    h1, h2, h3, label {{ color: #ffffff !important; font-family: 'Assistant', sans-serif; }}

    /* שדות קלט */
    .stTextArea textarea, .stTextInput input {{
        background-color: rgba(255, 255, 255, 0.9) !important;
        color: #1e293b !important;
        border-radius: 10px !important;
        border: none !important;
    }}

    /* כפתור מעוצב */
    .stButton>button {{
        background: linear-gradient(90deg, #ff512f 0%, #dd2476 100%);
        color: white;
        border: none;
        padding: 12px 25px;
        border-radius: 12px;
        font-weight: 700;
        font-size: 1.1rem;
        width: 100%;
        transition: 0.3s;
    }}
    .stButton>button:hover {{
        box-shadow: 0 8px 20px rgba(221, 36, 118, 0.4);
        transform: translateY(-2px);
    }}
</style>
""", unsafe_allow_html=True)

# --- 3. ניהול מצב כניסה ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'reports' not in st.session_state:
    st.session_state.reports = []

# --- 4. מסך כניסה (Login) ---
if not st.session_state.logged_in:
    st.markdown("<div style='height: 15vh;'></div>", unsafe_allow_html=True)
    cols = st.columns([1, 1.5, 1])
    with cols[1]:
        st.markdown("<div class='glass-card' style='text-align: center;'>", unsafe_allow_html=True)
        st.title("🌅 כניסת מורים")
        st.write("נא להזין את המילה הסודית כדי להמשיך")
        user_key = st.text_input("סיסמה:", type="password")
        if st.button("כניסה למערכת 🔑"):
            if user_key == SECRET_WORD:
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("מילה סודית שגויה. נסה שוב.")
        st.markdown("</div>", unsafe_allow_html=True)

# --- 5. מערכת בדיקת מבחנים ---
else:
    st.markdown("<h1 style='text-align: center; padding-top: 20px;'>EduCheck AI - ניתוח פדגוגי 🎓</h1>", unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["🔍 בדיקת מבחן", "📊 ריכוז דוחות פדגוגיים"])

    with tab1:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        col_r, col_l = st.columns(2)
        
        with col_r:
            student_name = st.text_input("שם התלמיד:")
            rubric = st.text_area("מחוון תשובות (מה נחשב נכון?):", height=150)
        
        with col_l:
            source = st.file_uploader("העלה תמונה", type=['png', 'jpg', 'jpeg'])
            cam = st.camera_input("או צלם")
            
        final_img = cam if cam else source

        if st.button("נתח והפק דוח פדגוגי 🚀") and final_img:
            with st.spinner("ה-AI מנתח את התמונה..."):
                try:
                    img = Image.open(final_img)
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    prompt = f"""
                    נתח את המבחן של {student_name} לפי המחוון: {rubric}.
                    כתוב דוח פדגוגי בעברית הכולל:
                    - ציון מוערך.
                    - תמלול התשובות מהכתב יד.
                    - חוזקות וחולשות של התלמיד.
                    - המלצה פדגוגית להמשך למידה.
                    """
                    response = model.generate_content([prompt, img])
                    output = response.text
                    
                    # שמירה להיסטוריה
                    st.session_state.reports.append({
                        "שם": student_name,
                        "תאריך": datetime.now().strftime("%d/%m/%Y"),
                        "דוח": output
                    })
                    
                    st.success("הניתוח הסתיים!")
                    st.markdown(f"<div style='background: white; color: black; padding: 20px; border-radius: 12px;'>{output}</div>", unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"שגיאה בחיבור לשרת: {e}")
        st.markdown("</div>", unsafe_allow_html=True)

    with tab2:
        st.subheader("📋 היסטוריית דוחות")
        if st.session_state.reports:
            for r in reversed(st.session_state.reports):
                with st.expander(f"📄 {r['שם']} | {r['תאריך']}"):
                    st.markdown(r['דוח'])
            
            # כפתור אקסל
            df = pd.DataFrame(st.session_state.reports)
            csv = df.to_csv(index=False).encode('utf-8-sig')
            st.download_button("📥 הורד קובץ ריכוז נתונים (CSV)", csv, "reports.csv", "text/csv")
        else:
            st.info("עדיין אין דוחות שמורים.")

    if st.sidebar.button("🚪 יציאה"):
        st.session_state.logged_in = False
        st.rerun()
