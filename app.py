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
    page_title="EduCheck AI", # זה השם שיופיע במחשב כשתתקין
    page_icon="🎓", 
    layout="wide"
)

# ==========================================
# 2. חיבור ל-AI של גוגל (Gemini)
# ==========================================
# פונקציה לבדיקת מפתח ה-API ומניעת שגיאות 404
def init_gemini():
    if "GEMINI_API_KEY" not in st.secrets:
        st.error("🔑 מפתח API חסר! נא להגדיר GEMINI_API_KEY ב-Secrets של Streamlit.")
        return None
    try:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        # מחפש את המודל הכי מעודכן שזמין עבורכם
        return "gemini-1.5-flash"
    except Exception as e:
        st.error(f"שגיאה בחיבור ל-AI: {e}")
        return None

MODEL_NAME = init_gemini()

# ==========================================
# 3. מודל ה-PyTorch שביקשת (FCN32s)
# ==========================================
class FCN32s(nn.Module):
    def __init__(self, n_class=21): # שיניתי ל-21 כברירת מחדל של VGG
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

# פונקציה לטעינת המודל (אם יש קובץ משקולות .pth)
@st.cache_resource
def load_pytorch_model():
    model = FCN32s(n_class=2) # מותאם לזיהוי כתב יד (שחור/לבן)
    # אם יש לכם קובץ מאומן, כאן טוענים אותו: 
    # model.load_state_dict(torch.load('model_weights.pth', map_location='cpu'))
    model.eval()
    return model

pytorch_model = load_pytorch_model()

# ==========================================
# 4. עיצוב הממשק (CSS) - לבן על כהה
# ==========================================
st.markdown("""
<style>
    .stApp { background-color: #0f172a; color: white; direction: rtl; text-align: right; }
    .white-bold { color: #ffffff !important; font-weight: 900 !important; text-shadow: 2px 2px 4px #000000; }
    .glass-card { background: rgba(30, 41, 59, 0.7); border: 1px solid #38bdf8; border-radius: 15px; padding: 25px; margin-bottom: 20px; }
    .stButton>button { background: linear-gradient(135deg, #38bdf8 0%, #1d4ed8 100%); color: white !important; font-weight: 700; border-radius: 10px; border: none; }
</style>
""", unsafe_allow_html=True)

# ניהול נתונים ב-Pandas (שמירה בזיכרון האפליקציה)
if 'db' not in st.session_state:
    st.session_state.db = []

# --- כותרת ---
st.markdown("<h1 class='white-bold' style='text-align: center;'>EduCheck AI 🎓</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>מערכת חכמה לבדיקת מבחנים וסריקת כתב יד</p>", unsafe_allow_html=True)

# --- תפריט ראשי ---
tab1, tab2, tab3 = st.tabs(["📄 בדיקת מבחן בודד", "📁 סריקה המונית (ZIP)", "📊 יומן ציונים (Pandas)"])

# כרטיסייה 1: בדיקת מבחן
with tab1:
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    
    with col1:
        student_name = st.text_input("שם התלמיד:")
        subject = st.text_input("מקצוע:", "תורה")
        rubric = st.text_area("מחוון תשובות (מה התשובות הנכונות?):")
        
    with col2:
        uploaded_file = st.file_uploader("העלה צילום של המבחן:", type=['jpg', 'jpeg', 'png'])
        if st.button("🚀 התחל בדיקה") and uploaded_file and student_name:
            with st.spinner("ה-AI מנתח את כתב היד..."):
                img = Image.open(uploaded_file)
                # שימוש ב-Gemini
                model = genai.GenerativeModel(MODEL_NAME)
                prompt = f"פענח את המבחן של {student_name} במקצוע {subject}. השווה למחוון: {rubric}. תן ציון ופרט טעויות."
                response = model.generate_content([prompt, img])
                
                # שמירה ל-Pandas
                res_data = {
                    "תאריך": datetime.now().strftime("%d/%m/%Y %H:%M"),
                    "תלמיד": student_name,
                    "מקצוע": subject,
                    "תוצאה": response.text
                }
                st.session_state.db.append(res_data)
                st.success("הבדיקה הושלמה!")
                st.markdown(f"**תוצאה:** \n\n {response.text}")
    st.markdown("</div>", unsafe_allow_html=True)

# כרטיסייה 2: סריקה המונית (אלפי תמונות)
with tab2:
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    st.info("כדי להשתמש בזה, העלה קובץ images.zip ב-Cloud Shell ועשה unzip.")
    
    if st.button("🔍 סרוק את כל תיקיית התמונות"):
        if os.path.exists('images'):
            image_files = [f for f in os.listdir('images') if f.endswith(('.png', '.jpg', '.jpeg'))]
            st.write(f"נמצאו {len(image_files)} תמונות לסריקה.")
            
            prog_bar = st.progress(0)
            for i, filename in enumerate(image_files):
                img_path = os.path.join('images', filename)
                img = Image.open(img_path)
                
                model = genai.GenerativeModel(MODEL_NAME)
                res = model.generate_content(["תמצת את הכתוב במבחן זה ותן ציון הערכתי", img])
                
                st.session_state.db.append({
                    "תאריך": "סריקה המונית",
                    "תלמיד": filename,
                    "מקצוע": "אוטומטי",
                    "תוצאה": res.text
                })
                prog_bar.progress((i + 1) / len(image_files))
            st.success("סריקת כל התיקייה הסתיימה!")
        else:
            st.error("לא נמצאה תיקייה בשם 'images'. וודא שהעלת ZIP וביצעת חילוץ.")
    st.markdown("</div>", unsafe_allow_html=True)

# כרטיסייה 3: יומן ציונים
with tab3:
    if st.session_state.db:
        df = pd.DataFrame(st.session_state.db)
        st.markdown("<p class='white-bold'>טבלת הישגים:</p>", unsafe_allow_html=True)
        st.dataframe(df, use_container_width=True)
        
        # כפתור הורדה לאקסל
        csv = df.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 הורד דוח לאקסל (CSV)", data=csv, file_name="educheck_results.csv", mime="text/csv")
    else:
        st.write("אין עדיין ציונים במערכת.")
