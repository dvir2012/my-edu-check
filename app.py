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
        font-size: 3rem; font-weight: 800; text-align: center;
        background: linear-gradient(90deg, #38bdf8, #818cf8);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }
    .stButton>button { 
        background: linear-gradient(135deg, #38bdf8 0%, #1d4ed8 100%); 
        color: white !important; border-radius: 12px; font-weight: 700; width: 100%;
    }
    .exam-preview { border: 3px solid #38bdf8; border-radius: 15px; padding: 10px; background: #1e293b; margin-top: 10px; }
    .rubric-area { background: #0c4a6e; border-radius: 10px; padding: 15px; border-right: 5px solid #0ea5e9; }
</style>
""", unsafe_allow_html=True)

if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'reports' not in st.session_state: st.session_state.reports = []
if 'rubric_text' not in st.session_state: st.session_state.rubric_text = ""

# --- 4. מסך כניסה ---
if not st.session_state.logged_in:
    st.markdown("<div style='height: 15vh;'></div>", unsafe_allow_html=True)
    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        st.markdown("<div class='glass-card' style='text-align: center;'>", unsafe_allow_html=True)
        st.markdown("<h2>כניסת מורה מורשה</h2>", unsafe_allow_html=True)
        pwd = st.text_input("קוד גישה:", type="password")
        if st.button("התחבר"):
            if pwd in ALLOWED_PASSWORDS:
                st.session_state.logged_in = True
                st.rerun()
            else: st.error("קוד שגוי")
        st.markdown("</div>", unsafe_allow_html=True)

# --- 5. המערכת המרכזית ---
else:
    st.markdown("<h1 class='main-title'>EduCheck AI Pro 🎓</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center;'>פיתוח: דביר ויגל טולדנו</p>", unsafe_allow_html=True)

    tab_scan, tab_archive = st.tabs(["🔍 בדיקה וניתוח", "📊 ארכיון ציונים"])

    with tab_scan:
        col_setup, col_preview = st.columns([1, 1.2])

        with col_setup:
            # שלב 1: פרטים
            st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
            st.subheader("1. פרטי המבחן")
            s_name = st.text_input("שם התלמיד:")
            subject = st.selectbox("מקצוע המבחן:", ["תורה", "גמרא", "מדעים", "עברית", "מתמטיקה", "אחר"])
            st.markdown("</div>", unsafe_allow_html=True)

            # שלב 2: מחוון תשובות (Rubric)
            st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
            st.subheader("2. מחוון תשובות (Rubric)")
            st.write("הגדר ל-AI מהן התשובות הנכונות:")
            
            if st.button("✨ צור מחוון אוטומטי עם Gemini"):
                with st.spinner("בונה מחוון למקצוע..."):
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    res_rub = model.generate_content(f"צור מחוון תשובות למבחן ב{subject}. כלול נקודות מרכזיות למענה נכון וקריטריונים לציון.")
                    st.session_state.rubric_text = res_rub.text
            
            st.session_state.rubric_text = st.text_area("ערוך את המחוון (ניתן להדביק כאן תשובות נכונות):", 
                                                    value=st.session_state.rubric_text, height=200)
            st.markdown("</div>", unsafe_allow_html=True)

            # שלב 3: העלאה
            st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
            st.subheader("3. מקור תמונה")
            up_file = st.file_uploader("העלה מבחן:", type=['jpg', 'png', 'jpeg'])
            cam_file = st.camera_input("צילום ישיר")
            st.markdown("</div>", unsafe_allow_html=True)

        with col_preview:
            st.subheader("🖼️ אזור המבחן")
            active_img = cam_file if cam_file else up_file
            
            if active_img:
                img_pil = Image.open(active_img)
                st.markdown("<div class='exam-preview'>", unsafe_allow_html=True)
                st.image(img_pil, caption=f"בדיקת המבחן של {s_name}", use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)
                
                if st.button("🚀 הרץ בדיקה מול המחוון"):
                    if s_name and st.session_state.rubric_text:
                        with st.spinner("מנתח כתב יד ומשווה לתשובות הנכונות..."):
                            # FCN
                            _ = hw_model(prepare_image(img_pil))
                            # Gemini Analysis
                            model = genai.GenerativeModel('gemini-1.5-flash')
                            full_prompt = f"""
                            אתה מורה מקצועי שבודק מבחן ב{subject} עבור התלמיד {s_name}.
                            להלן מחוון התשובות והקריטריונים לבדיקה:
                            {st.session_state.rubric_text}
                            
                            משימה:
                            1. פענח את כתב היד העברי בתמונה.
                            2. השווה את תשובות התלמיד למחוון שסופק.
                            3. תן ציון סופי בפורמט: **ציון: XX/100**.
                            4. פרט משוב פדגוגי בעברית על הטעויות וההצלחות.
                            """
                            res = model.generate_content([full_prompt, img_pil])
                            
                            st.session_state.reports.append({
                                "שם": s_name, "מקצוע": subject, "דוח": res.text, "תאריך": datetime.now().strftime("%d/%m/%y %H:%M")
                            })
                            st.markdown("### 📝 תוצאות הניתוח:")
                            st.markdown(f"<div class='glass-card'>{res.text}</div>", unsafe_allow_html=True)
                    else:
                        st.warning("חובה להזין שם תלמיד ולוודא שהמחוון אינו ריק.")
            else:
                st.info("אנא העלה תמונה של מבחן כדי להתחיל.")

    with tab_archive:
        if st.session_state.reports:
            df = pd.DataFrame(st.session_state.reports)
            st.download_button("📥 הורד ציונים לאקסל", df.to_csv(index=False).encode('utf-8-sig'), "grades.csv")
            for r in reversed(st.session_state.reports):
                with st.expander(f"{r['שם']} - {r['מקצוע']} ({r['תאריך']})"):
                    st.markdown(r['דוח'])
        else: st.info("אין דוחות שמורים.")

    if st.sidebar.button("התנתק 🚪"):
        st.session_state.logged_in = False
        st.rerun()
