import streamlit as st
import google.generativeai as genai
from PIL import Image
import os

# --- 1. עיצוב גרפי מתקדם (CSS Custom Styling) ---
st.set_page_config(page_title="EduCheck Pro", layout="wide", page_icon="📝")

st.markdown("""
    <style>
    /* רקע כללי הדרגתי ונעים */
    .stApp {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        font-family: 'Assistant', sans-serif;
    }
    
    /* עיצוב כותרת ראשית */
    .main-header {
        background: linear-gradient(90deg, #4facfe 0%, #00f2fe 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        font-size: 3rem;
        font-weight: 800;
        margin-bottom: 10px;
    }
    
    /* עיצוב תיבות (Cards) */
    div.stButton > button {
        background: linear-gradient(to right, #6a11cb 0%, #2575fc 100%);
        color: white;
        border-radius: 15px;
        padding: 15px;
        font-size: 18px;
        font-weight: bold;
        border: none;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        transition: all 0.3s ease;
    }
    div.stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0,0,0,0.15);
    }
    
    /* עיצוב ה-Sidebar */
    [data-testid="stSidebar"] {
        background-color: #ffffff;
        border-left: 1px solid #e0e0e0;
        box-shadow: 2px 0 10px rgba(0,0,0,0.05);
    }
    
    /* עיצוב תיבות טקסט */
    .stTextArea textarea {
        border-radius: 15px;
        border: 1px solid #d1d9e6;
        padding: 15px;
        background-color: #ffffff;
    }

    /* כותרות משנה */
    h2, h3 {
        color: #2c3e50;
        border-right: 5px solid #4facfe;
        padding-right: 15px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. לוגיקה וחיבורים ---
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("Missing API Key!")
    st.stop()

st.markdown("<h1 class='main-header'>EduCheck Pro</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #5c6b73; font-size: 1.2rem;'>העוזר החכם שלך לבדיקת מבחנים וניהול כיתה</p>", unsafe_allow_html=True)

# כניסת מורה
st.sidebar.markdown("### 🔐 מרחב מורה אישי")
teacher_id = st.sidebar.text_input("הכנס קוד מורה:", type="password", placeholder="למשל: מספר טלפון")

if not teacher_id:
    st.info("👋 ברוכים הבאים! אנא הזדהו בסרגל הצדי כדי לגשת למאגר האישי שלכם.")
    st.image("https://img.freepik.com/free-vector/modern-online-education-concept-with-flat-design_23-2147926189.jpg", use_column_width=True)
    st.stop()

teacher_folder = f"data_{teacher_id}"
if not os.path.exists(teacher_folder):
    os.makedirs(teacher_folder)

# --- 3. סגנון בדיקה אישי ---
st.sidebar.divider()
st.sidebar.markdown("### ⚙️ הגדרות בדיקה")
grading_style = st.sidebar.text_area("הסגנון שלך:", placeholder="למשל: 'היה מעודד', 'שים דגש על ניסוח', 'התעלם משגיאות כתיב'...")

# --- 4. ניהול תלמידים ---
st.sidebar.markdown("### 👥 מאגר תלמידים")
action = st.sidebar.radio("פעולה:", ["선택 (תלמיד קיים)", "+ חדש (רישום תלמיד)"])
existing_students = os.listdir(teacher_folder)
selected_student = None
sample_images = []

if "+ חדש" in action:
    new_name = st.sidebar.text_input("שם מלא:")
    s1 = st.sidebar.file_uploader("דגימה 1", type=['png', 'jpg', 'jpeg'], key="s1")
    s2 = st.sidebar.file_uploader("דגימה 2", type=['png', 'jpg', 'jpeg'], key="s2")
    s3 = st.sidebar.file_uploader("דגימה 3", type=['png', 'jpg', 'jpeg'], key="s3")
    if st.sidebar.button("✨ שמור תלמיד במערכת"):
        if new_name and s1 and s2 and s3:
            s_path = os.path.join(teacher_folder, new_name)
            if not os.path.exists(s_path): os.makedirs(s_path)
            for i, s in enumerate([s1, s2, s3]):
                with open(os.path.join(s_path, f"sample_{i}.png"), "wb") as f:
                    f.write(s.getbuffer())
            st.sidebar.success("התלמיד נרשם בהצלחה!")
            st.rerun()
else:
    if existing_students:
        selected_student = st.sidebar.selectbox("בחר מהרשימה:", existing_students)
        s_path = os.path.join(teacher_folder, selected_student)
        for i in range(3):
            img_p = os.path.join(s_path, f"sample_{i}.png")
            if os.path.exists(img_p):
                sample_images.append(Image.open(img_p))

# --- 5. אזור העבודה המרכזי ---
st.container()
col1, col2 = st.columns([1, 1], gap="large")

with col1:
    st.markdown("### 📸 העלאת המבחן")
    st.write("צלמו את דף המבחן של התלמיד והעלו כאן:")
    exam_file = st.file_uploader("", type=['png', 'jpg', 'jpeg'])

with col2:
    st.markdown("### 🎯 הגדרת מחוון")
    st.write("מהן התשובות הנכונות במבחן זה?")
    rubric = st.text_area("", placeholder="למשל: שאלה 1 - פוטוסינתזה, שאלה 2 - חמצן...", height=120)

st.divider()

if st.button("התחל בדיקה חכמה 🚀"):
    if selected_student and sample_images and exam_file and rubric:
        with st.status("🔍 ה-AI מנתח את המבחן...", expanded=True) as status:
            try:
                model = genai.GenerativeModel('gemini-1.5-flash')
                img_exam = Image.open(exam_file)
                
                prompt = f"""
                You are a smart teacher's assistant.
                STYLE: {grading_style if grading_style else "Professional and balanced."}
                STUDENT: {selected_student}
                1. Use the handwriting samples to recognize the student's text.
                2. Grade based on this rubric: {rubric}
                3. Respond in Hebrew. Be positive and helpful.
                """
                
                response = model.generate_content([prompt] + sample_images + [img_exam])
                status.update(label="✅ ניתוח הושלם!", state="complete", expanded=False)
                
                st.markdown("---")
                st.markdown(f"## 📋 תוצאות עבור: {selected_student}")
                st.info(response.text)
                
            except Exception as e:
                st.error(f"אירעה שגיאה בתקשורת עם הבינה המלאכותית: {e}")
    else:
        st.warning("שימו לב: יש לבחור תלמיד, להעלות מבחן ולהזין מחוון.")
