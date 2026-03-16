import streamlit as st
import google.generativeai as genai
from PIL import Image
import pandas as pd
from datetime import datetime
import sqlite3
import time
import re
import json

# ==========================================
# 0. מנגנון סיסמאות והפרדת משתמשים
# ==========================================
PASSWORDS = [str(i) for i in range(1000, 10000)]

if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'teacher_id' not in st.session_state:
    st.session_state.teacher_id = None

def login_screen():
    st.markdown("<h2 style='text-align:center; color:white;'>כניסה למערכת EduCheck</h2>", unsafe_allow_html=True)
    pwd = st.text_input("הזן סיסמת מורה:", type="password")
    if st.button("התחבר"):
        if pwd in PASSWORDS:
            st.session_state.authenticated = True
            st.session_state.teacher_id = pwd
            st.rerun()
        else:
            st.error("סיסמה שגויה")

if not st.session_state.authenticated:
    login_screen()
    st.stop()

SUBJECTS_LIST = ["תורה", "נביא", "הלכה", "גמרא", "חשבון", "אנגלית", "שפה","כישורי חיים", "מחשבת ישראל", "היסטוריה", "מדעים", "אזרחות", "אחר"]

# ==========================================
# 1. בסיס נתונים עם הפרדה ותיקון עמודות חסרות
# ==========================================
def init_db():
    conn = sqlite3.connect('results.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS exams
                (id INTEGER PRIMARY KEY AUTOINCREMENT,
                 teacher_id TEXT,
                 date TEXT, student_name TEXT, subject TEXT, result TEXT)''')
    
    # בדיקה אם עמודת teacher_id קיימת (למניעת קריסה בגרסאות ישנות)
    c.execute("PRAGMA table_info(exams)")
    columns = [column[1] for column in c.fetchall()]
    if 'teacher_id' not in columns:
        try:
            c.execute("ALTER TABLE exams ADD COLUMN teacher_id TEXT")
        except:
            pass
    conn.commit()
    conn.close()

def save_to_db(name, subject, result):
    conn = sqlite3.connect('results.db', check_same_thread=False)
    c = conn.cursor()
    date_now = datetime.now().strftime("%d/%m/%Y %H:%M")
    c.execute("INSERT INTO exams (teacher_id, date, student_name, subject, result) VALUES (?, ?, ?, ?, ?)",
            (st.session_state.teacher_id, date_now, name, subject, result))
    conn.commit()
    conn.close()

def load_from_db(subject_filter="הכל"):
    conn = sqlite3.connect('results.db', check_same_thread=False)
    tid = st.session_state.teacher_id
    try:
        if subject_filter == "הכל":
            query = "SELECT date, student_name, subject, result FROM exams WHERE teacher_id = ?"
            df = pd.read_sql_query(query, conn, params=(tid,))
        else:
            query = "SELECT date, student_name, subject, result FROM exams WHERE teacher_id = ? AND subject = ?"
            df = pd.read_sql_query(query, conn, params=(tid, subject_filter))
    except:
        df = pd.DataFrame(columns=['date', 'student_name', 'subject', 'result'])
    conn.close()
    return df

# ==========================================
# 2. הגדרות AI - עקביות וחסכון במכסה
# ==========================================
def get_available_models():
    """Get list of available model names to try"""
    return [
        'models/gemini-2.0-flash-001',    # Specific version - more likely to work
        'models/gemini-2.5-flash',        # Newer Flash model
        'models/gemini-2.5-pro',          # Pro model (limited free tier)
        'models/gemini-pro',               # Fallback
        'models/gemini-1.5-pro'            # Another fallback
    ]

def init_gemini():
    if "GEMINI_API_KEY" not in st.secrets:
        st.error("🔑 מפתח API חסר ב-Secrets!")
        return None
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
    
    # הגדרות ליציבות ועקביות הציון
    generation_config = {
        "temperature": 0.0,
        "top_p": 1,
        "top_k": 1,
        "max_output_tokens": 2048,
    }

    # Try to get the first available model
    model_names = get_available_models()
    
    for model_name in model_names:
        try:
            model = genai.GenerativeModel(model_name=model_name, generation_config=generation_config)
            # Model object created successfully, return it
            return model
        except Exception as e:
            # If it's a 404, try next model
            error_str = str(e)
            if "404" in error_str or "not found" in error_str.lower():
                continue
            # For other errors, also try next model
            continue
    
    return None

def generate_content_with_fallback(prompt, image=None):
    """
    Try to generate content with multiple models, falling back if one doesn't exist or has quota issues
    """
    model_names = get_available_models()
    generation_config = {
        "temperature": 0.0,
        "top_p": 1,
        "top_k": 1,
        "max_output_tokens": 2048,
    }
    
    last_error = None
    for model_name in model_names:
        try:
            model = genai.GenerativeModel(model_name=model_name, generation_config=generation_config)
            
            # Prepare content
            if image:
                content = [prompt, image]
            else:
                content = prompt
            
            # Try to generate
            response = model.generate_content(content)
            return response
            
        except Exception as e:
            error_str = str(e)
            error_type = type(e).__name__
            
            # If it's a NotFound error, try next model
            if error_type == "NotFound" or "404" in error_str or ("not found" in error_str.lower() and "model" in error_str.lower()):
                last_error = e
                continue
            
            # If it's a ResourceExhausted (quota) error, try next model
            elif error_type == "ResourceExhausted" or "ResourceExhausted" in error_str:
                # Check if it's a permanent quota exhaustion (limit: 0) or rate limit
                is_permanent_quota = "limit: 0" in error_str
                
                if is_permanent_quota:
                    # Quota exhausted for this model - try next model
                    last_error = e
                    continue
                else:
                    # It's a rate limit (temporary) - also try next model first
                    last_error = e
                    continue
            
            else:
                # For other errors, raise immediately
                raise
    
    # If all models failed, raise the last error
    if last_error:
        raise last_error
    
    raise Exception("No models available")

# ==========================================
# 3. עיצוב הממשק
# ==========================================
st.set_page_config(page_title="EduCheck AI Pro", page_icon="🎓", layout="wide")
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Heebo:wght@400;600;800;900&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Heebo', sans-serif;
    }
    
    .stApp { 
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        color: white; 
        direction: rtl; 
        text-align: right; 
    }
    
    .white-bold { 
        color: #ffffff !important; 
        font-weight: 900 !important; 
        text-shadow: 0px 4px 10px rgba(0,0,0,0.5); 
        margin-bottom: 1.5rem;
    }
    
    .glass-card { 
        background: rgba(30, 41, 59, 0.6); 
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(56, 189, 248, 0.3); 
        border-radius: 20px; 
        padding: 30px; 
        margin-bottom: 25px; 
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
        transition: transform 0.3s ease, border-color 0.3s ease;
    }
    
    .glass-card:hover {
        border-color: rgba(56, 189, 248, 0.6);
    }
    
    .stButton>button { 
        background: linear-gradient(135deg, #38bdf8 0%, #2563eb 100%); 
        color: white !important; 
        font-weight: 800; 
        border-radius: 12px; 
        border: none; 
        height: 3.2em; 
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(37, 99, 235, 0.3);
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(37, 99, 235, 0.5);
        background: linear-gradient(135deg, #7dd3fc 0%, #1d4ed8 100%);
    }
    
    label, p, .stMarkdown { 
        color: #f8fafc !important; 
        font-weight: 600; 
    }
    
    /* שדות טקסט ובחירה */
    .stTextInput>div>div>input, .stSelectbox>div>div>div, .stTextArea>div>div>textarea {
        background-color: rgba(15, 23, 42, 0.6) !important;
        color: white !important;
        border: 1px solid #475569 !important;
        border-radius: 8px;
    }
    
    .stTextInput>div>div>input:focus, .stSelectbox>div>div>div:focus, .stTextArea>div>div>textarea:focus {
        border-color: #38bdf8 !important;
        box-shadow: 0 0 0 1px #38bdf8 !important;
    }

    /* עיצוב כרטיסיות (Tabs) */
    .stTabs [data-baseweb="tab-list"] {
        gap: 15px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: transparent;
        border-radius: 10px 10px 0 0;
        color: #94a3b8 !important;
        font-weight: 600;
        padding: 10px 15px;
    }
    .stTabs [aria-selected="true"] {
        color: #38bdf8 !important;
        font-weight: 800 !important;
        border-bottom: 3px solid #38bdf8 !important;
    }
</style>
""", unsafe_allow_html=True)

init_db()

# ==========================================
# 4. הממשק המרכזי
# ==========================================
st.markdown("<h1 class='white-bold' style='text-align: center;'>EduCheck AI Pro 🎓</h1>", unsafe_allow_html=True)
st.markdown(f"<p style='text-align: center;'>מחובר כמורה: {st.session_state.teacher_id}</p>", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["📄 בדיקת מבחן", "📊 ארכיון אישי", "⚙️ הגדרות"])

if 'rubric' not in st.session_state:
    st.session_state.rubric = "בדוק את התשובות על פי הבנה עמוקה של החומר ודיוק בפרטים."

with tab1:
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        student_name = st.text_input("שם התלמיד:")
        subject = st.selectbox("מקצוע:", SUBJECTS_LIST)
        
        rubric_file = st.file_uploader("מחוון תשובות (אופציונלי):", type=['jpg', 'jpeg', 'png'])
        if rubric_file and st.button("🔍 פענח מחוון מהקובץ"):
            try:
                # בדיקה שהקובץ הוא תמונה תקינה
                if rubric_file.type not in ['image/jpeg', 'image/jpg', 'image/png']:
                    st.error("❌ סוג קובץ לא נתמך. אנא העלה תמונה בפורמט JPG או PNG.")
                else:
                    # Check API key first
                    if "GEMINI_API_KEY" not in st.secrets:
                        st.error("❌ לא ניתן להתחבר ל-Gemini API. בדוק את המפתח API.")
                    else:
                        with st.spinner("מפענח..."):
                            img_r = Image.open(rubric_file)
                            
                            # Try with retry logic for rate limits and model fallback
                            max_retries = 3
                            retry_delay = 6
                            res_r = None
                            
                            for attempt in range(max_retries):
                                try:
                                    # --- שינוי פרומפט המחוון ל-JSON מובנה ---
                                    rubric_prompt = """
                                    פענח את המחוון מהתמונה. עליך להחזיר אך ורק מערך JSON (JSON array) תקין של אובייקטים.
                                    כל אובייקט ייצג שאלה במחוון ויכיל:
                                    "שאלה" (מספר השאלה), "תשובה" (התשובה המצופה), "ניקוד" (הניקוד המקסימלי).
                                    אל תוסיף שום מילה, סימון markdown, או טקסט לפני ואחרי ה-JSON.
                                    """
                                    res_r = generate_content_with_fallback(rubric_prompt, img_r)
                                    break
                                except Exception as retry_error:
                                    error_msg = str(retry_error)
                                    error_type_retry = type(retry_error).__name__
                                    
                                    # Check if it's a rate limit/quota error that can be retried
                                    is_rate_limit = (
                                        error_type_retry == "ResourceExhausted" or
                                        "Please retry in" in error_msg or
                                        "retry_delay" in error_msg or
                                        ("429" in error_msg and "quota" in error_msg.lower())
                                    )
                                    
                                    if is_rate_limit and attempt < max_retries - 1:
                                        # Extract retry delay from error message
                                        delay_match = re.search(r'retry in ([\d.]+)s', error_msg, re.IGNORECASE)
                                        if delay_match:
                                            retry_delay = float(delay_match.group(1)) + 1
                                        else:
                                            retry_delay = (attempt + 1) * 6
                                        
                                        time.sleep(retry_delay)
                                        continue
                                    else:
                                        raise
                            
                            if not res_r:
                                raise Exception("Failed to generate content after all retries")
                            
                            if res_r and res_r.text:
                                # --- מנגנון חילוץ בטוח של המחוון ---
                                raw_text = res_r.text
                                start_idx = raw_text.find('[')
                                end_idx = raw_text.rfind(']')
                                
                                if start_idx != -1 and end_idx != -1:
                                    json_str = raw_text[start_idx:end_idx+1]
                                    try:
                                        rubric_data = json.loads(json_str)
                                        df_rubric = pd.DataFrame(rubric_data)
                                        st.session_state.rubric = df_rubric.to_markdown(index=False)
                                        st.success("המחוון עודכן בהצלחה!")
                                        st.rerun()
                                    except json.JSONDecodeError:
                                        st.session_state.rubric = raw_text
                                        st.warning("המחוון פוענח כטקסט גולמי (ללא טבלה).")
                                else:
                                    st.session_state.rubric = raw_text
                                    st.warning("המחוון פוענח כטקסט גולמי (ללא טבלה).")
                                # ---------------------------------
                            else:
                                st.error("❌ לא התקבלה תשובה מה-AI. נסה שוב.")
                                
            except Exception as e:
                error_str = str(e)
                error_type = type(e).__name__
                
                # בדיקה אם זו שגיאת תמונה
                if "cannot identify image file" in error_str.lower() or "UnidentifiedImageError" in error_type:
                    st.error("❌ הקובץ לא מזוהה כתמונה תקינה. אנא העלה תמונה בפורמט JPG או PNG.")
                # בדיקה אם המודל לא נמצא
                elif error_type == "NotFound" or "404" in error_str or ("not found" in error_str.lower() and "model" in error_str.lower()):
                    st.error("❌ המודל לא נמצא או לא זמין. המערכת תנסה מודל אחר אוטומטית - נסה שוב.")
                # בדיקה מדויקת של ResourceExhausted
                elif error_type == "ResourceExhausted" or "ResourceExhausted" in error_str:
                    if "free_tier" in error_str.lower() or "limit: 0" in error_str:
                        st.error("⚠️ המכסה החינמית של Google Gemini API נגמרה. המערכת מנסה מודלים אחרים אוטומטית - נסה שוב בעוד כמה דקות.")
                    else:
                        st.error("⚠️ עומס על השרת של גוגל. נא להמתין כ-60 שניות ולנסות שוב.")
                elif "quota" in error_str.lower() and ("exceeded" in error_str.lower() or "limit" in error_str.lower()):
                    st.error("⚠️ המכסה של גוגל נגמרה. נא להמתין ולנסות שוב מאוחר יותר.")
                else:
                    st.error(f"❌ שגיאה בפענוח המחוון: {error_str}")

        st.session_state.rubric = st.text_area("מחוון הבדיקה הנוכחי:", value=st.session_state.rubric, height=150)

    with col2:
        upload_method = st.radio("שיטת העלאה:", ["קובץ", "מצלמה"])
        file = st.file_uploader("העלה מבחן:", type=['jpg', 'jpeg', 'png']) if upload_method == "קובץ" else st.camera_input("צלם מבחן")
        
        if st.button("🚀 בדוק מבחן"):
            if not file or not student_name:
                st.warning("נא למלא שם תלמיד ולהעלות קובץ.")
            else:
                try:
                    with st.spinner("מנתח את המבחן בצורה עקבית..."):
                        img = Image.open(file)
                        
                        # Check API key first
                        if "GEMINI_API_KEY" not in st.secrets:
                            st.error("❌ לא ניתן להתחבר ל-Gemini API. בדוק את המפתח API.")
                        else:
                            # --- פקודה משודרגת למבחן עצמו (שלב 1) ---
                            prompt = f"""
                            משימה: מומחה פדגוגי לבדיקת מבחנים בכתב יד.
                            מקצוע: {subject} | שם התלמיד: {student_name}

                            הנחיות עבודה קריטיות:
                            1. זיהוי טקסט (OCR): פענח את כתב היד בתמונה בצורה מדויקת.
                            2. ניתוח מחוון: השתמש במחוון הבא כקריטריון יחיד לציון: {st.session_state.rubric}
                            3. בדיקה שאלה-שאלה: לכל שאלה שזוהתה, השווה את תשובת התלמיד למחוון.
                            4. מתן ניקוד: אם התשובה חלקית, תן ניקוד יחסי והסבר למה.

                            פורמט פלט נדרש (Markdown):
                            ## דו"ח בדיקה פדגוגי: {student_name}
                            ---
                            |   מס' שאלה | מה התלמיד כתב | ניקוד | הסבר והערות רחב|
                            | :--- | :--- | :--- | :--- |
                            | [מספר] | [תמצית תשובת התלמיד] | [X/Y] | [למה ירד ניקוד או מה היה חסר] |

                            ---
                            **ציון סופי משוקלל: [ציון סופי]**

                            **משוב אישי מעצים:** [כתוב משפט אחד על חוזקה שהפגין התלמיד במבחן זה]

                            **נקודות לשיפור ללמידה הבאה:**
                            * [נקודה ספציפית שהתלמיד צריך לחזור עליה]
                            """
                            # ----------------------------------------
                            
                            # הקטנת תמונה לחיסכון במכסה
                            img.thumbnail((1600, 1600))
                            
                            # Try with retry logic for rate limits and model fallback
                            max_retries = 3
                            retry_delay = 6
                            response = None
                            
                            for attempt in range(max_retries):
                                try:
                                    response = generate_content_with_fallback(prompt, img)
                                    break
                                except Exception as retry_error:
                                    error_msg = str(retry_error)
                                    error_type_retry = type(retry_error).__name__
                                    
                                    # Check if it's a rate limit/quota error that can be retried
                                    is_rate_limit = (
                                        error_type_retry == "ResourceExhausted" or
                                        "Please retry in" in error_msg or
                                        "retry_delay" in error_msg or
                                        ("429" in error_msg and "quota" in error_msg.lower())
                                    )
                                    
                                    if is_rate_limit and attempt < max_retries - 1:
                                        # Extract retry delay from error message
                                        delay_match = re.search(r'retry in ([\d.]+)s', error_msg, re.IGNORECASE)
                                        if delay_match:
                                            retry_delay = float(delay_match.group(1)) + 1
                                        else:
                                            retry_delay = (attempt + 1) * 6
                                        
                                        time.sleep(retry_delay)
                                        continue
                                    else:
                                        raise
                            
                            if not response:
                                raise Exception("Failed to generate content after all retries")
                            
                            if response and response.text:
                                save_to_db(student_name, subject, response.text)
                                st.success("הבדיקה הושלמה!")
                                st.markdown(response.text)
                            else:
                                st.error("❌ לא התקבלה תשובה מה-AI. נסה שוב.")
                                
                except Exception as e:
                    error_str = str(e)
                    error_type = type(e).__name__
                    
                    # בדיקה אם המודל לא נמצא
                    if error_type == "NotFound" or "404" in error_str or ("not found" in error_str.lower() and "model" in error_str.lower()):
                        st.error("❌ המודל לא נמצא או לא זמין. המערכת תנסה מודל אחר אוטומטית - נסה שוב.")
                    # בדיקה מדויקת של ResourceExhausted
                    elif error_type == "ResourceExhausted" or "ResourceExhausted" in error_str:
                        if "free_tier" in error_str.lower() or "limit: 0" in error_str:
                            st.error("⚠️ המכסה החינמית של Google Gemini API נגמרה. המערכת מנסה מודלים אחרים אוטומטית - נסה שוב בעוד כמה דקות.")
                        else:
                            st.error("⚠️ המכסה של גוגל נגמרה לדקה זו. נא להמתין דקה אחת בדיוק ולנסות שוב.")
                    elif "quota" in error_str.lower() and ("exceeded" in error_str.lower() or "limit" in error_str.lower()):
                        st.error("⚠️ המכסה של גוגל נגמרה. נא להמתין ולנסות שוב מאוחר יותר.")
                    else:
                        st.error(f"❌ שגיאה בניתוח: {error_str}")
    st.markdown("</div>", unsafe_allow_html=True)

with tab2:
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    st.subheader(f"ארכיון אישי - מורה {st.session_state.teacher_id}")
    filter_sub = st.selectbox("סנן לפי מקצוע:", ["הכל"] + SUBJECTS_LIST)
    df = load_from_db(filter_sub)
    if not df.empty:
        st.dataframe(df, use_container_width=True)
        st.download_button("📥 הורד אקסל (CSV)", data=df.to_csv(index=False).encode('utf-8-sig'), file_name=f"grades_{st.session_state.teacher_id}.csv")
    else:
        st.info("לא נמצאו נתונים בארכיון האישי שלך.")
    st.markdown("</div>", unsafe_allow_html=True)

with tab3:
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    if st.button("🔓 התנתקות מהמערכת"):
        st.session_state.authenticated = False
        st.session_state.teacher_id = None
        st.rerun()
    st.markdown("---")
    if st.button("🔴 מחיקת הארכיון האישי שלי בלבד"):
        conn = sqlite3.connect('results.db')
        conn.execute("DELETE FROM exams WHERE teacher_id = ?", (st.session_state.teacher_id,))
        conn.commit()
        conn.close()
        st.success("הארכיון האישי שלך נמחק."); st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)
