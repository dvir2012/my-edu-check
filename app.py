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
# 1. הגדרות דף ומיתוג
# ==========================================
st.set_page_config(page_title="EduCheck AI", page_icon="🎓", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #0f172a; color: white; direction: rtl; text-align: right; }
    .white-bold { color: #ffffff !important; font-weight: 900 !important; text-shadow: 2px 2px 4px #000000; }
    .glass-card { background: rgba(30, 41, 59, 0.7); border: 1px solid #38bdf8; border-radius: 15px; padding: 25px; margin-bottom: 20px; }
    .stButton>button { background: linear-gradient(135deg, #38bdf8 0%, #1d4ed8 100%); color: white !important; font-weight: 700; border-radius: 10px; border: none; width: 100%; }
    label, p, .stMarkdown { color: white !important; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. חיבור ל-AI (תיקון ה-404)
# ==========================================
def init_gemini():
    if "GEMINI_API_KEY" not in st.secrets:
        st.error("🔑 מפתח API חסר ב-Secrets!")
        return None
    try:
        # פתרון קריטי: הגדרת המפתח
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        # יצירת אובייקט המודל עם הגדרה מפורשת
        return genai.GenerativeModel('gemini-1.5-flash')
    except Exception as e:
        st.error(f"שגיאה בחיבור: {e}")
        return None

# ==========================================
# 3. מודל ה-PyTorch (FCN32s)
# ==========================================
class FCN32s(nn.Module):
    def __init__(self, n_class=21):
        super(FCN32s, self).__init__()
        vgg = models.vgg16(weights='DEFAULT')
        self.features = vgg.features
        self.classifier = nn.Sequential(
            nn.Conv2d(512, 4096, 7), nn.ReLU(inplace=True), nn.Dropout2d(),
            nn.Conv2d(4096, 4096, 1), nn.ReLU(inplace=True), nn.Dropout2d(),
            nn.Conv2d(4096, n_class, 1),
        )
        self.upscore = nn.ConvTranspose2d(n_class, n_class, 64, stride=32, bias=False)
    def forward(self, x):
        x = self.features(x); x = self.classifier(x); x = self.upscore(x)
        return x

@st.cache_resource
def load_pytorch_model():
    model = FCN32s(n_class=2); model.eval()
    return model

pytorch_model = load_pytorch_model()

# ניהול נתונים
if 'db' not in st.session_state: st.session_state.db = []
if 'rubric' not in st.session_state: st.session_state.rubric = ""

st.markdown("<h1 class='white-bold' style='text-align: center;'>EduCheck AI 🎓</h1>", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["📄 בדיקה ומחוון", "📊 ארכיון תלמידים", "⚙️ הגדרות"])

with tab1:
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        student_name = st.text_input("שם התלמיד:")
        subject = st.text_input("מקצוע:", "תורה")
        if st.button("✨ צור מחוון אוטומטי"):
            model = init_gemini()
            if model:
                res = model.generate_content(f"צור מחוון תשובות למבחן ב{subject}")
                st.session_state.rubric = res.text
        st.session_state.rubric = st.text_area("מחוון הבדיקה:", value=st.session_state.rubric, height=200)
    with col2:
        uploaded_file = st.file_uploader("העלה צילום מבחן:", type=['jpg', 'jpeg', 'png'])
        if st.button("🚀 בדוק מבחן") and uploaded_file and student_name:
            with st.spinner("מנתח..."):
                try:
                    img = Image.open(uploaded_file)
                    model = init_gemini()
                    if model:
                        prompt = f"פענח את המבחן של {student_name} לפי מחוון: {st.session_state.rubric}. תן ציון והסבר בעברית."
                        response = model.generate_content([prompt, img])
                        st.session_state.db.append({
                            "תאריך": datetime.now().strftime("%d/%m/%Y %H:%M"),
                            "תלמיד": student_name, "מקצוע": subject, "תוצאה": response.text
                        })
                        st.success("הבדיקה הושלמה!")
                        st.write(response.text)
                except Exception as e:
                    st.error(f"שגיאה: {e}")
    st.markdown("</div>", unsafe_allow_html=True)

with tab2:
    if st.session_state.db:
        df = pd.DataFrame(st.session_state.db)
        st.dataframe(df, use_container_width=True)
        st.download_button("📥 הורד לאקסל", data=df.to_csv(index=False).encode('utf-8-sig'), file_name="results.csv")
    else: st.info("הארכיון ריק.")

with tab3:
    if st.button("🔴 איפוס נתונים"):
        st.session_state.db = []; st.rerun()
