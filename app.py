import streamlit as st
import google.generativeai as genai
from PIL import Image
import io
import pandas as pd
from datetime import datetime

# --- 1. הגדרות API ---
MY_API_KEY = "AIzaSyDJdiYe4VmudGKFQzoCI_MmngD26D4wm1Q" 
genai.configure(api_key=MY_API_KEY)

# --- 2. עיצוב הממשק (שילוב כהה-בהיר יוקרתי) ---
st.set_page_config(page_title="EduCheck AI PRO", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Assistant:wght@300;400;700&display=swap');
    
    html, body, [class*="css"] { font-family: 'Assistant', sans-serif; direction: rtl; }
    
    .stApp { background-color: #f8fafc; }
    
    /* כותרת יוקרתית */
    .main-header { 
        background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
        padding: 2.5rem;
        border-radius: 0 0 30px 30px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.1);
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .main-header h1 { color: #f8fafc; font-weight: 800; margin: 0; font-size: 3rem; }
    .main-header p { color: #cbd5e1; font-size: 1.2rem; margin-top: 0.5rem; }

    /* כרטיסים לבנים עם צל */
    .content-card {
        background: white;
        padding: 2rem;
        border-radius: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.02);
        border: 1px solid #e2e8f0;
        margin-bottom: 1.5rem;
    }

    /* עיצוב שדות קלט (כהה) */
    .stTextArea textarea, .stTextInput input {
        background-color: #1e293b !important;
        color: #f8fafc !important;
        border-radius: 12px !important;
        border: 2px solid #334155 !important;
        padding: 15px !important;
    }

    /* כפתור בדיקה */
    .stButton>button {
        background: linear-gradient(90deg, #2563eb, #7c3aed);
        color: white;
        border: none;
        padding: 1rem 2rem;
        border-radius: 15px;
        font-weight: 700;
        font-size: 1.2rem;
        width: 100%;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(37, 99, 235, 0.3);
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(37, 99, 235, 0.4);
    }
</style>
""", unsafe_allow_html=True)

# --- 3. פונקציות עזר ---

def get_gemini_response(name, rubric, image):
    model = genai.GenerativeModel('gemini-1.5-flash')
    prompt = f"""
    אתה מורה בוחן מומחה. עליך לנתח מבחן של תלמיד בשם {name}.
    השתמש במחוון התשובות הבא: {rubric}
    
    משימות:
    1. קרא את כתב היד בתמונה (גם אם הוא לא קריא, נסה לפענח לפי ההקשר).
    2. השווה כל תשובה למחוון.
    3. תן ציון מספרי מ-0 עד 100.
    4. כתב משוב מפורט ומעודד לתלמיד.
    
    החזר את התשובה במבנה הבא:
    תמלול: [מה שהתלמיד כתב]
    ציון: [מספר]
    משוב: [פירוט]
    """
    response = model.generate_content([prompt, image])
    return response.text

# --- 4. מבנה האפליקציה (Sidebar) ---

with st.sidebar:
    st.markdown("### ⚙️ הגדרות מערכת")
    st.info("מודל פעיל: Gemini 1.5 Flash (גרסה משופרת)")
    
    if "history" not in st.session_state:
        st.session_state.history = []

    if st.button("🗑️ נקה היסטוריה"):
        st.session_state.history = []
        st.rerun()

# --- 5. מסך ראשי ---

st.markdown("""
<div class="main-header">
    <h1>EduCheck AI PRO</h1>
    <p>מערכת חכמה לבדיקת מבחנים וניתוח כתב יד</p>
</div>
""", unsafe_allow_html=True)

# לשוניות (Tabs)
tab1, tab2, tab3 = st.tabs(["🔍 בדיקת מבחן", "📊 היסטוריית ציונים", "📝 דף תרגול א-ת"])

with tab1:
    col1, col2 = st.columns([1, 1.2], gap="large")
    
    with col1:
        st.markdown("<div class='content-card'>", unsafe_allow_html=True)
        st.subheader("📋 פרטי המבחן")
        student_name = st.text_input("שם התלמיד:", placeholder="למשל: ישראל ישראלי")
        rubric = st.text_area("מחוון תשובות:", placeholder="כתוב כאן מהן התשובות הנכונות...", height=200)
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown("<div class='content-card'>", unsafe_allow_html=True)
        st.subheader("📸 העלאת המבחן")
        img_source = st.radio("בחר מקור:", ["העלאת קובץ", "צילום במצלמה"], horizontal=True)
        
        if img_source == "העלאת קובץ":
            uploaded_file = st.file_uploader("בחר תמונה...", type=['png', 'jpg', 'jpeg'])
        else:
            uploaded_file = st.camera_input("צלם את המבחן")
        st.markdown("</div>", unsafe_allow_html=True)

    if st.button("התחל בדיקה אוטומטית 🚀"):
        if uploaded_file and student_name and rubric:
            with st.spinner("ה-AI מנתח את כתב היד..."):
                img = Image.open(uploaded_file)
                result = get_gemini_response(student_name, rubric, img)
                
                # שמירה להיסטוריה
                st.session_state.history.append({
                    "תאריך": datetime.now().strftime("%d/%m/%Y %H:%M"),
                    "תלמיד": student_name,
                    "תוצאה": result
                })
                
                st.markdown("<div class='content-card' style='border-right: 10px solid #2563eb;'>", unsafe_allow_html=True)
                st.markdown("### 🏁 תוצאות הניתוח:")
                st.write(result)
                st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.error("נא למלא את כל הפרטים ולהעלות תמונה.")

with tab2:
    st.subheader("📈 ריכוז ציונים")
    if st.session_state.history:
        df = pd.DataFrame(st.session_state.history)
        st.table(df)
        
        # אפשרות להורדה ל-CSV
        csv = df.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 הורד דוח לאקסל (CSV)", csv, "grades.csv", "text/csv")
    else:
        st.write("עדיין אין ציונים במערכת.")

with tab3:
    st.subheader("📝 הדפסת דף איסוף כתב יד")
    st.write("הדפס את הטבלה הזו כדי לאסוף דגימות כתב יד מהתלמידים:")
    letters = ['א','ב','ג','ד','ה','ו','ז','ח','ט','י','כ','ך','ל','מ','ם','נ','ן','ס','ע','פ','ף','צ','ץ','ק','ר','ש','ת']
    
    html_grid = "<div style='display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; direction: rtl;'>"
    for l in letters:
        html_grid += f"<div style='border: 1px solid #000; padding: 20px; text-align: center; background: white;'>{l} = <br><br></div>"
    html_grid += "</div>"
    st.markdown(html_grid, unsafe_allow_html=True)
