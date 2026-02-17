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
# 1. הגדרות דף ומיתוג (המראה המקצועי)
# ==========================================
st.set_page_config(
    page_title="EduCheck AI", 
    page_icon="🎓", 
    layout="wide"
)

st.markdown("""
<style>
    .stApp { background-color: #0f172a; color: white; direction: rtl; text-align: right; }
    .white-bold { color: #ffffff !important; font-weight: 900 !important; text-shadow: 2px 2px 4px #000000; }
    .glass-card { background: rgba(30, 41, 59, 0.7); border: 1px solid #38bdf8; border-radius: 15px; padding: 25px; margin-bottom: 20px; }
    .stButton>button { background: linear-gradient(135deg, #38bdf8 0%, #1d4ed8 100%); color: white !important; font-weight: 700; border-radius: 10px; border: none; width: 100%; }
    .logout-btn>button { background: linear-gradient(135deg, #ef4444 0%, #991b1b 100%) !important; }
    label, p, .stMarkdown { color: white !important; font-weight: 600; }
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] { height: 50px; background-color: rgba(255,255,255,0.05); border-radius: 10px 10px 0 0; color: white !important; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. חיבור ל-AI (פתרון ה-404 הסופי)
# ==========================================
def init_gemini():
    if "GEMINI_API_KEY" not in st.secrets:
        st.error("🔑 מפתח API חסר ב-Secrets!")
        return None
    try:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        # החזרה של אובייקט מודל מוכן
        return genai.GenerativeModel('gemini-1.5-flash')
    except Exception as e:
        st.error(f"שגיאה בחיבור ל-AI: {e}")
        return None

# ==========================================
# 3. מודל ה-PyTorch (FCN32s) - החזרנו את המודל שלך
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

# טעינת המודל (יכול לקחת זמן ב-Reboot ראשון)
pytorch_model = load_pytorch_model()

# ניהול נתונים בזיכרון
if 'db' not in st.session_state:
    st.session_state.db = []
if 'rubric' not in st.session_state:
    st.session_state.rubric = ""

# --- כותרת ראשית ---
st.markdown("<h1 class='white-bold' style='text-align: center;'>EduCheck AI 🎓</h1>", unsafe_allow_html=True)

# --- תפריט ראשי ---
tab1, tab2, tab3 = st.tabs(["📄 בדיקה ומחוון", "📊 ארכיון תלמידים", "⚙️ הגדרות"])

# כרטיסייה 1: בדיקת מבחן
with tab1:
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    
    with col1:
        student_name = st.text_input("שם התלמיד:")
        subject = st.text_input("מקצוע:", "תורה")
        if st.button("✨ צור מחוון אוטומטי"):
            model_ai = init_gemini()
            if model_ai:
                with st.spinner("מייצר מחוון..."):
                    res = model_ai.generate_content(f"צור מחוון תשובות למבחן בנושא {subject}")
                    st.session_state.rubric = res.text
        st.session_state.rubric = st.text_area("מחוון הבדיקה:", value=st.session_state.rubric, height=200)
    
    with col2:
        uploaded_file = st.file_uploader("העלה צילום מבחן:", type=['jpg', 'jpeg', 'png'])
        if st.button("🚀 בדוק מבחן") and uploaded_file and student_name:
            with st.spinner("ה-AI מנתח את המבחן..."):
                try:
                    img = Image.open(uploaded_file)
                    model_ai = init_gemini()
                    if model_ai:
                        prompt = f"פענח את המבחן של {student_name} במקצוע {subject} לפי המחוון הבא: {st.session_state.rubric}. תן ציון מ-1 עד 100 ופרט בעברית מה נכון ומה לא."
                        response = model_ai.generate_content([prompt, img])
                        
                        # שמירה לארכיון
                        st.session_state.db.append({
                            "תאריך": datetime.now().strftime("%d/%m/%Y %H:%M"),
                            "תלמיד": student_name,
                            "מקצוע": subject,
                            "תוצאה": response.text
                        })
                        st.success("הבדיקה הושלמה!")
                        st.markdown("### 📝 תוצאה:")
                        st.write(response.text)
                except Exception as e:
                    st.error(f"שגיאה במהלך הבדיקה: {e}")
    st.markdown("</div>", unsafe_allow_html=True)

# כרטיסייה 2: ארכיון
with tab2:
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    if st.session_state.db:
        df = pd.DataFrame(st.session_state.db)
        st.dataframe(df, use_container_width=True)
        csv = df.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 הורד לאקסל (CSV)", data=csv, file_name="educheck_results.csv", mime="text/csv")
    else:
        st.info("הארכיון ריק כרגע.")
    st.markdown("</div>", unsafe_allow_html=True)

# כרטיסייה 3: הגדרות
with tab3:
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    st.subheader("ניהול נתונים")
    st.markdown("<div class='logout-btn'>", unsafe_allow_html=True)
    if st.button("🔴 מחק הכל ואתחל מערכת"):
        st.session_state.db = []
        st.session_state.rubric = ""
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("---")
    st.write("**גרסת מערכת:** 2.6.0 Stable Pro")
    st.markdown("</div>", unsafe_allow_html=True)
