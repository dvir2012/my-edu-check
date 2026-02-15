import streamlit as st
import google.generativeai as genai
from PIL import Image
import pandas as pd
from datetime import datetime
import torch
import torch.nn as nn
from torchvision import models
import numpy as np
import cv2

# --- 1. הגדרות API וסיסמאות ---
genai.configure(api_key="AIzaSyDJdiYe4VmudGKFQzoCI_MmngD26D4wm1Q")

ALLOWED_PASSWORDS = ["dvir2012", "Teacher2012", "Sunset2012", "מורה2012", "Dvir_2012!"]

# רשימה ענקית של מקצועות
SUBJECTS = [
    "תורה", "גמרא", "דינים", "היסטוריה", "מדעים", "עברית", "מתמטיקה", 
    "אנגלית", "גאוגרפיה", "ספרות", "אזרחות", "של''ח", "תנ''ך", "משנה",
    "הבעה", "ערבית", "פיזיקה", "כימיה", "ביולוגיה", "מחשבת ישראל", "אחר"
]

# --- 2. מודל FCN ---
class FCN32s(nn.Module):
    def __init__(self, n_class=2):
        super(FCN32s, self).__init__()
        vgg = models.vgg16(weights=None)
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
def load_hw_model():
    model = FCN32s(n_class=2)
    model.eval()
    return model

hw_model = load_hw_model()

# --- 3. עיצוב הממשק ---
st.set_page_config(page_title="EduCheck AI Pro", layout="wide")
st.markdown("""
<style>
    .stApp { background: #0f172a; color: white; direction: rtl; text-align: right; }
    .glass-card { 
        background: rgba(30, 41, 59, 0.7); 
        border: 1px solid #38bdf8; 
        border-radius: 15px; 
        padding: 20px; 
        margin-bottom: 15px;
        min-height: 85vh;
    }
    .main-title { 
        font-size: 2rem; font-weight: 800; text-align: center;
        background: linear-gradient(90deg, #38bdf8, #818cf8);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        margin-bottom: 20px;
    }
    .stButton>button { 
        background: linear-gradient(135deg, #38bdf8 0%, #1d4ed8 100%); 
        color: white !important; border-radius: 10px; font-weight: 700;
    }
    .result-area { background: #1e293b; border-right: 4px solid #38bdf8; padding: 15px; border-radius: 8px; font-size: 0.9rem; }
</style>
""", unsafe_allow_html=True)

if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'reports' not in st.session_state: st.session_state.reports = []
if 'rubric' not in st.session_state: st.session_state.rubric = ""
if 'current_analysis' not in st.session_state: st.session_state.current_analysis = ""

# --- 4. מסך כניסה ---
if not st.session_state.logged_in:
    _, col, _ = st.columns([1, 1, 1])
    with col:
        st.markdown("<div class='glass-card' style='text-align: center; min-height: auto;'>", unsafe_allow_html=True)
        pwd = st.text_input("קוד גישה:", type="password")
        if st.button("התחבר"):
            if pwd in ALLOWED_PASSWORDS:
                st.session_state.logged_in = True
                st.rerun()
            else: st.error("קוד שגוי")
        st.markdown("</div>", unsafe_allow_html=True)

# --- 5. המערכת המרכזית (3 עמודות נפרדות) ---
else:
    st.markdown("<h1 class='main-title'>EduCheck AI Pro 🎓</h1>", unsafe_allow_html=True)
    
    col_work, col_res, col_arch = st.columns([1.1, 1.1, 0.8])

    # עמודה 1: הכל ביחד - מחוון ובדיקה
    with col_work:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        subject_active = st.selectbox("בחר מקצוע:", SUBJECTS)
        s_name = st.text_input("שם התלמיד:")
        
        st.write("**מחוון תשובות:**")
        if st.button("✨ צור מחוון אוטומטי"):
            model = genai.GenerativeModel('gemini-1.5-flash')
            res = model.generate_content(f"צור מחוון תשובות למבחן ב{subject_active}.")
            st.session_state.rubric = res.text
        st.session_state.rubric = st.text_area("ערוך מחוון:", value=st.session_state.rubric, height=150)
        
        st.write("**בדיקת מבחן:**")
        up_file = st.file_uploader("העלה צילום:", type=['jpg', 'png', 'jpeg'])
        
        if st.button("🚀 הרץ בדיקה"):
            if up_file and s_name and st.session_state.rubric:
                with st.spinner("מנתח..."):
                    img_pil = Image.open(up_file)
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    prompt = f"נתח מבחן ב{subject_active} של {s_name} לפי המחוון: {st.session_state.rubric}. תן ציון ומשוב."
                    res = model.generate_content([prompt, img_pil])
                    st.session_state.current_analysis = res.text
                    st.session_state.reports.append({
                        "שם": s_name, "שיעור": subject_active, "דוח": res.text, "זמן": datetime.now().strftime("%H:%M")
                    })
            else: st.warning("מלא את כל השדות")
        st.markdown("</div>", unsafe_allow_html=True)

    # עמודה 2: תוצאה בלבד
    with col_res:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.subheader("📄 משוב פדגוגי")
        if st.session_state.current_analysis:
            st.markdown(f"<div class='result-area'>{st.session_state.current_analysis}</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # עמודה 3: ארכיון נפרד
    with col_arch:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        filter_sub = st.selectbox("סינון ארכיון לפי מקצוע:", ["הכל"] + SUBJECTS)
        st.write("---")
        
        display_data = st.session_state.reports if filter_sub == "הכל" else [r for r in st.session_state.reports if r['שיעור'] == filter_sub]
        
        for r in reversed(display_data):
            with st.expander(f"{r['שם']} ({r['זמן']})"):
                st.markdown(r['דוח'])
        st.markdown("</div>", unsafe_allow_html=True)
