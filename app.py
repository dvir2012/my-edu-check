import streamlit as st
import google.generativeai as genai
from PIL import Image
import torch
import torch.nn as nn
from torchvision import models, transforms
import cv2
import numpy as np
import io
import pandas as pd
from datetime import datetime
import time

# ==========================================
# 1. הגדרות ליבת המערכת ו-API
# ==========================================
# שימוש בגרסה היציבה ביותר למניעת שגיאות 404
MODEL_NAME = 'gemini-1.5-flash-latest' 
genai.configure(api_key="AIzaSyDJdiYe4VmudGKFQzoCI_MmngD26D4wm1Q")

ALLOWED_PASSWORDS = ["dvir2012", "Teacher2012", "Sunset2012", "מורה2012", "Dvir_2012!"]

SUBJECTS = [
    "תורה", "גמרא", "דינים", "היסטוריה", "מדעים", "עברית", "מתמטיקה", 
    "אנגלית", "גאוגרפיה", "ספרות", "אזרחות", "של''ח", "תנ''ך", "משנה",
    "הבעה", "ערבית", "פיזיקה", "כימיה", "ביולוגיה", "מחשבת ישראל", "אחר"
]

# ==========================================
# 2. מימוש מודל ה-DEEP LEARNING (PyTorch)
# ==========================================
class FCN32s(nn.Module):
    """
    מימוש רשת סגמנטציה מלאה מבוססת VGG16 כפי ששלחת.
    נועד לזיהוי אזורי טקסט בכתב יד.
    """
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

def prepare_image_dl(img_pil):
    """הכנת התמונה למודל ה-DL ברזולוציה מותאמת"""
    img = np.array(img_pil.convert('RGB'))
    img = cv2.resize(img, (512, 512))
    img = img.astype(np.float32) / 255.0
    img = np.transpose(img, (2, 0, 1))
    return torch.from_numpy(img).unsqueeze(0)

# ==========================================
# 3. פונקציות עזר לעיבוד והאצה (Turbo)
# ==========================================
def optimize_image_for_ai(upload_file):
    """אופטימיזציה של נפח התמונה מבלי לאבד חדות בכתב היד"""
    img = Image.open(upload_file)
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")
    
    # חישוב יחס היבט לשמירה על פרופורציות
    max_size = 2000
    ratio = min(max_size / img.size[0], max_size / img.size[1])
    new_size = (int(img.size[0] * ratio), int(img.size[1] * ratio))
    
    img = img.resize(new_size, Image.LANCZOS)
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='JPEG', quality=85)
    return Image.open(img_byte_arr)

