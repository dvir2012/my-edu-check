import streamlit as st
import google.generativeai as genai
from PIL import Image

# הגדרת ה-API מה-Secrets
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
except:
    st.error("Missing API Key in Secrets!")

st.title("📝 EduCheck AI")

# שימוש במודל בסיסי שיש לו הכי פחות שגיאות 404
model = genai.GenerativeModel('gemini-1.5-flash')

rubric = st.text_area("הכנס מחוון / Rubric:")
uploaded_file = st.file_uploader("העלה תמונה:", type=['png', 'jpg', 'jpeg'])

if st.button("בדוק מבחן"):
    if uploaded_file and rubric:
        with st.spinner("מנתח..."):
            try:
                img = Image.open(uploaded_file)
                # שליחת הבקשה בצורה הכי פשוטה
                response = model.generate_content(["Grade this based on rubric: " + rubric, img])
                st.write(response.text)
            except Exception as e:
                st.error(f"עדיין יש שגיאה: {e}")
