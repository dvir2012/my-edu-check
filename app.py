import streamlit as st
import google.generativeai as genai
from PIL import Image

st.set_page_config(page_title="EduCheck Pro AI", layout="wide")
st.title("📝 EduCheck Pro - למידת כתב יד עמוקה")

# הגדרת ה-API
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("חסר מפתח API ב-Secrets!")

# ממשק העלאת קבצים
st.subheader("💡 שלב 1: למד את ה-AI את כתב היד שלך")
col1, col2 = st.columns(2)
with col1:
    sample1 = st.file_uploader("דף אותיות 1 (למשל א-ל):", type=['png', 'jpg', 'jpeg'])
with col2:
    sample2 = st.file_uploader("דף אותיות 2 (למשל מ-ת + מספרים):", type=['png', 'jpg', 'jpeg'])

st.subheader("✍️ שלב 2: העלה את המבחן")
exam_img = st.file_uploader("תמונת המבחן לפענוח:", type=['png', 'jpg', 'jpeg'])

rubric = st.text_area("מחוון (התשובה הנכונה):")

if st.button("למד ובדוק מבחן 🚀"):
    if sample1 and exam_img and rubric:
        with st.spinner('ה-AI לומד את האותיות ומנתח...'):
            try:
                # שימוש במודל Pro - חזק יותר בניתוח תמונות
                model = genai.GenerativeModel(model_name="gemini-1.5-pro")
                
                # הכנת התמונות
                img_sample1 = Image.open(sample1)
                img_exam = Image.open(exam_img)
                inputs = [img_sample1]
                
                if sample2:
                    img_sample2 = Image.open(sample2)
                    inputs.append(img_sample2)
                
                inputs.append(img_exam)
                
                # הנחיה מפורטת וממוקדת
                prompt = f"""
                אתה מומחה לפענוח כתב יד קשה. 
                התמונות הראשונות שהעליתי הן 'מפתח הפענוח' שלך. 
                תסתכל על האותיות שם, תלמד את הזוויות, העובי והצורה שבה הכותב כותב כל אות.
                
                עכשיו, תשתמש בידע הזה כדי לקרוא את התמונה האחרונה (המבחן).
                
                לאחר הפענוח, בצע את המשימות הבאות:
                1. תמלל את מה שכתוב במבחן מילה במילה.
                2. השווה למחוון הבא: {rubric}
                3. תן ציון והסבר בפירוט.
                
                ענה בעברית ברורה.
                """
                
                inputs.append(prompt)
                
                response = model.generate_content(inputs)
                
                st.success("הבדיקה הושלמה!")
                st.markdown("---")
                st.write(response.text)
                
            except Exception as e:
                st.error(f"שגיאה: {e}")
                st.info("אם השגיאה נמשכת, וודא שמפתח ה-API שלך בתוקף ושחשבון ה-Google Cloud שלך פעיל.")
    else:
        st.warning("חובה להעלות לפחות דף אותיות אחד ואת דף המבחן.")