# ==========================================
# 4. עיצוב ממשק המשתמש (CSS מורחב)
# ==========================================
st.set_page_config(page_title="EduCheck AI Pro v2.0", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #0f172a; color: #f8fafc; direction: rtl; text-align: right; }
    
    /* כרטיסיות זכוכית (Glassmorphism) */
    .glass-card {
        background: rgba(30, 41, 59, 0.7);
        border: 1px solid rgba(56, 189, 248, 0.3);
        border-radius: 16px;
        padding: 2rem;
        box-shadow: 0 4px 30px rgba(0, 0, 0, 0.1);
        backdrop-filter: blur(5px);
    }
    
    /* טקסטים לבנים מודגשים לקריאות מקסימלית */
    .white-bold {
        color: #ffffff !important;
        font-weight: 900 !important;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
    }
    
    .main-header {
        background: linear-gradient(to right, #38bdf8, #818cf8);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3rem;
        font-weight: 800;
        text-align: center;
        margin-bottom: 1rem;
    }
    
    /* עיצוב כפתורים */
    .stButton>button {
        background: linear-gradient(135deg, #38bdf8 0%, #1d4ed8 100%);
        color: white !important;
        border: none;
        padding: 0.75rem 1.5rem;
        border-radius: 12px;
        font-weight: 700;
        transition: all 0.3s ease;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(56, 189, 248, 0.4);
    }
    
    /* תיבת תוצאה */
    .result-container {
        background: #1e293b;
        border-right: 6px solid #38bdf8;
        padding: 20px;
        border-radius: 12px;
        font-size: 1.1rem;
        line-height: 1.6;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 5. ניהול מצב המערכת (Session State)
# ==========================================
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'reports_list' not in st.session_state: st.session_state.reports_list = []
if 'current_rubric' not in st.session_state: st.session_state.current_rubric = ""
if 'class_list' not in st.session_state: st.session_state.class_list = []

# ==========================================
# 6. לוגיקה עסקית וממשק
# ==========================================

# --- מסך כניסה ---
if not st.session_state.logged_in:
    _, col_login, _ = st.columns([1, 1, 1])
    with col_login:
        st.markdown("<div class='glass-card' style='text-align: center;'>", unsafe_allow_html=True)
        st.markdown("<h2 class='white-bold'>כניסת מורים</h2>", unsafe_allow_html=True)
        user_pwd = st.text_input("הזן קוד גישה סודי:", type="password")
        if st.button("התחבר עכשיו"):
            if user_pwd in ALLOWED_PASSWORDS:
                st.session_state.logged_in = True
                st.success("התחברת בהצלחה!")
                time.sleep(1)
                st.rerun()
            else:
                st.error("קוד שגוי. נסה שוב.")
        st.markdown("</div>", unsafe_allow_html=True)

# --- מערכת ראשית ---
else:
    st.markdown("<h1 class='main-header'>EduCheck AI Pro</h1>", unsafe_allow_html=True)
    
    tabs = st.tabs(["🔍 בדיקת מבחנים", "📊 דוחות וציונים (Pandas)", "⚙️ ניהול מערכת"])
    
    # --- כרטיסייה 1: בדיקה ---
    with tabs[0]:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        c_right, c_left = st.columns([1, 1])
        
        with c_right:
            st.markdown("<p class='white-bold'>1. פרטי המבחן</p>", unsafe_allow_html=True)
            active_subject = st.selectbox("בחר מקצוע לימוד:", SUBJECTS)
            
            if st.session_state.class_list:
                active_student = st.selectbox("בחר תלמיד מהרשימה:", st.session_state.class_list)
            else:
                active_student = st.text_input("הקלד שם תלמיד:")
            
            st.divider()
            st.markdown("<p class='white-bold'>2. מחוון תשובות (Rubric)</p>", unsafe_allow_html=True)
            
            rub_type = st.radio("מקור המחוון:", ["יצירה אוטומטית (AI)", "העלאת קובץ מחוון", "הקלדה חופשית"])
            
            if rub_type == "יצירה אוטומטית (AI)":
                if st.button("צור מחוון בעזרת המודל"):
                    with st.spinner("יוצר מחוון..."):
                        m = genai.GenerativeModel(MODEL_NAME)
                        r = m.generate_content(f"צור מחוון תשובות מפורט ומקצועי למבחן בנושא {active_subject}")
                        st.session_state.current_rubric = r.text
            
            elif rub_type == "העלאת קובץ מחוון":
                rub_file = st.file_uploader("העלה צילום של דף התשובות:", type=['jpg', 'png', 'jpeg'])
                if rub_file and st.button("סרוק מחוון"):
                    with st.spinner("מפענח מחוון..."):
                        img_r = optimize_image_for_ai(rub_file)
                        m = genai.GenerativeModel(MODEL_NAME)
                        r = m.generate_content(["תמלל את מחוון התשובות שבתמונה בצורה מסודרת:", img_r])
                        st.session_state.current_rubric = r.text

            st.session_state.current_rubric = st.text_area("תוכן המחוון הסופי:", value=st.session_state.current_rubric, height=200)

        with c_left:
            st.markdown("<p class='white-bold'>3. העלאת מבחן ובדיקה</p>", unsafe_allow_html=True)
            test_image = st.file_uploader("בחר צילום מבחן (תומך בכתב יד עברי):", type=['jpg', 'png', 'jpeg'])
            
            if st.button("🚀 הרץ בדיקה פדגוגית") and test_image:
                with st.spinner(f"ה-AI מפענח את כתב היד של {active_student}..."):
                    try:
                        # אופטימיזציה מהירה
                        processed_test = optimize_image_for_ai(test_image)
                        
                        # הכנה למודל ה-Deep Learning ששלחת
                        dl_tensor = prepare_image_dl(processed_test)
                        
                        # קריאה ל-Gemini לפענוח התוכן
                        gen_model = genai.GenerativeModel(MODEL_NAME)
                        full_prompt = f"""
                        אתה מורה מקצועי הבודק מבחן ב{active_subject}.
                        שם התלמיד: {active_student}.
                        מחוון בדיקה: {st.session_state.current_rubric}.
                        
                        הוראות:
                        1. פענח את כתב היד בעברית בתמונה המצורפת.
                        2. השווה כל תשובה למחוון.
                        3. כתוב דוח הכולל: ציון סופי, מה נכון, ואיפה הטעויות.
                        4. היה סבלני עם כתב היד והבנת ההקשר.
                        """
                        
                        final_response = gen_model.generate_content([full_prompt, processed_test])
                        st.session_state.last_output = final_response.text
                        
                        # שמירה לארכיון כ-Dictionary עבור Pandas
                        st.session_state.reports_list.append({
                            "תאריך": datetime.now().strftime("%d/%m/%Y %H:%M"),
                            "תלמיד": active_student,
                            "מקצוע": active_subject,
                            "ציון": "נמצא בדוח",
                            "דוח מלא": final_response.text
                        })
                    except Exception as e:
                        st.error(f"אירעה שגיאה בתהליך: {str(e)}")

            if 'last_output' in st.session_state:
                st.markdown("<p class='white-bold'>תוצאת הבדיקה:</p>", unsafe_allow_html=True)
                st.markdown(f"<div class='result-container'>{st.session_state.last_output}</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # --- כרטיסייה 2: ארכיון ו-Pandas ---
    with tabs[1]:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.markdown("<h3 class='white-bold'>ניהול נתונים ב-Pandas</h3>", unsafe_allow_html=True)
        
        if st.session_state.reports_list:
            df = pd.DataFrame(st.session_state.reports_list)
            
            # הצגת הטבלה
            st.dataframe(df, use_container_width=True)
            
            # אפשרות הורדה ל-CSV
            csv = df.to_csv(index=False).encode('utf-8-sig')
            st.download_button("📥 הורד נתוני ציונים לאקסל (CSV)", data=csv, file_name="grades_archive.csv", mime="text/csv")
        else:
            st.info("אין עדיין ציונים בארכיון.")
        st.markdown("</div>", unsafe_allow_html=True)

    # --- כרטיסייה 3: הגדרות ---
    with tabs[2]:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.markdown("<h3 class='white-bold'>הגדרות כיתה</h3>", unsafe_allow_html=True)
        raw_names = st.text_area("הזן רשימת תלמידים (מופרדים בפסיקים):", value=", ".join(st.session_state.class_list))
        if st.button("שמור רשימת כיתה"):
            st.session_state.class_list = [n.strip() for n in raw_names.split(",") if n.strip()]
            st.success("הרשימה עודכנה!")
            
        st.divider()
        if st.button("🚪 התנתק מהמערכת"):
            st.session_state.logged_in = False
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
