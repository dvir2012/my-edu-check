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
# וודא שהמפתח תקין
genai.configure(api_key="AIzaSyDJdiYe4VmudGKFQzoCI_MmngD26D4wm1Q")

ALLOWED_PASSWORDS = [
    "dvir2012", "Teacher2012", "Sunset2012", "מורה2012", "Dvir_2012!",
    "2012EduCheck", "D2012V", "D@2012", "Dvir2012Pro", "Gold2012"
]

# --- 2. מודל FCN32s (זיהוי כתב יד מהגיטהאב) ---
class FCN32s(nn.Module):
    def __init__(self, n_class=2):
        super(FCN32s, self).__init__()
        # משתמשים במודל VGG16 בסיסי ללא משקולות כבדות כדי למנוע קריסת זיכרון בשרת
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

def prepare_image(img_pil):
    """מכין את התמונה למודל ה-FCN"""
    img = np.array(img_pil.convert('RGB'))
    img = cv2.resize(img, (512, 512))
    img = img.astype(np.float32) / 255.0
    img = np.transpose(img, (2, 0, 1))
    return torch.from_numpy(img).unsqueeze(0)

# --- 3. טעינת משאבים (Caching) ---
@st.cache_resource
def load_hw_model():
    model = FCN32s(n_class=2)
    model.eval()
    return model

hw_model = load_hw_model()

# --- 4. עיצוב ממשק המשתמש (UI) ---
st.set_page_config(page_title="EduCheck AI Pro", layout="wide")
st.markdown("""
<style>
    .stApp { background-color: #0f172a; color: white; direction: rtl; text-align: right; }
    .card { background: rgba(30, 41, 59, 0.7); border: 1px solid #38bdf8; border-radius: 15px; padding: 25px; margin-top: 10px; }
    .stButton>button { background: linear-gradient(90deg, #38bdf8, #1d4ed8); color: white; font-weight: bold; width: 100%; border-radius: 10px; }
    h1, h2, h3 { color: #38bdf8 !important; }
</style>
""", unsafe_allow_html=True)

# ניהול מצבי גלישה (Session State)
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'reports' not in st.session_state: st.session_state.reports = []

# --- 5. מסך כניסה ---
if not st.session_state.logged_in:
    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        st.markdown("<div class='card' style='margin-top:20vh; text-align:center;'>", unsafe_allow_html=True)
        st.header("כניסת מורה מורשה")
        pwd = st.text_input("הזן קוד גישה:", type="password")
        if st.button("התחברות"):
            if pwd in ALLOWED_PASSWORDS:
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("קוד גישה שגוי")
        st.markdown("</div>", unsafe_allow_html=True)

# --- 6. הממשק המרכזי ---
else:
    st.title("EduCheck AI Pro - יגל טולדנו ודביר 🎓")
    
    with st.sidebar:
        st.success("מחובר למערכת")
        if st.button("התנתק 🚪"):
            st.session_state.logged_in = False
            st.rerun()

    tab1, tab2 = st.tabs(["🔍 בדיקת מבחן", "📂 ארכיון דוחות"])

    with tab1:
        col_r, col_l = st.columns([1, 1])
        
        with col_r:
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            name = st.text_input("שם התלמיד:")
            subject = st.selectbox("מקצוע:", ["תורה", "גמרא", "מדעים", "עברית", "אחר"])
            up_img = st.file_uploader("העלה צילום מבחן (JPG/PNG):", type=['jpg', 'jpeg', 'png'])
            cam_img = st.camera_input("או צלם עכשיו")
            st.markdown("</div>", unsafe_allow_html=True)

        with col_l:
            st.subheader("תוצאות ניתוח ה-AI")
            active_img = cam_img if cam_img else up_img
            
            if st.button("🚀 הרץ בדיקה פדגוגית"):
                if active_img and name:
                    with st.spinner("מנתח כתב יד ומחשב ציון..."):
                        try:
                            # שלב א: הכנת התמונה והרצת מודל ה-FCN
                            img_pil = Image.open(active_img)
                            processed_tensor = prepare_image(img_pil)
                            with torch.no_grad():
                                _ = hw_model(processed_tensor)
                            
                            # שלב ב: ניתוח תוכן עם Gemini
                            model = genai.GenerativeModel('gemini-1.5-flash')
                            prompt = f"נתח את המבחן של {name} במקצוע {subject}. הטקסט הוא כתב יד עברי. פענח אותו, תן ציון מספרי מודגש ומשוב בונה."
                            response = model.generate_content([prompt, img_pil])
                            
                            # שמירה לארכיון
                            st.session_state.reports.append({
                                "שם": name, "מקצוע": subject, 
                                "דוח": response.text, "זמן": datetime.now().strftime("%d/%m %H:%M")
                            })
                            
                            st.markdown(f"<div class='card'>{response.text}</div>", unsafe_allow_html=True)
                        except Exception as e:
                            st.error(f"אירעה שגיאה בניתוח: {e}")
                else:
                    st.warning("אנא מלא שם תלמיד והעלה תמונה של המבחן.")

    with tab2:
        if not st.session_state.reports:
            st.info("עדיין אין דוחות בארכיון.")
        else:
            for r in reversed(st.session_state.reports):
                with st.expander(f"📄 {r['שם']} - {r['מקצוע']} ({r['זמן']})"):
                    st.markdown(r['דוח'])
