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

# רשימת מקצועות מורחבת
SUBJECTS = [
    "תורה", "גמרא", "היסטוריה", "מדעים", "עברית", "מתמטיקה", 
    "אנגלית", "גאוגרפיה", "ספרות", "אזרחות", "של"ח", "אחר"
]

# --- 2. מודל FCN (זיהוי כתב יד) ---
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
        font-size: 2.2rem; font-weight: 800; text-align: center;
        background: linear-gradient(90deg, #38bdf8, #818cf8);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        margin-bottom: 20px;
    }
    .stButton>button { 
        background: linear-gradient(135deg, #38bdf8 0%, #1d4ed8 100%); 
        color: white !important; border-radius: 10px; font-weight: 700; width: 100%;
    }
    .result-area { background: #1e293b; border-right: 4px solid #38bdf8; padding: 15px; border-radius: 8px; font-size: 0.9rem; white-space: pre-wrap; }
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
        st.header("EduCheck - כניסה")
        pwd = st.text_input("קוד גישה:", type="password")
        if st.button("התחבר"):
            if pwd in ALLOWED_PASSWORDS:
                st.session_state.logged_in = True
                st.rerun()
            else: st.error("קוד שגוי")
        st.markdown("</div>", unsafe_allow_html=True)

# --- 5. המערכת המרכזית (3 עמודות) ---
else:
    st.markdown("<h1 class='main-title'>EduCheck AI Pro 🎓</h1>", unsafe_allow_html=True)
    
    col_input, col_output, col_archive = st.columns([1, 1.2, 0.8])

    # --- עמודה 1: עבודה והזנה ---
    with col_input:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.subheader("🛠️ אזור עבודה")
        
        subject_active = st.selectbox("בחר מקצוע/שיעור:", SUBJECTS)
        s_name = st.text_input("שם התלמיד:")

        st.write("**ניהול מחוון:**")
        if st.button("✨ צור מחוון אוטומטי (Gemini)"):
            with st.spinner("מייצר מחוון תשובות..."):
                model = genai.GenerativeModel('gemini-1.5-flash')
                res = model.generate_content(f"צור מחוון תשובות מפורט למבחן ב{subject_active}. כלול נקודות ציון ותשובות נכונות.")
                st.session_state.rubric = res.text
        
        st.session_state.rubric = st.text_area("עריכת מחוון:", value=st.session_state.rubric, height=150)

        up_file = st.file_uploader("העלה צילום מבחן:", type=['jpg', 'png', 'jpeg'])
        
        if st.button("🚀 הרץ בדיקה פדגוגית"):
            if up_file and s_name and st.session_state.rubric:
                with st.spinner("מנתח כתב יד ומשווה למחוון..."):
                    img_pil = Image.open(up_file)
                    # ניתוח FCN (תשתית)
                    _ = hw_model(prepare_image(img_pil))
                    
                    # ניתוח תוכן Gemini
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    prompt = f"""
                    אתה מורה מקצועי ל{subject_active}. נתח את המבחן של {s_name}.
                    מחוון תשובות: {st.session_state.rubric}
                    
                    משימה:
                    1. פענח כתב יד.
                    2. השווה למחוון.
                    3. תן ציון מודגש (X/100).
                    4. תן משוב בונה בעברית.
                    """
                    res = model.generate_content([prompt, img_pil])
                    
                    st.session_state.current_analysis = res.text
                    st.session_state.reports.append({
                        "שם": s_name, "שיעור": subject_active, "דוח": res.text, "זמן": datetime.now().strftime("%d/%m %H:%M")
                    })
            else: st.error("אנא מלא את כל הפרטים (שם, מחוון ותמונה)")
        st.markdown("</div>", unsafe_allow_html=True)

    # --- עמודה 2: תוצאה בזמן אמת ---
    with col_output:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.subheader("📄 משוב נוכחי")
        if st.session_state.current_analysis:
            st.markdown(f"<div class='result-area'>{st.session_state.current_analysis}</div>", unsafe_allow_html=True)
        else:
            st.info("כאן יופיע הניתוח לאחר הלחיצה על 'הרץ בדיקה'.")
        st.markdown("</div>", unsafe_allow_html=True)

    # --- עמודה 3: ארכיון מסונן ---
    with col_archive:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.subheader("📂 היסטוריה וציונים")
        
        filter_sub = st.selectbox("סנן ארכיון לפי:", ["הכל"] + SUBJECTS)
        
        if filter_sub == "הכל":
            display_data = st.session_state.reports
        else:
            display_data = [r for r in st.session_state.reports if r['שיעור'] == filter_sub]
        
        if display_data:
            for r in reversed(display_data):
                with st.expander(f"{r['שם']} - {r['זמן']}"):
                    st.caption(f"שיעור: {r['שיעור']}")
                    st.markdown(r['דוח'])
        else:
            st.write("אין נתונים שמורים.")
        st.markdown("</div>", unsafe_allow_html=True)

    if st.sidebar.button("התנתק 🚪"):
        st.session_state.logged_in = False
        st.rerun()
