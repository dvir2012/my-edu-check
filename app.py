import streamlit as st
import google.generativeai as genai
from PIL import Image

st.set_page_config(page_title="EduCheck AI - מפענח כתב יד", layout="wide")
st.title("📝 EduCheck AI - פענוח לפי דוגמת כתב")

# פתרון לשגיאת ה-404: הגדרת המודל בצורה מפורשת
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("חסר מפתח API ב-Secrets!")

col1, col2 = st.columns(2)

with col1:
    st.subheader("1. דף לימוד אותיות")
    handwriting_sample = st.file_uploader("העלה צילום שבו כתבת 'זה א', 'זה ב' וכו':", type=['png', 'jpg', 'jpeg'], key="sample")

with col2:
    st.subheader("2. דף המבחן")
    exam_image = st.file_uploader("העלה את המבחן שצריך לפענח:", type=['png', 'jpg', 'jpeg'], key="exam")

rubric = st.text_area("מחוון (התשובה הנכונה שאתה מצפה לה):")

if st.button("למד כתב ובדוק מבחן 🚀"):
    if handwriting_sample and exam_image and rubric:
        with st.spinner('מנתח את כתב היד...'):
            try:
                # שימוש במודל היציב ביותר
                model = genai.GenerativeModel('gemini-1.5-flash')
                
                sample_img = Image.open(handwriting_sample)
                exam_img = Image.open(exam_image)
                
                # הנחיה (Prompt) חזקה שמדגישה את הלימוד
                prompt = f"""
                משימה: פענוח כתב יד קשה.
                
                שלב 1: תסתכל בתמונה הראשונה (דף הלימוד). למד איך הכותב מצייר כל אות וכל מילה. זה ה'מפתח' שלך לפענוח.
                שלב 2: תשתמש בידע שרכשת בשלב 1 כדי לקרוא את הטקסט בתמונה השנייה (המבחן).
                שלב 3: השווה את מה שפענחת למחוון הבא: {rubric}.
                
                ענה בעברית:
                1. מה כתוב במבחן (ציטוט)?
                2. ציון סופי.
                3. הסבר קצר.
                """
                
                # שליחת הבקשה
                response = model.generate_content([prompt, sample_img, exam_img])
                
                st.success("הפענוח הושלם!")
                st.markdown("---")
                st.write(response.text)
                
            except Exception as e:
                st.error(f"קרתה שגיאה: {e}")
                st.info("אם השגיאה היא 404, נסה להחליף את 'gemini-1.5-flash' ב-'gemini-pro-vision' בקוד.")
    else:
        st.warning("נא להעלות את שתי התמונות ולכתוב מחוון.")
