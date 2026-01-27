import streamlit as st
import google.generativeai as genai
from PIL import Image

# כותרת פשוטה
st.title("📝 EduCheck AI")

# בדיקה אם יש מפתח
if "GOOGLE_API_KEY" not in st.secrets:
    st.error("Please add GOOGLE_API_KEY to Streamlit Secrets!")
    st.stop()

genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

rubric = st.text_area("הכנס מחוון (תשובה נכונה):")
uploaded_file = st.file_uploader("העלה צילום מבחן:", type=['png', 'jpg', 'jpeg'])

if st.button("בדוק מבחן"):
    if uploaded_file and rubric:
        with st.spinner("בודק..."):
            try:
                img = Image.open(uploaded_file)
                # נסיון להשתמש במודל הכי חדש
                model = genai.GenerativeModel('gemini-1.5-flash')
                response = model.generate_content([f"Grade this: {rubric}", img])
                st.markdown(response.text)
            except Exception as e:
                st.error(f"שגיאה: {e}")
    else:
        st.warning("נא להעלות תמונה ולכתוב מחוון.")
