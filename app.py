import streamlit as st
import google.generativeai as genai
from PIL import Image

st.set_page_config(page_title="EduCheck AI - מומחה כתב יד", layout="centered")
st.title("📝 EduCheck AI")
st.subheader("סורק מבחנים חכם (גם לכתב יד מאתגר)")

# הגדרת המפתח
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("אנא הגדר מפתח API ב-Secrets")

# ממשק המשתמש
rubric = st.text_area("מה התשובה הנכונה? (המחוון):", height=150)
uploaded_file = st.file_uploader("צלם או העלה את המבחן:", type=['png', 'jpg', 'jpeg'])

if st.button("בדוק מבחן"):
    if uploaded_file and rubric:
        with st.spinner('מפענח כתב יד ומנתח נתונים...'):
            try:
                img = Image.open(uploaded_file)
                
                # שימוש במודל החזק ביותר לניתוח תמונות
                model = genai.GenerativeModel('gemini-pro-vision'
                
                # הפרומפט המשופר - כאן קורה הקסם
                instructions = f"""
                אתה מורה מומחה לפענוח כתב יד של תלמידים. 
                משימה:
                1. קרא בריכוז רב את הטקסט בכתב היד שבתמונה (גם אם הוא לא ברור או מרוח).
                2. השווה את מה שכתוב בתמונה למחוון הבא: {rubric}.
                3. תן ציון מ-0 עד 100.
                4. הסבר בנקודות: מה התלמיד כתב נכון ומה חסר לו.
                
                חשוב: אם הכתב קשה לקריאה, נסה להבין מההקשר של המשפט מה המילה הסבירה ביותר שנכתבה.
                ענה בעברית ברורה.
                """
                
                response = model.generate_content([instructions, img])
                
                st.success("הבדיקה הושלמה!")
                st.markdown("---")
                st.markdown("### 📋 תוצאות הבדיקה:")
                st.write(response.text)
                
            except Exception as e:
                st.error(f"שגיאה טכנית: {e}")
    else:
        st.warning("נא להזין מחוון ולהעלות תמונה.")
