import streamlit as st
import google.generativeai as genai
from PIL import Image

st.set_page_config(page_title="EduCheck AI")
st.title("?? EduCheck AI - áãé÷ú îáçðéí")

# äâãøú äîôúç îä-Secrets ùì äîòøëú
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("ùâéàä: îôúç ä-API ìà îåâãø áîòøëú.")

rubric = st.text_area("äëðñ îçååï (îä äúùåáä äðëåðä?):")
uploaded_file = st.file_uploader("äòìä úîåðä ùì äîáçï:", type=['png', 'jpg', 'jpeg'])

if st.button("áãå÷ òëùéå"):
    if uploaded_file and rubric:
        with st.spinner('îðúç...'):
            img = Image.open(uploaded_file)
            model = genai.GenerativeModel('gemini-1.5-flash')
            prompt = f"äùååä àú äúùåáä áúîåðä ìîçååï: {rubric}. úï öéåï åäñáø ÷öø áòáøéú."
            response = model.generate_content([prompt, img])
            st.markdown("### úåöàä:")
            st.write(response.text)
    else:

        st.warning("ðà ìîìà àú ëì äùãåú.")
