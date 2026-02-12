import streamlit as st
import google.generativeai as genai
from PIL import Image
import pandas as pd
from datetime import datetime
import io

# --- 1. הגדרות API ואבטחה ---
MY_API_KEY = "AIzaSyDJdiYe4VmudGKFQzoCI_MmngD26D4wm1Q" 
ALLOWED_PASSWORDS = [
    "dvir2012", "Teacher2012", "Sunset2012", "מורה2012", "Dvir_2012!",
    "2012EduCheck", "D2012V", "D@2012", "Dvir2012Pro", "Gold2012"
]
genai.configure(api_key=MY_API_KEY)

# --- 2. עיצוב UI מודרני מורחב (Modern Tech Edition) ---
st.set_page_config(page_title="EduCheck AI - Pro", layout="wide")

st.markdown("""
<style>
    /* הגדרות כלליות */
    .stApp {
        background: radial-gradient(circle at top left, #1e293b, #0f172a);
        color: #f8fafc;
        direction: rtl;
        text-align: right;
    }
    
    /* כרטיס מודרני עם אפקט זכוכית עמוק */
    .feature-card {
        background: rgba(30, 41, 59, 0.5);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 20px;
        padding: 30px;
        margin-bottom: 25px;
        box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.2);
    }

    /* כותרות בסגנון הייטק */
    .main-title {
        background: linear-gradient(90deg, #38bdf8, #818cf8);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3.5rem;
        font-weight: 800;
        text-align: center;
        margin-bottom: 0;
    }

    /* כפתור מודרני */
    .stButton>button {
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
        color: white !important;
        border: none;
        border-radius: 12px;
        padding: 15px 30px;
        font-size: 1.1rem;
        font-weight: 600;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        width: 100%;
    }
    .stButton>button:hover {
        transform: translateY(-3px);
        box-shadow: 0 10px 20px rgba(37, 99, 235, 0.4);
        background: linear-gradient(135deg, #60a5fa 0%, #3b82f6 100%);
    }

    /* עיצוב שדות קלט */
    .stTextInput>div>div>input, .stTextArea>div>div>textarea, .stSelectbox>div>div>div {
        background-color: #1e293b !important;
        color: white !important;
        border: 1px solid #334155 !important;
        border-radius: 10px !important;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. לוגיקה פנימית ופונקציות ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'reports' not in st.session_state: st.session_state.reports = []
if 'current_rubric' not in st.session_state: st.session_state.current_rubric = ""

def call_gemini(prompt, image=None):
    try:
        model = genai.GenerativeModel('models/gemini-1.5-flash')
        content = [prompt]
        if image:
            content.append(Image.open(image))
        response = model.generate_content(content)
        return response.text
    except Exception as e:
        return f"שגיאה בחיבור ל-AI: {str(e)}"

# --- 4. מסך כניסה ---
if not st.session_state.logged_in:
    st.markdown("<div style='height: 15vh;'></div>", unsafe_allow_html=True)
    _, login_col, _ = st.columns([1, 1, 1])
    with login_col:
        st.markdown("<div class='feature-card' style='text-align: center;'>", unsafe_allow_html=True)
        st.markdown("<h1 style='color: white;'>EduCheck AI</h1>", unsafe_allow_html=True)
        st.write("מערכת זיהוי וניתוח פדגוגי")
        pwd = st.text_input("הזן קוד מורשה:", type="password", placeholder="••••••••")
        if st.button("התחבר למערכת"):
            if pwd in ALLOWED_PASSWORDS:
                st.session_state.logged_in = True
                st.rerun()
            else: st.error("קוד שגוי. הגישה נחסמה.")
        st.markdown("</div>", unsafe_allow_html=True)

# --- 5. הממשק המרכזי ---
else:
    st.markdown("<h1 class='main-title'>EduCheck AI</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; color:#94a3b8;'>מערכת חכמה לבדיקת מבחנים וניהול ציונים</p>", unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["🚀 מרכז בדיקה", "📊 ארכיון וסטטיסטיקה", "⚙️ הגדרות מחוון"])

    with tab3:
        st.markdown("<div class='feature-card'>", unsafe_allow_html=True)
        st.subheader("🛠️ ניהול מחוון תשובות (Rubric)")
        col_r1, col_r2 = st.columns([1, 1])
        with col_r1:
            rubric_img = st.file_uploader("העלה צילום של שאלון המבחן", type=['png', 'jpg', 'jpeg'], key="rubric_up")
            instructions = st.text_area("הנחיות מיוחדות ל-AI (למשל: 'היה מחמיר בדקדוק')", height=100)
        with col_r2:
            if st.button("ייצר מחוון אוטומטי"):
                if rubric_img:
                    with st.spinner("מנתח שאלון..."):
                        res = call_gemini(f"בנה מחוון תשובות מפורט וניקוד לכל שאלה על סמך התמונה. הנחיות נוספות: {instructions}", rubric_img)
                        st.session_state.current_rubric = res
                else: st.warning("אנא העלה תמונה של השאלון קודם.")
            
            st.session_state.current_rubric = st.text_area("טקסט המחוון (ניתן לעריכה):", value=st.session_state.current_rubric, height=200)
        st.markdown("</div>", unsafe_allow_html=True)

    with tab1:
        col_input, col_preview = st.columns([1.5, 1])
        
        with col_input:
            st.markdown("<div class='feature-card'>", unsafe_allow_html=True)
            st.subheader("📝 פרטי המבחן")
            c1, c2 = st.columns(2)
            with c1:
                student = st.text_input("שם התלמיד:", placeholder="ישראל ישראלי")
                grade_lvl = st.text_input("כיתה:", placeholder="ז' 4")
            with c2:
                subjects = ["תורה", "נביא", "גמרא", "משנה", "הלכה", "מדעים", "היסטוריה", "עברית", "אחר"]
                subj = st.selectbox("מקצוע:", subjects)
            
            st.divider()
            exam_file = st.file_uploader("העלה את המבחן לבדיקה:", type=['png', 'jpg', 'jpeg'], key="exam_up")
            cam_file = st.camera_input("או צלם בזמן אמת")
            st.markdown("</div>", unsafe_allow_html=True)

        with col_preview:
            st.markdown("<div class='feature-card' style='height: 100%;'>", unsafe_allow_html=True)
            st.subheader("🎯 פעולות")
            if st.button("בצע בדיקה פדגוגית עכשיו"):
                active = cam_file if cam_file else exam_file
                if active and student:
                    with st.spinner("Gemini מנתח את התשובות..."):
                        prompt = f"""
                        נתח את המבחן ב{subj} עבור {student}. 
                        מחוון: {st.session_state.current_rubric}. 
                        חובה לציין ציון מספרי מודגש בראש הדוח. 
                        ספק משוב מפורט: מה היה טוב ומה טעון שיפור.
                        """
                        analysis = call_gemini(prompt, active)
                        
                        # חילוץ ציון
                        score = "".join(filter(str.isdigit, analysis[:40])) or "100"
                        
                        st.session_state.reports.append({
                            "שם": student, "מקצוע": subj, "כיתה": grade_lvl,
                            "ציון": int(score) if score.isdigit() else 0,
                            "תאריך": datetime.now().strftime("%d/%m/%Y %H:%M"),
                            "דוח": analysis
                        })
                        st.success("הבדיקה הושלמה ונשמרה!")
                        st.markdown(f"<div style='background:#1e293b; padding:15px; border-radius:10px; border-right: 4px solid #38bdf8;'>{analysis}</div>", unsafe_allow_html=True)
                else: st.error("חסרים נתונים: וודא שהעלית מבחן והזנת שם תלמיד.")
            st.markdown("</div>", unsafe_allow_html=True)

    with tab2:
        st.markdown("<div class='feature-card'>", unsafe_allow_html=True)
        st.subheader("📈 היסטוריית ציונים וניתוח")
        
        if st.session_state.reports:
            df = pd.DataFrame(st.session_state.reports)
            
            # סטטיסטיקה מהירה
            avg_score = df['ציון'].mean()
            st.metric("ממוצע כיתתי", f"{avg_score:.1f}")
            
            st.divider()
            
            for r in reversed(st.session_state.reports):
                with st.expander(f"📄 {r['שם']} | {r['מקצוע']} | ציון: {r['ציון']} ({r['תאריך']})"):
                    st.markdown(r['דוח'])
            
            # ייצוא לאקסל
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name='Reports')
            st.download_button("📥 הורד את כל הנתונים לאקסל", data=output.getvalue(), file_name="educheck_reports.xlsx")
        else:
            st.info("עדיין לא בוצעו בדיקות.")
        st.markdown("</div>", unsafe_allow_html=True)

    st.sidebar.markdown(f"### שלום, מורה")
    if st.sidebar.button("יציאה מהמערכת"):
        st.session_state.logged_in = False
        st.rerun()
