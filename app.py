import streamlit as st
import google.generativeai as genai
from PIL import Image

# הגדרות תצוגה לעברית (RTL)
st.markdown("""
    <style>
    .stMarkdown, .stTextArea, .stTitle {
        direction: rtl;
        text-align: right;
    }
    </style>
    """, unsafe_allow_html=True)

# בחירת שפה
lang = st.sidebar.selectbox("Language / שפה", ["עברית", "English"])

# טקסטים לפי שפה
texts = {
    "עברית": {
        "title": "📝 EduCheck AI - בדיקה מהירה",
        "label_api": "הכנס מפתח API:",
        "label_rubric": "הכנס מחוון (תשובה נכונה):",
        "label_file": "העלה צילום מבחן:",
        "btn": "בדוק מבחן עכשיו",
        "wait": "מנתח במהירות...",
        "result": "תוצאות הבדיקה:"
    },
    "English": {
        "title": "📝 EduCheck AI - Fast Grader",
        "label_api": "Enter API Key:",
        "label_rubric": "Enter Rubric (Correct Answer):",
        "label_file": "Upload Exam Photo:",
        "btn": "Grade Now",
        "wait": "Analyzing fast...",
        "result": "Grading Results:"
    }
}

t = texts[lang]

st.title(t["title"])

# הגדרת API
api_key = st.sidebar.text_input(t["label_api"], type="password")

if api_key:
    genai.configure(api_key=api_key)
    
    rubric = st.text_area(t["label_rubric"])
    uploaded_file = st.file_uploader(t["label_file"], type=['png', 'jpg', 'jpeg'])

    if st.button(t["btn"]):
        if uploaded_file and rubric:
            with st.spinner(t["wait"]):
                img = Image.open(uploaded_file)
                # שימוש במודל Flash המהיר
                model = genai.GenerativeModel('gemini-1.5-flash')
                
                prompt = f"Role: Professional Teacher. Task: Grade the student's answer in the image based on this rubric: {rubric}. Respond in {lang} language."
                
                response = model.generate_content([prompt, img])
                
                st.subheader(t["result"])
                st.write(response.text)
        else:
            st.warning("Please fill all fields / נא למלא את כל השדות")
else:
    st.info("Please enter API Key in the sidebar / נא להזין מפתח API בצד")
