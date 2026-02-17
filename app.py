import streamlit as st
import google.generativeai as genai
from PIL import Image
import torch
import torch.nn as nn
from torchvision import models
import cv2
import numpy as np
import io
import pandas as pd
from datetime import datetime
import os

# ==========================================
# 1. הגדרות מיתוג ושם האפליקציה
# ==========================================
st.set_page_config(
    page_title="EduCheck AI", 
    page_icon="🎓", 
    layout="wide"
)

# ==========================================
# 2. חיבור ל-AI של גוגל (Gemini)
# ==========================================
def init_gemini():
    if "GEMINI_API_KEY" not in st.secrets:
        st.error("🔑 מפתח API חסר! נא להגדיר GEMINI_API_KEY ב-Secrets.")
        return None
    try:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        return "gemini-1.5-flash"
    except Exception as e:
        st.error(f"שגיאה בחיבור ל-AI: {e}")
        return None

MODEL_NAME = init_gemini()

# ==========================================
# 3. מודל ה-PyTorch (FCN32s)
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
# 4. עיצוב הממשק (CSS)
# ==========================================
st.markdown("""
<style>
    .stApp { background-color: #0f172a; color: white; direction: rtl; text-align: right; }
    .white-bold { color: #ffffff !important; font-weight: 900 !important; text-shadow: 2px 2px 4px #000000; }
    .glass-card { background: rgba(30, 41, 59, 0.7); border: 1px solid #38bdf8; border-radius: 15px; padding: 25px; margin-bottom: 20px; }
    .stButton>button { background: linear-gradient(135deg, #38bdf8 0%, #1d4ed8 100%); color: white !important; font-weight: 700; border-radius: 10px; border: none; width: 100%; }
    .logout-btn>button { background: linear-gradient(135deg, #ef4444 0%, #991b1b 100%) !important; }
    label, p { color: white !important; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

# ניהול נתונים בזיכרון
if 'db' not in st.session_state:
    st.session_state.db = []
if 'rubric' not in st.session_state:
    st.session_state.rubric = ""

# --- כותרת ראשית ---
st.markdown("<h1 class='white-bold' style='text-align: center;'>EduCheck AI 🎓</h1>", unsafe_allow_html=True)

# --- תפריט ראשי עם עמודת הגדרות חדשה ---
tab1, tab2, tab3 = st.tabs(["📄 בדיקה ומחוון", "📊 ארכיון תלמידים", "⚙️ הגדרות"])

# כרטיסייה 1: בדיקת מבחן
with tab1:
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        student_name = st.text_input("שם התלמיד:")
        subject = st.text_input("מקצוע:", "תורה")
        if st.button("✨ צור מחוון אוטומטי"):
            if MODEL_NAME:
                model = genai.GenerativeModel(MODEL_NAME)
                res = model.generate_content(f"צור מחוון תשובות למבחן ב{subject}")
                st.session_state.rubric = res.text
        st.session_state.rubric = st.text_area("מחוון הבדיקה:", value=st.session_state.rubric, height=200)
    with col2:
        uploaded_file = st.file_uploader("העלה צילום מבחן:", type=['jpg', 'jpeg', 'png'])
        if st.button("🚀 בדוק מבחן") and uploaded_file and student_name:
            with st.spinner("מנתח..."):
                img = Image.open(uploaded_file)
                model = genai.GenerativeModel(MODEL_NAME)
                prompt = f"פענח את המבחן של {student_name} ב{subject} לפי מחוון: {st.session_state.rubric}. תן ציון."
                response = model.generate_content([prompt, img])
                st.session_state.db.append({
                    "תאריך": datetime.now().strftime("%d/%m/%Y %H:%M"),
                    "תלמיד": student_name,
                    "מקצוע": subject,
                    "תוצאה": response.text
                })
                st.success("הבדיקה הושלמה!")
                st.write(response.text)
    st.markdown("</div>", unsafe_allow_html=True)

# כרטיסייה 2: ארכיון
with tab2:
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    if st.session_state.db:
        df = pd.DataFrame(st.session_state.db)
        st.dataframe(df, use_container_width=True)
        csv = df.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 הורד לאקסל", data=csv, file_name="educheck_results.csv")
    else:
        st.info("הארכיון ריק.")
    st.markdown("</div>", unsafe_allow_html=True)

# כרטיסייה 3: הגדרות והתנתקות
with tab3:
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    st.subheader("ניהול חשבון")
    st.write("מחובר כעת למערכת EduCheck AI")
    
    st.markdown("<div class='logout-btn'>", unsafe_allow_html=True)
    if st.button("🔴 התנתק מהמערכת ומחק נתונים זמניים"):
        # איפוס כל הנתונים בזיכרון
        st.session_state.db = []
        st.session_state.rubric = ""
        st.success("התנתקת בהצלחה. כל הנתונים הזמניים נמחקו.")
        st.rerun() # מרענן את האפליקציה למצב התחלתי
    st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("---")
    st.write("**גרסת אפליקציה:** 2.0.0 Pro")
    st.markdown("</div>", unsafe_allow_html=True)
