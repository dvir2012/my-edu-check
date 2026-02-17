import streamlit as st
import google.generativeai as genai
from PIL import Image
import torch
import torch.nn as nn
from torchvision import models
import cv2
import numpy as np
import pandas as pd
from datetime import datetime
import sqlite3
import easyocr
import io
import os

# ==========================================
# 1. הגדרות בסיס נתונים (שמירה קבועה)
# ==========================================
def init_db():
    conn = sqlite3.connect('results.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS exams 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  date TEXT, student_name TEXT, subject TEXT, result TEXT)''')
    conn.commit()
    conn.close()

def save_to_db(name, subject, result):
    conn = sqlite3.connect('results.db')
    c = conn.cursor()
    date_now = datetime.now().strftime("%d/%m/%Y %H:%M")
    c.execute("INSERT INTO exams (date, student_name, subject, result) VALUES (?, ?, ?, ?)",
              (date_now, name, subject, result))
    conn.commit()
    conn.close()

def load_from_db():
    conn = sqlite3.connect('results.db')
    df = pd.read_sql_query("SELECT date, student_name, subject, result FROM exams", conn)
    conn.close()
    return df

init_db()

# ==========================================
# 2. זיהוי כתב יד (EasyOCR)
# ==========================================
@st.cache_resource
def load_ocr():
    # טעינת המודל לעברית ואנגלית
    return easyocr.Reader(['he', 'en'])

reader = load_ocr()

def perform_ocr(image):
    img_array = np.array(image)
    # זיהוי טקסט בפורמט פשוט
    results = reader.readtext(img_array, detail=0)
    return " ".join(results)

# ==========================================
# 3. מודל ה-PyTorch (FCN32s) המקורי
# ==========================================
class FCN32s(nn.Module):
    def __init__(self, n_class=21):
        super(FCN32s, self).__init__()
        vgg = models.vgg16(weights='DEFAULT')
        self.features = vgg.features
        self.classifier = nn.Sequential(
            nn.Conv2d(512, 4096, 7),
            nn.ReLU(inplace=True),
            nn.Dropout2d(),
            nn.Conv2d(4096, 4096, 1),
            nn.ReLU(inplace=True),
            nn.Dropout2d(),
            nn.Conv2d(4096, n_class, 1),
        )
        self.upscore = nn.ConvTranspose2d(n_class, n_class, 64, stride=32, bias=False)

    def forward(self, x):
        x = self.features(x)
        x = self.classifier(x)
        x = self.upscore(x)
        return x

@st.cache_resource
def load_pytorch_model():
    model = FCN32s(n_class=2) 
    model.eval()
    return model

pytorch_model = load_pytorch_model()

# ==========================================
# 4. עיצוב וחיבור AI
# ==========================================
st.set_page_config(page_title="EduCheck AI Pro", page_icon="🎓", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #0f172a; color: white; direction: rtl; text-align: right; }
    .white-bold { color: #ffffff !important; font-weight: 900 !important; text-shadow: 2px 2px 4px #000000; }
    .glass-card { background: rgba(30, 41, 59, 0.7); border: 1px solid #38bdf8; border-radius: 15px; padding: 25px; margin-bottom: 20px; }
    .stButton>button { background: linear-gradient(135deg, #38bdf8 0%, #1d4ed8 100%); color: white !important; font-weight: 700; border-radius: 10px; border: none; width: 100%; }
    label, p, .stMarkdown { color: white !important; font-weight: 600; }
    .stTabs [data-baseweb="tab"] { color: white !important; }
</style>
""", unsafe_allow_html=True)

def init_gemini():
    if "GEMINI_API_KEY" not in st.secrets:
        st.error("🔑 מפתח API חסר ב-Secrets!")
        return None
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    return genai.GenerativeModel('gemini-1.5-flash')

# ==========================================
# 5. ממשק המשתמש (Tabs)
# ==========================================
st.markdown("<h1 class='white-bold' style='text-align: center;'>EduCheck AI Pro 🎓</h1>", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["📄 בדיקת מבחן", "📊 ארכיון (SQLite)", "⚙️ הגדרות"])

with tab1:
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    
    with col1:
        student_name = st.text_input("שם התלמיד:")
        subject = st.text_input("מקצוע:", "תורה")
        if st.button("✨ צור מחוון אוטומטי"):
            model_ai = init_gemini()
            if model_ai:
                with st.spinner("יוצר מחוון..."):
                    res = model_ai.generate_content(f"צור מחוון תשובות למבחן ב{subject}")
                    st.session_state.rubric = res.text
        if 'rubric' not in st.session_state: st.session_state.rubric = ""
        st.session_state.rubric = st.text_area("מחוון הבדיקה:", value=st.session_state.rubric, height=200)
    
    with col2:
        file = st.file_uploader("העלה צילום מבחן:", type=['jpg', 'jpeg', 'png'])
        if st.button("🚀 בדוק מבחן") and file and student_name and st.session_state.rubric:
            with st.spinner("מזהה כתב יד ומנתח..."):
                try:
                    img = Image.open(file)
                    # שלב 1: EasyOCR לחילוץ טקסט
                    detected_text = perform_ocr(img)
                    
                    # שלב 2: Gemini לניתוח התמונה + הטקסט שזוהה
                    model_ai = init_gemini()
                    prompt = f"""
                    תסתכל על התמונה + על הטקסט שזיהיתי ב-OCR: "{detected_text}"
                    השתמש במחוון הבא כבסיס לבדיקה: {st.session_state.rubric}
                    תן ציון מ-1 עד 100 עבור התלמיד {student_name}.
                    תכתוב בעברית בצורה מסודרת בדיוק כך:
                    ציון: [כאן הציון]
                    מה היה טוב: [פירוט]
                    מה היה לא טוב: [פירוט]
                    הסבר לכל שאלה: [השוואה בין תשובת התלמיד למחוון]
                    """
                    response = model_ai.generate_content([prompt, img])
                    
                    # שלב 3: שמירה לבסיס הנתונים (SQLite)
                    save_to_db(student_name, subject, response.text)
                    
                    st.success("הבדיקה הושלמה ונשמרה!")
                    st.write(response.text)
                except Exception as e:
                    st.error(f"שגיאה: {e}")
    st.markdown("</div>", unsafe_allow_html=True)

with tab2:
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    db_data = load_from_db()
    if not db_data.empty:
        st.dataframe(db_data, use_container_width=True)
        st.download_button("📥 הורד אקסל מלא", data=db_data.to_csv(index=False).encode('utf-8-sig'), file_name="exams_archive.csv")
    else:
        st.info("אין נתונים שמורים בארכיון.")
    st.markdown("</div>", unsafe_allow_html=True)

with tab3:
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    if st.button("🔴 מחיקת כל הארכיון"):
        conn = sqlite3.connect('results.db')
        conn.execute("DELETE FROM exams")
        conn.commit()
        conn.close()
        st.warning("הארכיון נמחק!")
        st.rerun()
    st.markdown("---")
    st.write("**מצב מערכת:** פעיל (OCR + SQLite + PyTorch)")
    st.markdown("</div>", unsafe_allow_html=True)
