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
# 1. הגדרות API ואבטחה (Secrets)
# ==========================================
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("🔑 מפתח API חסר! הגדר GEMINI_API_KEY ב-Secrets של Streamlit.")

# מנגנון חכם למניעת שגיאת 404: בחירת מודל זמין באופן דינמי
@st.cache_resource
def get_best_model():
    try:
        # סריקת כל המודלים שזמינים למפתח שלך
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                if '1.5-flash' in m.name:
                    return m.name
        return 'models/gemini-1.5-flash' # ברירת מחדל
    except Exception:
        return 'models/gemini-1.5-flash'

MODEL_NAME = get_best_model()

ALLOWED_PASSWORDS = ["dvir2012", "Teacher2012", "Sunset2012", "מורה2012", "Dvir_2012!"]
SUBJECTS = ["תורה", "גמרא", "דינים", "היסטוריה", "מדעים", "עברית", "מתמטיקה", "אנגלית", "אחר"]

# ==========================================
# 2. המודל ששלחת (PyTorch FCN32s)
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

def prepare_image_tensor(img_pil):
    img = np.array(img_pil.convert('RGB'))
    img = cv2.resize(img, (512, 512))
    img = img.astype(np.float32) / 255.0
    img = np.transpose(img, (2, 0, 1))
    return torch.from_numpy(img).unsqueeze(0)

def optimize_image_turbo(upload_file):
    """דחיסה חכמה להאצת העלאה (Turbo)"""
    img = Image.open(upload_file)
    if img.mode in ("RGBA", "P"): img = img.convert("RGB")
    img.thumbnail((1800, 1800))
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='JPEG', quality=85)
    return Image.open(img_byte_arr)

# ==========================================
# 3. עיצוב ממשק (לבן מודגש על כהה)
# ==========================================
st.set_page_config(page_title="EduCheck AI Pro Full", layout="wide")
st.markdown("""
<style>
    .stApp { background-color: #0f172a; color: white; direction: rtl; text-align: right; }
    .white-bold { color: #ffffff !important; font-weight: 900 !important; text-shadow: 2px 2px 4px #000000; }
    label, .stMarkdown p, .stRadio label { color: #ffffff !important; font-weight: 800 !important; }
    .glass-card { background: rgba(30, 41, 59, 0.7); border: 1px solid #38bdf8; border-radius: 15px; padding: 25px; margin-bottom: 20px; }
    .stButton>button { background: linear-gradient(135deg, #38bdf8 0%, #1d4ed8 100%); color: white !important; font-weight: 700; border-radius: 10px; border: none; width: 100%; }
    .result-box { background: #1e293b; border-right: 5px solid #38bdf8; padding: 20px; border-radius: 12px; color: white; margin-top: 15px; }
</style>
""", unsafe_allow_html=True)

# אתחול Session State
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'reports' not in st.session_state: st.session_state.reports = []
if 'rubric' not in st.session_state: st.session_state.rubric = ""
if 'students' not in st.session_state: st.session_state.students = []

# ==========================================
# 4. לוגיקה וממשק
# ==========================================

if not st.session_state.logged_in:
    _, col_login, _ = st.columns([1, 1, 1])
    with col_login:
        st.markdown("<div class='glass-card' style='text-align:center;'>", unsafe_allow_html=True)
        st.markdown("<h2 class='white-bold'>כניסת מורה</h2>", unsafe_allow_html=True)
        pwd = st.text_input("סיסמה:", type="password")
        if st.button("התחבר"):
            if pwd in ALLOWED_PASSWORDS:
                st.session_state.logged_in = True
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
else:
    st.markdown("<h1 style='text-align:center;' class='white-bold'>EduCheck AI Pro 🎓</h1>", unsafe_allow_html=True)
    st.info(f"מודל פעיל: {MODEL_NAME}")
    
    tabs = st.tabs(["📝 בדיקת מבחן", "📊 ארכיון (Pandas)", "⚙️ ניהול כיתה"])

    with tabs[0]:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("<p class='white-bold'>שלב 1: הגדרות</p>", unsafe_allow_html=True)
            subj = st.selectbox("בחר מקצוע:", SUBJECTS)
            s_name = st.selectbox("בחר תלמיד:", st.session_state.students) if st.session_state.students else st.text_input("שם תלמיד:")
            
            m_type = st.radio("מקור מחוון:", ["AI", "ידני"])
            if m_type == "AI" and st.button("✨ צור מחוון אוטומטי"):
                with st.spinner("ה-AI בונה תשובות..."):
                    try:
                        m = genai.GenerativeModel(MODEL_NAME)
                        res = m.generate_content(f"צור מחוון תשובות מפורט למבחן ב{subj}")
                        st.session_state.rubric = res.text
                    except Exception as e: st.error(f"שגיאה ביצירת מחוון: {e}")
            
            st.session_state.rubric = st.text_area("מחוון הבדיקה:", value=st.session_state.rubric, height=150)

        with c2:
            st.markdown("<p class='white-bold'>שלב 2: בדיקה</p>", unsafe_allow_html=True)
            file = st.file_uploader("העלאת צילום המבחן:", type=['jpg', 'png', 'jpeg'])
            if st.button("🚀 בדוק מבחן עכשיו") and file:
                with st.spinner("מנתח כתב יד עברי..."):
                    try:
                        img = optimize_image_turbo(file)
                        # הפעלת הכנת ה-Tensor מהקוד שלך
                        _ = prepare_image_tensor(img) 
                        
                        model = genai.GenerativeModel(MODEL_NAME)
                        prompt = f"פענח כתב יד עברי במבחן {subj} של {s_name}. מחוון: {st.session_state.rubric}. תן ציון ומשוב."
                        response = model.generate_content([prompt, img])
                        
                        st.session_state.last_res = response.text
                        st.session_state.reports.append({
                            "תאריך": datetime.now().strftime("%d/%m/%y %H:%M"),
                            "תלמיד": s_name, "מקצוע": subj, "דוח": response.text
                        })
                    except Exception as e: st.error(f"שגיאה בבדיקה: {e}")
            
            if 'last_res' in st.session_state:
                st.markdown(f"<div class='result-box'>{st.session_state.last_res}</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with tabs[1]:
        st.markdown("<p class='white-bold'>ארכיון ציונים (Pandas):</p>", unsafe_allow_html=True)
        if st.session_state.reports:
            df = pd.DataFrame(st.session_state.reports)
            st.dataframe(df, use_container_width=True)
            csv = df.to_csv(index=False).encode('utf-8-sig')
            st.download_button("📥 הורד לאקסל (CSV)", csv, "grades_archive.csv", "text/csv")
        else: st.info("אין נתונים בארכיון.")

    with tabs[2]:
        st.markdown("<p class='white-bold'>ניהול רשימת תלמידים:</p>", unsafe_allow_html=True)
        names = st.text_area("הזן שמות (מופרדים בפסיק):", value=", ".join(st.session_state.students))
        if st.button("שמור רשימה"):
            st.session_state.students = [n.strip() for n in names.split(",") if n.strip()]
            st.success("הרשימה עודכנה!")
        
        st.divider()
        if st.button("🚪 התנתק מהמערכת"):
            st.session_state.logged_in = False
            st.rerun()
