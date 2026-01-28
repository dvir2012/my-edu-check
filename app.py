import streamlit as st
import google.generativeai as genai
from PIL import Image

st.set_page_config(page_title="EduCheck AI - לומד כתב יד", layout="wide")
st.title("📝 EduCheck AI - לומד את כתב היד שלך")

# וידוא מפתח API
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("חסר מפתח API בהגדרות!")

col1, col2 = st.columns(2)

with col1:
    st.header("1. לימוד הכתב")
    handwriting_sample = st.file_uploader("העלה דף עם דוגמאות לכתב שלך (למשל א', ב', ג'):", type=['png', 'jpg', 'jpeg'], key="sample")

with col2:
    st.header("2. המבחן לבדיקה")
    exam_image = st.file_uploader("העלה את דף המבחן שצריך לבדוק:", type=['png', 'jpg', 'jpeg'], key="exam")

rubric = st.text_area("מה התשובה הנכונה? (המחוון):")

if st.button("נתח ולמד כתב יד 🚀"):
    if handwriting_sample and exam_image and rubric:
        with st.spinner('לומד את הכתב ומפענח את המבחן...'):
            try:
                model = genai.GenerativeModel('gemini-1.5-flash')
                sample_img = Image.open(handwriting_sample)
                exam_img = Image.open(exam_image)
                
                prompt = f"""
                אתה עוזר הוראה חכם. קיבלת שתי תמונות:
                1. תמונת דוגמה של כתב היד (כדי שתלמד איך הכותב כותב אותיות).
                2. תמונת המבחן.
                
                השתמש בדוגמה כדי לפענח את המבחן. 
                השווה את התשובה שמצאת במבחן למחוון הבא: {rubric}.
                תן ציון והסבר בפירוט מה נכתב במבחן.
                """
                
                response = model.generate_content([prompt, sample_img, exam_img])
                st.success("הפענוח הושלם!")
                st.markdown("### תוצאות:")
                st.write(response.text)
            except Exception as e:
                st.error(f"שגיאה: {e}")
    else:
        st.warning("בבקשה תעלה את שתי התמונות ותכתוב מחוון.")
