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
import io

# --- 1. הגדרות API וסיסמאות ---
genai.configure(api_key="AIzaSyDJdiYe4VmudGKFQzoCI_MmngD26D4wm1Q")

ALLOWED_PASSWORDS = [
    "dvir2012", "Teacher2012", "Sunset2012", "מורה2012", "Dvir_2012!",
    "2012EduCheck", "D2012V", "D@2012", "Dvir2012Pro", "Gold2012"
]

# --- 2. מודל FCN מהגיטהאב (לוגיקה מוטמעת) ---
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

def prepare_image(img_pil):
    img = np.array(img_pil.convert('RGB'))
    img = cv2.resize(img, (512, 512))
    img = img.astype(np.float32) / 255.0
    img = np.transpose(img, (2, 0, 1))
    return torch.from_numpy(img).unsqueeze(0)

# --- 3. טעינת משאבים ---
@st.cache_resource
def load_hw_model():
    model = FCN32s(n_class=2)
    model.eval()
    return model

hw_model = load_hw_model()

# --- 4. עיצוב הממשק (UI) ---
st.set_page_config(page_title="EduCheck AI Pro", layout="wide")
st.markdown("""
<style>
    .stApp { background: #0f172a; color: white; direction: rtl; text-align: right; }
    .glass-card { 
        background: rgba(30, 41, 59, 0.7); 
        border: 1px solid #38bdf8; 
        border-radius: 20px; 
        padding: 25px; 
        margin-bottom: 20px;
    }
    .main-title { 
        font-size: 3rem; 
        font-weight: 800; 
        background: linear-gradient(90deg, #38bdf8, #818cf8);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
    }
    .stButton>button { 
        background: linear-gradient(135deg, #38bdf8 0%, #1d4ed8 100%); 
        color: white !important; border-radius: 12px; font-weight: 700; width: 100%;
    }
</style>
""", unsafe_allow_html=True)

# ניהול Session State
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'reports' not in st.session_state: st.session_state.reports = []
if 'rubric' not in st.session_state: st.session_state.rubric = "בדוק לפי דיוק בתוכן, הבנה וניסוח."

# --- 5. מסך כניסה ---
if not st.session_state.logged_in:
    st.markdown("<div style='height: 15vh;'></div>", unsafe_allow_html=True)
    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        st.markdown("<div class='glass-card' style='text-align: center;'>", unsafe_allow_html=True)
        st.markdown("<h2 style='color: white;'>כניסת מורה מורשה</h2>", unsafe_allow_html=True)
        pwd = st.text_input("קוד גישה:", type="password")
        if st.button("התחבר"):
            if pwd in ALLOWED_PASSWORDS:
                st.session_state.logged_in = True
                st.rerun()
            else: st.error("קוד גישה לא מורשה")
        st.markdown("</div>", unsafe_allow_html=True)

# --- 6. המערכת המרכזית ---
else:
    st.markdown("<h1 class='main-title'>EduCheck AI Pro 🎓</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center;'>פיתוח: דביר ויגל טולדנו</p>", unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["🔍 בדיקת מבחן", "📊 ארכיון ודוחות", "⚙️ הגדרות מחוון"])

    # טאב הגדרות מחוון
    with tab3:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.subheader("עריכת מחוון (Rubric)")
        subj_opt = st.selectbox("מקצוע:", ["תורה", "גמרא", "מדעים", "עברית", "אחר"])
        if st.button("ייצר מחוון בסיסי עם AI"):
            model = genai.GenerativeModel('gemini-1.5-flash')
            res = model.generate_content(f"צור מחוון לבדיקת מבחן ב{subj_opt}")
            st.session_state.rubric = res.text
        st.session_state.rubric = st.text_area("טקסט המחוון הסופי:", value=st.session_state.rubric, height=200)
        st.markdown("</div>", unsafe_allow_html=True)

    # טאב בדיקה
    with tab1:
        col_r, col_l = st.columns([1, 1])
        with col_r:
            st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
            s_name = st.text_input("שם התלמיד:")
            up_file = st.file_uploader("העלה מבחן:", type=['jpg', 'png', 'jpeg'])
            cam_file = st.camera_input("או צלם")
            st.markdown("</div>", unsafe_allow_html=True)

        with col_l:
            st.subheader("ניתוח פדגוגי")
            active = cam_file if cam_file else up_file
            if st.button("🚀 הרץ בדיקה חכמה"):
                if active and s_name:
                    with st.spinner("מנתח כתב יד עברי..."):
                        img_pil = Image.open(active)
                        # שלב 1: FCN מהגיטהאב
                        _ = hw_model(prepare_image(img_pil))
                        
                        # שלב 2: Gemini
                        model = genai.GenerativeModel('gemini-1.5-flash')
                        prompt = f"נתח מבחן ב{subj_opt} עבור {s_name}. מחוון: {st.session_state.rubric}. פענח כתב יד עברי ותן ציון מספרי מודגש."
                        res = model.generate_content([prompt, img_pil])
                        
                        st.session_state.reports.append({
                            "שם": s_name, "מקצוע": subj_opt, "דוח": res.text, "תאריך": datetime.now().strftime("%d/%m/%Y")
                        })
                        st.markdown(f"<div class='glass-card'>{res.text}</div>", unsafe_allow_html=True)
                else: st.warning("מלא פרטים והעלה תמונה")

    # טאב ארכיון
    with tab2:
        if st.session_state.reports:
            df = pd.DataFrame(st.session_state.reports)
            csv = df.to_csv(index=False).encode('utf-8-sig')
            st.download_button("📥 הורד את כל הציונים לאקסל", csv, "grades.csv", "text/csv")
            
            for r in reversed(st.session_state.reports):
                with st.expander(f"{r['שם']} - {r['מקצוע']} ({r['תאריך']})"):
                    st.write(r['דוח'])
        else:
            st.info("הארכיון ריק")

    if st.sidebar.button("התנתק 🚪"):
        st.session_state.logged_in = False
        st.rerun()
