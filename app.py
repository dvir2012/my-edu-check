import streamlit as st
import google.generativeai as genai
from PIL import Image

# הגדרות שפה ותצוגה
st.set_page_config(page_title="EduCheck AI", layout="centered")

# עיצוב לעברית
st.markdown("""
    <style>
    .stMarkdown, .stTextArea, .stTitle, .stAlert {
        direction: rtl;
        text-align: right;
    }
    </style>
    """, unsafe_allow_html=True)

# בחירת שפה בסרגל הצד
lang = st.sidebar.radio("Select Language / בחר שפה", ["עברית", "English"])

if lang == "עברית":
    title = "📝 EduCheck AI - בדיקה מהירה"
    label_api = "הכנס מפתח API (בצד):"
    label_rubric = "הכנס את המחוון (מה התשובה הנכונה?):"
    label_file = "העלה צילום של המבחן:"
    btn_text = "בדוק מבחן"
    wait_text = "מנתח... זה ייקח כמה שניות"
else:
    title = "📝 EduCheck AI - Fast Grader"
    label_api = "Enter API Key (sidebar):"
    label_rubric = "Enter Rubric / Correct Answer:"
    label_file = "Upload Exam Photo:"
    btn_text = "Grade Now"
    wait_text = "Analyzing... please wait"

st.title(title)

# הגדרת API
api_key = st.sidebar.text_input("API Key", type="password")

if api_key:
    genai.configure(api_key=api_key)
    
    rubric = st.text_area(label_rubric)
    uploaded_file = st.file_uploader(label_file, type=['png', 'jpg', 'jpeg'])

    if st.button(btn_text):
        if uploaded_file and rubric:
            with st.spinner(wait_text):
                try:
                    img = Image.open(uploaded_file)
                    # שימוש במודל Flash למהירות מקסימלית
                    model = genai.GenerativeModel('gemini-1.5-pro')
                    prompt = f"Role: Teacher. Task: Grade the student's answer based on this rubric: {rubric}. Language: {lang}."
                    response = model.generate_content([prompt, img], stream=False)
                    st.success("✅ Done / בוצע")
                    st.write(response.text)
                except Exception as e:
                    st.error(f"Error: {e}")
        else:
            st.warning("Please fill all fields / נא למלא את כל השדות")
else:
    st.info("👈 Please enter your API Key in the sidebar to start / נא להזין מפתח API בסרגל הצד")
