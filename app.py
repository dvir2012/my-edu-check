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
    page_title="EduCheck AI", # השם שיופיע במחשב כשתתקין
    page_icon="🎓", 
    layout="wide"
)

# ==========================================
# 2. חיבור ל-AI של גוגל (Gemini)
# ==========================================
def init_gemini():
    if "GEMINI_API_KEY" not in st.secrets:
        st.error("🔑 מפתח API חסר! נא להגדיר GEMINI_API_KEY ב-Secrets של Streamlit.")
        return None
    try:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        return "gemini-1.5-flash"
    except Exception as e:
        st.error(f"שגיאה בחיבור ל-AI: {e}")
        return None

MODEL_NAME = init_gemini()

# ==========================================
# 3. מודל ה-PyTorch (FCN32s) - המבנה המלא
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
# 4. עיצוב הממשק (CSS) - לבן על כהה, מקצועי
# ==========================================
st.markdown("""
<style>
    .stApp { background-color: #0f172a; color: white; direction: rtl; text-align: right; }
    .white-bold { color: #ffffff !important; font-weight: 900 !important; text-shadow: 2px 2px 4px #000000; }
    .glass-card { background: rgba(30, 41, 59, 0.7); border: 1px solid #38bdf8; border-radius: 15px; padding: 25px; margin-bottom: 20px; }
    .stButton>button { background: linear-gradient(135deg, #38bdf8 0%, #1d4ed8 100%); color: white !important; font-weight: 700; border-radius: 10px; border: none; width: 100%; }
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
st.markdown("<p style='text-align: center;'>מערכת חכמה לבדיקת מבחנים וניהול ארכיון תלמידים</p>", unsafe_allow_html=True)

# --- תפריט ראשי ---
tab1, tab2 = st.tabs(["📄 בדיקת מבחן וניהול מחוון", "📊 ארכיון תלמידים (Pandas)"])

# כרטיסייה 1: בדיקת מבחן
with tab1:
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("<p class='white-bold'>פרטי המבחן והמחוון</p>", unsafe_allow_html=True)
        student_name = st.text_input("שם התלמיד:")
        subject = st.text_input("מקצוע:", "תורה")
        
        # יצירת מחוון עם Gemini
        if st.button("✨ צור מחוון תשובות אוטומטי (Gemini)"):
            if MODEL_NAME:
                model = genai.GenerativeModel(MODEL_NAME)
                res = model.generate_content(f"צור מחוון תשובות מפורט למבחן ב{subject}")
                st.session_state.rubric = res.text
            else:
                st.error("לא ניתן ליצור מחוון ללא מפתח API")
        
        st.session_state.rubric = st.text_area("מחוון הבדיקה (התשובות הנכונות):", value=st.session_state.rubric, height=200)
        
    with col2:
        st.markdown("<p class='white-bold'>העלאת המבחן לבדיקה</p>", unsafe_allow_html=True)
        uploaded_file = st.file_uploader("בחר צילום של המבחן:", type=['jpg', 'jpeg', 'png'])
        
        if st.button("🚀 בדוק מבחן עכשיו") and uploaded_file and student_name:
            with st.spinner("ה-AI מנתח את כתב היד מול המחוון..."):
                img = Image.open(uploaded_file)
                model = genai.GenerativeModel(MODEL_NAME)
                prompt = f"פענח את המבחן של {student_name} במקצוע {subject}. השווה למחוון הבא: {st.session_state.rubric}. תן ציון סופי ופרט טעויות."
                response = model.generate_content([prompt, img])
                
                # שמירה לארכיון (Pandas)
                res_data = {
                    "תאריך": datetime.now().strftime("%d/%m/%Y %H:%M"),
                    "תלמיד": student_name,
                    "מקצוע": subject,
                    "תוצאה": response.text
                }
                st.session_state.db.append(res_data)
                
                st.success("הבדיקה הושלמה!")
                st.markdown(f"<div style='background: #1e293b; padding: 20px; border-radius: 10px; border-right: 5px solid #38bdf8;'>{response.text}</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# כרטיסייה 2: ארכיון תלמידים
with tab2:
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    if st.session_state.db:
        df = pd.DataFrame(st.session_state.db)
        st.markdown("<p class='white-bold'>יומן מבחנים שנבדקו:</p>", unsafe_allow_html=True)
        st.dataframe(df, use_container_width=True)
        
        # כפתור הורדה לאקסל
        csv = df.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 הורד ארכיון לאקסל (CSV)", data=csv, file_name="educheck_results.csv", mime="text/csv")
    else:
        st.info("אין נתונים בארכיון עדיין. בצע בדיקה ראשונה כדי לראות תוצאות כאן.")
    st.markdown("</div>", unsafe_allow_html=True)
