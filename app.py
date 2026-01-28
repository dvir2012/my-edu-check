import streamlit as st
import google.generativeai as genai
from PIL import Image

# עיצוב דף רחב ויפה
st.set_page_config(page_title="EduCheck Pro - מילון כתב יד", layout="wide")

# CSS לעיצוב כפתורים וממשק
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stButton>button { width: 100%; border-radius: 20px; height: 3em; background-color: #4CAF50; color: white; }
    .sidebar .sidebar-content { background-image: linear-gradient(#2e7d32, #1b5e20); color: white; }
    </style>
    """, unsafe_allow_html=True)

st.title("📝 EduCheck Pro")
st.subheader("מערכת בדיקה חכמה עם לימוד אותיות אישי")

# הגדרת ה-API
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("יש להגדיר API Key ב-Secrets")

# סרגל צדי ללימוד אותיות
st.sidebar.header("🔤 סרגל לימוד אותיות")
st.sidebar.write("העלה תמונה לכל אות כדי לאמן את ה-AI:")

alphabet = ['א', 'ב', 'ג', 'ד', 'ה', 'ו', 'ז', 'ח', 'ט', 'י', 'כ', 'ל', 'מ', 'נ', 'ס', 'ע', 'פ', 'צ', 'ק', 'ר', 'ש', 'ת']
letter_images = {}

for letter in alphabet:
    with st.sidebar.expander(f"אות {letter}"):
        img = st.file_uploader(f"העלה {letter}", type=['png', 'jpg', 'jpeg'], key=f"letter_{letter}")
        if img:
            letter_images[letter] = Image.open(img)

# מסך ראשי - העלאת המבחן
st.divider()
col_main1, col_main2 = st.columns([1, 1])

with col_main1:
    st.header("📸 העלאת המבחן")
    exam_img_file = st.file_uploader("צילום תשובת התלמיד:", type=['png', 'jpg', 'jpeg'])

with col_main2:
    st.header("🎯 המחוון")
    rubric = st.text_area("מה התשובה הנכונה?", height=150, placeholder="למשל: על התלמיד להסביר ש...")

if st.button("הפעל ניתוח חכם 🚀"):
    if exam_img_file and rubric:
        with st.spinner('מנתח את הכתב לפי המילון האישי שלך...'):
            try:
                # שימוש במודל החזק ביותר למשימה
                model = genai.GenerativeModel('gemini-1.5-pro')
                
                # בניית רשימת הקבצים לשליחה ל-AI
                content_to_send = []
                
                # הוספת האותיות שהועלו כ"מילון"
                instructions = "אתה מומחה לפענוח כתב יד. השתמש בתמונות המצורפות כ'מילון' לכתב היד של הכותב:\n"
                for letter, img in letter_images.items():
                    instructions += f"התמונה הבאה היא האות {letter}.\n"
                    content_to_send.append(img)
                
                # הוספת המבחן וההנחיה הסופית
                final_prompt = f"""
                {instructions}
                כעת, השתמש במילון האותיות שלמדת כדי לקרוא את התמונה האחרונה (המבחן).
                1. תמלל את הטקסט.
                2. השווה למחוון: {rubric}
                3. תן ציון והסבר בעברית.
                """
                
                exam_img = Image.open(exam_img_file)
                content_to_send.append(exam_img)
                content_to_send.append(final_prompt)
                
                response = model.generate_content(content_to_send)
                
                st.success("הניתוח הושלם!")
                st.markdown("### 📊 תוצאות הבדיקה:")
                st.write(response.text)
                
            except Exception as e:
                st.error(f"שגיאה: {e}")
    else:
        st.warning("אנא העלה לפחות את תמונת המבחן ומלא את המחוון.")
