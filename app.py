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
# 1. הגדרות מיתוג ושם האפליקציה (זה מה שחיפשת!)
# ==========================================
st.set_page_config(
    page_title="EduCheck AI",  # השם שיופיע בלשונית ובשם הקובץ המותקן
    page_icon="🎓",             # האייקון שיופיע על שולחן העבודה
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==========================================
# 2. חיבור ל-AI של גוגל (Gemini)
# ==========================================
def init_gemini():
    if "GEMINI_API_KEY" in st.secrets:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        return "gemini-1.5-flash"
    else:
        # ניסיון למשוך משתנה סביבה אם Secrets לא מוגדר (לוקאלי)
        api_key = os.environ.get("GEMINI_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)
            return "gemini-1.5-flash"
        st.error("🔑 מפתח API חסר! נא להגדיר GEMINI_API_KEY ב-Secrets.")
        return None

MODEL_NAME = init_gemini()

# ==========================================
# 3. מודל ה-PyTorch (FCN32s)
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

@st.cache_resource
def load_pytorch_model():
    model = FCN32s(n_class=2)
    model.eval()
    return model

pytorch_model = load_pytorch_model()

# ==========================================
# 4. עיצוב הממשק (CSS משופר)
# ==========================================
st.markdown("""
<style>
    /* הגדרות רקע וטקסט כללי */
    .stApp { background-color: #0f172a; color: white; direction: rtl; text-align: right; }
    
    /* כותרות לבנות ומודגשות */
    .white-bold { color: #ffffff !important; font-weight: 900 !important; text-shadow: 2px 2px 4px #000000; }
    
    /* כרטיסיות זכוכית */
    .glass-card { background: rgba(30, 41, 59, 0.7); border: 1px solid #38bdf8; border-radius: 15px; padding: 25px; margin-bottom: 20px; }
    
    /* עיצוב כפתורים כחול בולט */
    .stButton>button { 
        background: linear-gradient(135deg, #38bdf8 0%, #1d4ed8 100%); 
        color: white !important; 
        font-weight: 800; 
        border-radius: 10px; 
        border: none;
        padding: 10px 20px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    }
    
    /* התאמת צבעי הטקסט בתיבות קלט */
    label, p, .stMarkdown { color: #ffffff !important; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

# ניהול נתונים
if 'db' not in st.session_state:
    st.session_state.db = []

# --- כותרת ראשית של המותג ---
st.markdown("<h1 class='white-bold' style='text-align: center;'>EduCheck AI 🎓</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-size: 1.2rem;'>המערכת שלך לבדיקת מבחנים וסריקת אלפי מסמכים</p>", unsafe_allow_html=True)

# --- תפריט ראשי ---
tab1, tab2, tab3 = st.tabs(["📄 בדיקה יחידה", "📁 סריקת ZIP המונית", "📊 יומן ציונים"])

# כרטיסייה 1: בדיקת מבחן בודד
with tab1:
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("<p class='white-bold'>פרטי המבחן</p>", unsafe_allow_html=True)
        student_name = st.text_input("שם התלמיד:", placeholder="למשל: ישראל ישראלי")
        subject = st.text_input("מקצוע:", "תורה")
        rubric = st.text_area("מחוון תשובות (התשובות הנכונות):", placeholder="הכנס כאן את הפתרון הנכון...")
        
    with col2:
        st.markdown("<p class='white-bold'>העלאת מסמך</p>", unsafe_allow_html=True)
        uploaded_file = st.file_uploader("בחר תמונה:", type=['jpg', 'jpeg', 'png'])
        if st.button("🚀 בדוק עכשיו") and uploaded_file and student_name:
            with st.spinner("מנתח כתב יד..."):
                img = Image.open(uploaded_file)
                model = genai.GenerativeModel(MODEL_NAME)
                prompt = f"פענח את המבחן של {student_name} במקצוע {subject}. השווה למחוון: {rubric}. תן ציון ופרט טעויות."
                response = model.generate_content([prompt, img])
                
                st.session_state.db.append({
                    "תאריך": datetime.now().strftime("%d/%m/%Y %H:%M"),
                    "תלמיד": student_name,
                    "מקצוע": subject,
                    "תוצאה": response.text
                })
                st.success("הבדיקה הושלמה בהצלחה!")
                st.markdown(f"<div style='background:#1e293b; padding:15px; border-radius:10px;'>{response.text}</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# כרטיסייה 2: סריקה המונית
with tab2:
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    st.info("💡 וודא שביצעת unzip images.zip ב-Cloud Shell לפני הלחיצה.")
    
    if st.button("🔍 סרוק את כל תיקיית ה-ZIP"):
        if os.path.exists('images'):
            image_files = [f for f in os.listdir('images') if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
            st.write(f"נמצאו {len(image_files)} תמונות.")
            
            prog_bar = st.progress(0)
            for i, filename in enumerate(image_files):
                img_path = os.path.join('images', filename)
                img = Image.open(img_path)
                model = genai.GenerativeModel(MODEL_NAME)
                res = model.generate_content(["תמצת את המבחן ותן ציון", img])
                
                st.session_state.db.append({
                    "תאריך": "סריקה המונית",
                    "תלמיד": filename,
                    "מקצוע": "אוטומטי",
                    "תוצאה": res.text
                })
                prog_bar.progress((i + 1) / len(image_files))
            st.success("סריקת כל התיקייה הסתיימה!")
        else:
            st.error("תיקיית 'images' לא נמצאה.")
    st.markdown("</div>", unsafe_allow_html=True)

# כרטיסייה 3: יומן ציונים (Pandas)
with tab3:
    if st.session_state.db:
        df = pd.DataFrame(st.session_state.db)
        st.dataframe(df, use_container_width=True)
        csv = df.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 ייצא לאקסל (CSV)", data=csv, file_name="educheck_results.csv", mime="text/csv")
    else:
        st.info("אין נתונים להצגה.")
