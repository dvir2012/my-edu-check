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

ALLOWED_PASSWORDS = [
    "dvir2012", "Teacher2012", "Sunset2012", "מורה2012", "Dvir_2012!",
    "2012EduCheck", "D2012V", "D@2012", "Dvir2012Pro", "Gold2012"
]

# --- 2. מודל ה-FCN (הלוגיקה מהגיטהאב) ---
class FCN32s(nn.Module):
    def __init__(self, n_class=2):
        super(FCN32s, self).__init__()
        vgg = models.vgg16(weights=None) # לא מורידים משקולות כבדות כדי לא לתקוע את השרת
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

def prepare_image(img_pil):
    img = np.array(img_pil.convert('RGB'))
    img = cv2.resize(img, (512, 512))
    img = img.astype(np.float32) / 255.0
    img = np.transpose(img, (2, 0, 1))
    return torch.from_numpy(img).unsqueeze(0)

# --- 3. טעינת משאבים ---
@st.cache_resource
def load_models():
    model = FCN32s(n_class=2)
    model.eval()
    return model

hw_model = load_models()

# --- 4. עיצוב הממשק ---
st.set_page_config(page_title="EduCheck AI Pro", layout="wide")
st.markdown("""
<style>
    .stApp { background: #0f172a; color: white; direction: rtl; text-align: right; }
    .card { background: rgba(30, 41, 59, 0.7); border: 1px solid #38bdf8; border-radius: 15px; padding: 20px; }
    .stButton>button { background: linear-gradient(90deg, #38bdf8, #1d4ed8); color: white; font-weight: bold; width: 100%; }
</style>
""", unsafe_allow_html=True)

if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'reports' not in st.session_state: st.session_state.reports = []

# --- 5. מסך כניסה ---
if not st.session_state.logged_in:
    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        st.markdown("<div class='card' style='margin-top:20vh; text-align:center;'>", unsafe_allow_html=True)
        st.header("כניסת מורה מורשה")
        pwd = st.text_input("קוד גישה:", type="password")
        if st.button("התחבר"):
            if pwd in ALLOWED_PASSWORDS:
                st.session_state.logged_in = True
                st.rerun()
            else: st.error("גישה נדחתה")
        st.markdown("</div>", unsafe_allow_html=True)

# --- 6. המערכת המרכזית ---
else:
    st.title("EduCheck AI Pro 🎓")
    st.sidebar.info("המערכת מופעלת עכשיו במצב יציב (Lite Mode)")
    if st.sidebar.button("התנתק"):
        st.session_state.logged_in = False
        st.rerun()

    tab1, tab2 = st.tabs(["🔍 בדיקת מבחן", "📂 ארכיון"])

    with tab1:
        c1, c2 = st.columns([1, 1])
        with c1:
            name = st.text_input("שם התלמיד:")
            subject = st.selectbox("מקצוע:", ["תורה", "גמרא", "מדעים", "עברית"])
            up_img = st.file_uploader("העלה צילום מבחן:", type=['jpg', 'png'])
            cam_img = st.camera_input("צילום")
        
        with c2:
            active = cam_img if cam_img else up_img
            if st.button("🚀 הרץ בדיקה"):
                if active and name:
                    with st.spinner("מפענח ומנתח..."):
                        img_pil = Image.open(active)
                        # עיבוד FCN
                        _ = hw_model(prepare_image(img_pil))
                        
                        # ניתוח Gemini
                        model = genai.GenerativeModel('gemini-1.5-flash')
                        res = model.generate_content([f"נתח מבחן ב{subject} עבור {name}. פענח כתב יד עברי ותן ציון.", img_pil])
                        
                        st.session_state.reports.append({"שם": name, "דוח": res.text, "זמן": datetime.now().strftime("%H:%M")})
                        st.markdown(f"<div class='card'>{res.text}</div>", unsafe_allow_html=True)
                else: st.warning("מלא פרטים")

    with tab2:
        for r in reversed(st.session_state.reports):
            with st.expander(f"{r['שם']} | {r['זמן']}"):
                st.write(r['דוח'])
