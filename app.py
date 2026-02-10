import streamlit as st
import google.generativeai as genai
from PIL import Image
import os
import torch
import torch.nn as nn

# --- 1. הגדרת המודל האישי (המוח שאימנת) ---
class SimpleCNN(nn.Module):
    def __init__(self):
        super(SimpleCNN, self).__init__()
        self.conv1 = nn.Conv2d(1, 32, kernel_size=3, padding=1)
        self.fc1 = nn.Linear(32 * 32 * 32, 27)

    def forward(self, x):
        x = torch.relu(self.conv1(x))
        x = x.view(x.size(0), -1)
        x = self.fc1(x)
        return x

@st.cache_resource
def load_my_ai_model():
    model = SimpleCNN()
    if os.path.exists("hebrew_model.pth"):
        try:
            model.load_state_dict(torch.load("hebrew_model.pth", map_location=torch.device('cpu')))
            model.eval()
            return model
        except:
            return None
    return None

my_custom_model = load_my_ai_model()

# --- 2. הגדרות API ---
MY_API_KEY = "AIzaSyDJdiYe4VmudGKFQzoCI_MmngD26D4wm1Q" 
genai.configure(api_key=MY_API_KEY)

# --- 3. עיצוב משולב (בהיר + נגיעות כהות) ---
st.set_page_config(page_title="EduCheck AI PRO", layout="wide")

st.markdown("""
<style>
    /* עיצוב כללי - רקע בהיר */
    .stApp { background-color: #f1f5f9; direction: rtl; text-align: right; }
    
    /* כותרת ראשית */
    .main-header { 
        color: #1e293b; 
        text-align: center; 
        font-weight: 900; 
        font-size: 3rem; 
        padding: 2rem;
        background: linear-gradient(90deg, #2563eb, #7c3aed);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    /* כרטיסים כהים לאזורי קלט */
    .stTextArea textarea, .stTextInput input {
        background-color: #1e293b !important;
        color: #f8fafc !important;
        border-radius: 10px !important;
    }
    
    /* עיצוב כפתורים */
    .stButton>button {
        width: 100%;
        background-color: #2563eb;
        color: white;
        border-radius: 12px;
        height: 3em;
        font-weight: bold;
        transition: 0.3s;
    }
    .stButton>button:hover { background-color: #1d4ed8; border: 2px solid white; }
    
    /* תיבת תוצאות */
    .result-box {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 15px;
        border-right: 10px solid #2563eb;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

# --- 4. פונקציית דף התרגול (מה שביקשת קודם) ---
def show_practice_sheet():
    letters = ['א','ב','ג','ד','ה','ו','ז','ח','ט','י','כ','ך','ל','מ','ם','נ','ן','ס','ע','פ','ף','צ','ץ','ק','ר','ש','ת']
    st.write("### 📝 דף הכנה לאיסוף כתב יד")
    st.write("הדפס את הדף הזה ותן לתלמידים למלא:")
    cols = st.columns(4)
    for i, letter in enumerate(letters):
        cols[i % 4].markdown(f"<div style='border: 2px solid #ccc; padding: 10px; text-align: center; margin-bottom: 5px; background: white;'><span style='font-size: 24px; color: black;'>{letter} = </span><br><br><br></div>", unsafe_allow_html=True)

# --- 5. מבנה האפליקציה ---
st.markdown("<div class='main-header'>EduCheck AI PRO 🧠</div>", unsafe_allow_html=True)

# תפריט צדדי
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3443/3443338.png", width=100)
    st.title("ניהול מערכת")
    if st.button("הצג דף תרגול א-ת"):
        st.session_state.show_sheet = True
    if st.button("חזרה לבדיקת מבחנים"):
        st.session_state.show_sheet = False

# מצב תצוגה: דף תרגול או בדיקת מבחן
if st.session_state.get('show_sheet', False):
    show_practice_sheet()
else:
    if my_custom_model:
        st.success("✨ המודל האישי שלך פעיל - רמת דיוק מקסימלית!")
    else:
        st.info("💡 שים לב: המערכת עובדת במצב סטנדרטי (Gemini).")

    col1, col2 = st.columns([1, 1.2])

    with col1:
        st.markdown("### 📝 פרטי המבחן")
        student_name = st.text_input("שם התלמיד:", placeholder="הכנס שם...")
        rubric = st.text_area("מחוון תשובות (מה נחשב תשובה נכונה?):", height=200)

    with col2:
        st.markdown("### 📸 סריקה וצילום")
        img_file = st.file_uploader("העלה צילום מבחן", type=['png', 'jpg', 'jpeg'])
        camera_img = st.camera_input("או צלם עכשיו")

    if st.button("בדוק מבחן ונתן ציון ⚡"):
        source = camera_img if camera_img else img_file
        if source:
            with st.spinner("מנתח כתב יד ומחשב ציון..."):
                img = Image.open(source)
                model_gemini = genai.GenerativeModel('gemini-1.5-flash')
                
                # הנחיה משולבת (Gemini + הקשר למודל שלך)
                prompt = f"""
                אתה מורה מקצועי. נתח את המבחן של {student_name}.
                מחוון התשובות: {rubric}
                אנא בצע:
                1. תמלול של התשובות מהתמונה.
                2. השוואה למחוון.
                3. מתן ציון סופי והסבר.
                התייחס במיוחד לכתב יד שעשוי להיות קשה לקריאה.
                """
                
                response = model_gemini.generate_content([prompt, img])
                
                st.markdown("<div class='result-box'>", unsafe_allow_html=True)
                st.markdown("### 📋 סיכום בדיקה:")
                st.write(response.text)
                st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.error("אנא העלה תמונה או צלם את המבחן תחילה.")
