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

# ==========================================
# 1. הגדרות API מתוך Secrets (אבטחה)
# ==========================================
MODEL_NAME = 'gemini-1.5-flash-latest' 

if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.warning("⚠️ מפתח API לא הוגדר. אנא הגדר אותו ב-Secrets תחת השם GEMINI_API_KEY")

ALLOWED_PASSWORDS = ["dvir2012", "Teacher2012", "Sunset2012", "מורה2012", "Dvir_2012!"]
SUBJECTS = ["תורה", "גמרא", "דינים", "היסטוריה", "מדעים", "עברית", "מתמטיקה", "אחר"]

# ==========================================
# 2. מודל ה-Deep Learning (FCN32s)
# ==========================================
class FCN32s(nn.Module):
    def __init__(self, n_class=2):
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

def optimize_image(upload_file):
    img = Image.open(upload_file)
    if img.mode in ("RGBA", "P"): img = img.convert("RGB")
    img.thumbnail((1800, 1800))
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='JPEG', quality=85)
    return Image.open(img_byte_arr)

# ==========================================
# 3. עיצוב ממשק (לבן מודגש)
# ==========================================
st.set_page_config(page_title="EduCheck AI - Secure Edition", layout="wide")
st.markdown("""
<style>
    .stApp { background-color: #0f172a; color: white; direction: rtl; text-align: right; }
    .white-bold { color: #ffffff !important; font-weight: 900 !important; text-shadow: 2px 2px 4px #000000; }
    label, .stMarkdown p { color: #ffffff !important; font-weight: 800 !important; }
    .result-box { background: #1e293b; border-right: 5px solid #38bdf8; padding: 20px; border-radius: 12px; }
</style>
""", unsafe_allow_html=True)

# אתחול
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'reports' not in st.session_state: st.session_state.reports = []

# --- מסך כניסה ---
if not st.session_state.logged_in:
    pwd = st.text_input("קוד גישה:", type="password")
    if st.button("התחבר"):
        if pwd in ALLOWED_PASSWORDS:
            st.session_state.logged_in = True
            st.rerun()
else:
    st.markdown("<h1 style='text-align:center;'>EduCheck AI 🎓 (גרסה מאובטחת)</h1>", unsafe_allow_html=True)
    
    t1, t2 = st.tabs(["📝 בדיקת מבחן", "📂 ארכיון (Pandas)"])

    with t1:
        st.markdown("<div class='result-box'>", unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("<p class='white-bold'>פרטי המבחן</p>", unsafe_allow_html=True)
            subject = st.selectbox("מקצוע:", SUBJECTS)
            s_name = st.text_input("שם תלמיד:")
            rubric = st.text_area("מחוון תשובות:")
        with c2:
            st.markdown("<p class='white-bold'>העלאת קובץ</p>", unsafe_allow_html=True)
            up_file = st.file_uploader("צילום המבחן:", type=['jpg', 'png', 'jpeg'])
            if st.button("🚀 בדוק עכשיו") and up_file:
                with st.spinner("מפענח עברית..."):
                    try:
                        img = optimize_image(up_file)
                        model = genai.GenerativeModel(MODEL_NAME)
                        res = model.generate_content([f"בדוק מבחן ב{subject} עבור {s_name}. מחוון: {rubric}", img])
                        st.session_state.last_res = res.text
                        st.session_state.reports.append({"תלמיד": s_name, "דוח": res.text, "זמן": datetime.now().strftime("%H:%M")})
                    except Exception as e: st.error(f"שגיאה: {e}")
            if 'last_res' in st.session_state:
                st.markdown(f"<div class='result-box'>{st.session_state.last_res}</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with t2:
        if st.session_state.reports:
            st.dataframe(pd.DataFrame(st.session_state.reports), use_container_width=True)
