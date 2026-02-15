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
genai.configure(api_key="AIzaSyDJdiYe4VmudGKFQzoCI_MmngD26D4wm1Q")

ALLOWED_PASSWORDS = ["dvir2012", "Teacher2012", "Sunset2012", "מורה2012", "Dvir_2012!"]

SUBJECTS = [
    "תורה", "גמרא", "דינים", "היסטוריה", "מדעים", "עברית", "מתמטיקה", 
    "אנגלית", "גאוגרפיה", "ספרות", "אזרחות", "של''ח", "תנ''ך", "משנה",
    "הבעה", "ערבית", "פיזיקה", "כימיה", "ביולוגיה", "מחשבת ישראל", "אחר"
]

# --- 2. עיצוב הממשק ---
st.set_page_config(page_title="EduCheck AI Pro", layout="wide")
st.markdown("""
<style>
    .stApp { background: #0f172a; color: white; direction: rtl; text-align: right; }
    .glass-card { 
        background: rgba(30, 41, 59, 0.7); 
        border: 1px solid #38bdf8; 
        border-radius: 15px; 
        padding: 25px; 
        margin-top: 10px;
    }
    .main-title { 
        font-size: 2.5rem; font-weight: 800; text-align: center;
        background: linear-gradient(90deg, #38bdf8, #818cf8);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }
    .stButton>button { 
        background: linear-gradient(135deg, #38bdf8 0%, #1d4ed8 100%); 
        color: white !important; border-radius: 10px; font-weight: 700; width: 100%;
    }
    .result-box { background: #1e293b; border-right: 5px solid #38bdf8; padding: 20px; border-radius: 10px; margin-top: 20px; }
</style>
""", unsafe_allow_html=True)

if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'reports' not in st.session_state: st.session_state.reports = []
if 'rubric' not in st.session_state: st.session_state.rubric = ""

# --- 3. מסך כניסה ---
if not st.session_state.logged_in:
    _, col, _ = st.columns([1, 1, 1])
    with col:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        pwd = st.text_input("קוד גישה:", type="password")
        if st.button("התחבר"):
            if pwd in ALLOWED_PASSWORDS:
                st.session_state.logged_in = True
                st.rerun()
            else: st.error("קוד שגוי")
        st.markdown("</div>", unsafe_allow_html=True)

# --- 4. המערכת המרכזית (כרטיסיות) ---
else:
    st.markdown("<h1 class='main-title'>EduCheck AI Pro 🎓</h1>", unsafe_allow_html=True)
    
    # יצירת הכרטיסיות
    tab_check, tab_archive = st.tabs(["🔍 בדיקת מבחן ומחוון", "📂 ארכיון תשובות"])

    # --- כרטיסייה 1: בדיקת מבחן ומחוון ---
    with tab_check:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        col_a, col_b = st.columns([1, 1])
        
        with col_a:
            subject_active = st.selectbox("בחר מקצוע:", SUBJECTS)
            s_name = st.text_input("שם התלמיד:")
            
            st.write("**מחוון תשובות:**")
            if st.button("✨ צור מחוון אוטומטי עם Gemini"):
                model = genai.GenerativeModel('gemini-1.5-flash')
                res = model.generate_content(f"צור מחוון תשובות למבחן ב{subject_active}.")
                st.session_state.rubric = res.text
            st.session_state.rubric = st.text_area("תוכן המחוון:", value=st.session_state.rubric, height=150)

        with col_b:
            st.write("**העלאת המבחן:**")
            up_file = st.file_uploader("בחר צילום מבחן:", type=['jpg', 'png', 'jpeg'])
            
            if st.button("🚀 הרץ בדיקה פדגוגית"):
                if up_file and s_name and st.session_state.rubric:
                    with st.spinner("מנתח..."):
                        img_pil = Image.open(up_file)
                        model = genai.GenerativeModel('gemini-1.5-flash')
                        prompt = f"נתח מבחן ב{subject_active} של {s_name} לפי המחוון: {st.session_state.rubric}. תן ציון ומשוב."
                        res = model.generate_content([prompt, img_pil])
                        
                        st.session_state.current_res = res.text
                        st.session_state.reports.append({
                            "שם": s_name, "שיעור": subject_active, "דוח": res.text, "זמן": datetime.now().strftime("%H:%M")
                        })
                else: st.warning("מלא את כל הפרטים")
            
            if 'current_res' in st.session_state:
                st.markdown("<div class='result-box'>", unsafe_allow_html=True)
                st.markdown(st.session_state.current_res)
                st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # --- כרטיסייה 2: ארכיון תשובות ---
    with tab_archive:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        filter_sub = st.selectbox("בחר מקצוע לצפייה:", ["הכל"] + SUBJECTS)
        
        display_data = st.session_state.reports if filter_sub == "הכל" else [r for r in st.session_state.reports if r['שיעור'] == filter_sub]
        
        if display_data:
            for r in reversed(display_data):
                with st.expander(f"{r['שם']} - {r['שיעור']} ({r['זמן']})"):
                    st.markdown(r['דוח'])
        else:
            st.info("אין עדיין ציונים שמורים למקצוע זה.")
        st.markdown("</div>", unsafe_allow_html=True)

    if st.sidebar.button("התנתק 🚪"):
        st.session_state.logged_in = False
        st.rerun()
