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
        border-radius: 20px; 
        padding: 25px; 
        margin-bottom: 20px;
    }
    .main-title { 
        font-size: 2.5rem; font-weight: 800; text-align: center;
        background: linear-gradient(90deg, #38bdf8, #818cf8);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }
    .stButton>button { 
        background: linear-gradient(135deg, #38bdf8 0%, #1d4ed8 100%); 
        color: white !important; border-radius: 12px; font-weight: 700; width: 100%;
    }
    .result-area { background: #1e293b; border-right: 5px solid #38bdf8; padding: 20px; border-radius: 10px; min-height: 400px; }
</style>
""", unsafe_allow_html=True)

if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'reports' not in st.session_state: st.session_state.reports = []
if 'rubric' not in st.session_state: st.session_state.rubric = ""
if 'current_analysis' not in st.session_state: st.session_state.current_analysis = ""

# --- 4. מסך כניסה ---
if not st.session_state.logged_in:
    st.markdown("<div style='height: 15vh;'></div>", unsafe_allow_html=True)
    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        st.markdown("<div class='glass-card' style='text-align: center;'>", unsafe_allow_html=True)
        st.header("כניסת מורה מורשה")
        pwd = st.text_input("קוד גישה:", type="password")
        if st.button("התחבר"):
            if pwd in ALLOWED_PASSWORDS:
                st.session_state.logged_in = True
                st.rerun()
            else: st.error("קוד שגוי")
        st.markdown("</div>", unsafe_allow_html=True)

# --- 5. המערכת המרכזית ---
else:
    st.markdown("<h1 class='main-title'>EduCheck AI Pro - ניהול פדגוגי חכם 🎓</h1>", unsafe_allow_html=True)
    
    # עמודה ימנית: קלט | עמודה שמאלית: פלט
    col_input, col_output = st.columns([1, 1])

    with col_input:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.subheader("🛠️ אזור העבודה")
        
        # בחירת מקצוע ושם
        c1, c2 = st.columns(2)
        with c1:
            subject_active = st.selectbox("שיעור:", ["תורה", "גמרא", "מדעים", "עברית", "מתמטיקה", "אחר"])
        with c2:
            s_name = st.text_input("שם התלמיד:")

        # מחוון
        st.write("**מחוון תשובות:**")
        if st.button("✨ צור מחוון אוטומטי"):
            with st.spinner("יוצר..."):
                model = genai.GenerativeModel('gemini-1.5-flash')
                res = model.generate_content(f"צור מחוון תשובות למבחן ב{subject_active}.")
                st.session_state.rubric = res.text
        st.session_state.rubric = st.text_area("הגדרת תשובות נכונות:", value=st.session_state.rubric, height=150)

        # העלאה
        up_file = st.file_uploader("העלה/צלם מבחן:", type=['jpg', 'png', 'jpeg'])
        
        if st.button("🚀 הרץ בדיקה וניתוח"):
            if up_file and s_name and st.session_state.rubric:
                with st.spinner("ה-AI מנתח..."):
                    img_pil = Image.open(up_file)
                    # FCN
                    _ = hw_model(prepare_image(img_pil))
                    # Gemini
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    prompt = f"נתח מבחן ב{subject_active} של {s_name} לפי המחוון: {st.session_state.rubric}. תן ציון ומשוב."
                    res = model.generate_content([prompt, img_pil])
                    
                    st.session_state.current_analysis = res.text
                    st.session_state.reports.append({
                        "שם": s_name, "שיעור": subject_active, "דוח": res.text, "זמן": datetime.now().strftime("%d/%m %H:%M")
                    })
            else:
                st.error("וודא שמילאת שם, מחוון והעלית תמונה.")
        st.markdown("</div>", unsafe_allow_html=True)

    with col_output:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.subheader("📄 משוב פדגוגי לתלמיד")
        if st.session_state.current_analysis:
            st.markdown(f"<div class='result-area'>{st.session_state.current_analysis}</div>", unsafe_allow_html=True)
        else:
            st.info("כאן יופיע המשוב לאחר שתלחץ על 'הרץ בדיקה'.")
        st.markdown("</div>", unsafe_allow_html=True)

    st.divider()

    # --- ארכיון חכם לפי שיעור ---
    st.subheader("📂 ארכיון ציונים לפי שיעור")
    filter_sub = st.radio("בחר שיעור להצגת ציונים:", ["תורה", "גמרא", "מדעים", "עברית", "מתמטיקה", "אחר"], horizontal=True)
    
    filtered_data = [r for r in st.session_state.reports if r['שיעור'] == filter_sub]
    
    if filtered_data:
        df = pd.DataFrame(filtered_data)
        st.table(df[['שם', 'זמן']]) # טבלה מהירה של שמות וזמנים
        for r in reversed(filtered_data):
            with st.expander(f"דוח עבור {r['שם']} - {r['זמן']}"):
                st.markdown(r['דוח'])
    else:
        st.write(f"אין עדיין ציונים שמורים בשיעור {filter_sub}.")

    if st.sidebar.button("התנתק 🚪"):
        st.session_state.logged_in = False
        st.rerun()
