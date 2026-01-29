import streamlit as st
import google.generativeai as genai
from PIL import Image
import os

# --- 1. הגדרות שפה ועיצוב ---
st.set_page_config(page_title="EduCheck Pro - MultiLang", layout="wide", page_icon="📝")

# הוספת בורר שפה בסרגל הצדי
language = st.sidebar.selectbox("🌐 בחר שפה / اختر اللغة", ["עברית", "العربية"])

# הגדרת צבעים לפי שפה
if language == "עברית":
    primary_color = "#4facfe"
    secondary_color = "#00f2fe"
    text_align = "right"
    direction = "rtl"
    title = "EduCheck Pro"
    subtitle = "העוזר החכם שלך לבדיקת מבחנים"
else:
    primary_color = "#2ecc71" # ירוק לערבית
    secondary_color = "#27ae60"
    text_align = "right"
    direction = "rtl"
    title = "إيدوشيك برو"
    subtitle = "מساعدך الذكي לתכנון ובדיקת מבחנים"

st.markdown(f"""
    <style>
    .stApp {{
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        font-family: 'Assistant', sans-serif;
        direction: {direction};
        text-align: {text_align};
    }}
    .main-header {{
        background: linear-gradient(90deg, {primary_color} 0%, {secondary_color} 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        font-size: 3rem;
        font-weight: 800;
    }}
    div.stButton > button {{
        background: linear-gradient(to right, {primary_color} 0%, {secondary_color} 100%);
        color: white;
        border-radius: 15px;
        width: 100%;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 2. חיבור ל-API ---
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("Missing API Key!")
    st.stop()

st.markdown(f"<h1 class='main-header'>{title}</h1>", unsafe_allow_html=True)
st.markdown(f"<p style='text-align: center; color: #5c6b73;'>{subtitle}</p>", unsafe_allow_html=True)

# --- 3. סרגל צדי (Sidebar) ---
st.sidebar.markdown(f"### 🔐 {'מרחב מורה' if language=='עברית' else 'منطقة المعلم'}")
teacher_id = st.sidebar.text_input("ID:", type="password")

if not teacher_id:
    st.info("Please login in the sidebar / الرجاء تسجيل الدخول")
    st.stop()

teacher_folder = f"data_{teacher_id}"
if not os.path.exists(teacher_folder):
    os.makedirs(teacher_folder)

# --- 4. הגדרות וניהול תלמידים ---
grading_style = st.sidebar.text_area("Style / أسلوب التقييم:", placeholder="ציין דגשים מיוחדים...")

st.sidebar.divider()
action = st.sidebar.radio("Action:", ["선택 (תלמיד קיים)", "+ חדש"])
existing_students = os.listdir(teacher_folder)
selected_student = None
sample_images = []

if "+ חדש" in action:
    new_name = st.sidebar.text_input("Name:")
    # ... (כאן נשאר הקוד המקורי שלך לרישום תלמיד)
else:
    if existing_students:
        selected_student = st.sidebar.selectbox("Student:", existing_students)
        s_path = os.path.join(teacher_folder, selected_student)
        for i in range(3):
            img_p = os.path.join(s_path, f"sample_{i}.png")
            if os.path.exists(img_p):
                sample_images.append(Image.open(img_p))

# --- 5. אזור העבודה המרכזי ---
col1, col2 = st.columns(2)

with col1:
    label_exam = "📸 העלאת מבחן" if language=="עברית" else "📸 تحميل الامتحان"
    st.markdown(f"### {label_exam}")
    exam_file = st.file_uploader("", type=['png', 'jpg', 'jpeg'], key="exam")

with col2:
    label_rubric = "🎯 מחוון" if language=="עברית" else "🎯 نموذج الإجابة"
    st.markdown(f"### {label_rubric}")
    rubric = st.text_area("", placeholder="הכנס תשובות נכונות...", height=120, key="rubric")

if st.button("🚀 " + ("בדוק מבחן" if language=="עברית" else "ابدأ التقييم")):
    if selected_student and exam_file and rubric:
        with st.spinner("Analyzing..."):
            try:
                model = genai.GenerativeModel('gemini-1.5-flash')
                img_exam = Image.open(exam_file)
                
                # התאמת הפקודה לשפה הנבחרת
                prompt = f"""
                Analyze this exam for student: {selected_student}.
                Use the provided rubric: {rubric}.
                The teacher's style is: {grading_style}.
                IMPORTANT: Respond ONLY in {language}.
                If there are handwriting samples, use them to better understand the student's writing.
                """
                
                response = model.generate_content([prompt] + sample_images + [img_exam])
                
                st.markdown("---")
                st.markdown(f"### Results for {selected_student} / نتائج {selected_student}")
                st.success(response.text)
                
            except Exception as e:
                st.error(f"Error: {e}")
    else:
        st.warning("Please fill all fields / الرجاء ملء جميع الحقول")
