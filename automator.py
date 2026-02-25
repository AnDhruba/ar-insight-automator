import streamlit as st
import pdfplumber
import pandas as pd
import io

#1
st.set_page_config(page_title="AR Insight Automator", layout="wide")

st.markdown("""
<style>
    /* Gradient background for the main app */
    .stApp {
        background: linear-gradient(to right bottom, #f8f9fa, #e2e8f0);
    }
    
    /* Centered Main Title */
    .main-title {
        text-align: center;
        color: #0f172a; 
        font-family: 'Helvetica Neue', sans-serif;
        font-weight: 800;
        font-size: 3rem;
        margin-bottom: 0px;
        padding-bottom: 0px;
    }
    
    /* Centered Subtitle & Links */
    .sub-title {
        text-align: center;
        color: #475569;
        font-size: 1.1rem;
        margin-top: 5px;
        margin-bottom: 30px;
    }
    
    .author-link {
        text-align: center;
        font-size: 1rem;
        margin-bottom: 20px;
    }

    /* Make the Custom Keywords text box stand out */
    div.stTextArea textarea {
        background-color: #e2e8f0 !important; /* Solid grey background */
        border: 1.5px solid #94a3b8 !important; /* Visible darker grey border */
        border-radius: 8px !important; /* Smooth rounded corners */
        color: #1e293b !important; /* Dark text for readability */
        padding: 10px !important;
    }
    
    /* Make it light up white when the user clicks inside to type */
    div.stTextArea textarea:focus {
        border: 1.5px solid #2563eb !important; /* Turns blue */
        background-color: #ffffff !important; /* Turns white */
    }
</style>
""", unsafe_allow_html=True)
#2

st.markdown("<h1 class='main-title'>📄 AR Insight Automator</h1>", unsafe_allow_html=True)
st.markdown("<div class='author-link'>Project by <a href='https://www.linkedin.com/in/dhrubajyoti-rajak-3649a6195/' target='_blank'>Dhrubajyoti Rajak</a></div>", unsafe_allow_html=True)
st.markdown("<p class='sub-title'>Upload an NSE/BSE Annual Report (PDF). This tool semantic-scans the document to extract hidden risks and critical financial paragraphs.</p>", unsafe_allow_html=True)

st.markdown("---")

default_categories = {
    "Auditor Red Flags": ["key audit matters", "emphasis of matter", "qualified opinion", "adverse opinion", "auditor's qualifications"],
    "Hidden Risks (Contingent)": ["contingent liabilities", "claims against the company", "off-balance sheet", "guarantees provided"],
    "Promoter Dealings (RPTs)": ["related party transactions", "form no. aoc-2", "transactions with key managerial personnel"],
    "Management Pay": ["remuneration of directors", "managerial remuneration", "ceo pay ratio", "sweat equity"],
    "One-Off / Profit Distortions": ["exceptional items", "extraordinary items", "impairment of assets", "non-recurring"],
    "Debt & Covenants": ["debt covenants", "default in repayment", "pledging of shares", "secured borrowings"],
    "Future Capex & Outlook": ["capital work in progress", "future outlook", "capital expenditure plans"]
}

#3
col1, col2 = st.columns(2, gap="large")

with col1:
    st.subheader("⚙️ 1. Extraction Settings")
    st.markdown("**:green[The engine is pre-loaded with standard Indian Equity Research categories. You can also add your own custom terms below.]**")

    with st.expander("👀 Click here to view the standard pre-loaded categories"):
        st.markdown("""
        * **Auditor Red Flags:** Key audit matters, emphasis of matter, qualified opinion, adverse opinion, auditor's qualifications
        * **Hidden Risks (Contingent):** Contingent liabilities, claims against the company, off-balance sheet, guarantees provided
        * **Promoter Dealings (RPTs):** Related party transactions, form no. aoc-2, transactions with key managerial personnel
        * **Management Pay:** Remuneration of directors, managerial remuneration, ceo pay ratio, sweat equity
        * **One-Off / Profit Distortions:** Exceptional items, extraordinary items, impairment of assets, non-recurring
        * **Debt & Covenants:** Debt covenants, default in repayment, pledging of shares, secured borrowings
        * **Future Capex & Outlook:** Capital work in progress, future outlook, capital expenditure plans
        """)

    user_custom_input = st.text_area(
        "Add Custom Keywords (comma-separated, optional):", 
        placeholder="e.g., litigation, tax dispute, SEBI order, factory closure",
        height=100
    )

    #4
    if user_custom_input.strip():
        custom_keywords = [kw.strip().lower() for kw in user_custom_input.split(',')]
        default_categories["Custom User Search"] = custom_keywords

with col2:
    st.subheader("📂 2. Document Upload")
    uploaded_file = st.file_uploader("Drag and drop the Annual Report PDF here", type=["pdf"])

st.markdown("---")

#4
with st.container():
    if uploaded_file is not None:
        
        #4a
        _, center_btn, _ = st.columns([1, 1, 1])
        
        with center_btn:
            run_extraction = st.button("🚀 Extract Insights", use_container_width=True)
            
        if run_extraction:
            extracted_data = []
            progress_text = "Scanning Annual Report... Please wait."
            my_bar = st.progress(0, text=progress_text)

            with pdfplumber.open(uploaded_file) as pdf:
                total_pages = len(pdf.pages)
                
                for i, page in enumerate(pdf.pages):
                    progress = int(((i + 1) / total_pages) * 100)
                    my_bar.progress(progress, text=f"Scanning page {i + 1} of {total_pages}...")
                    
                    text = page.extract_text()
                    
                    if text:
                        lines = text.split('\n')
                        
                        for category, synonyms in default_categories.items():
                            for synonym in synonyms:
                                if synonym in text.lower():
                                    for line_num, line in enumerate(lines):
                                        if synonym in line.lower():
                                            context_snippet = " ".join(lines[line_num : line_num + 7])
                                            
                                            extracted_data.append({
                                                "Category": category,
                                                "Trigger Word": synonym.title(),
                                                "Page Number": i + 1,
                                                "Exact Context": context_snippet
                                            })
                                            break

            my_bar.empty() 
            
            #5
            if extracted_data:
                st.success(f"✅ Extraction Complete! Found {len(extracted_data)} critical insights.")
                df = pd.DataFrame(extracted_data)
                
                st.dataframe(df, use_container_width=True)
                
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False, sheet_name='Insights')
                
                _, center_dl, _ = st.columns([1, 1, 1])
                with center_dl:
                    st.download_button(
                        label="📥 Download Full Excel Report",
                        data=buffer.getvalue(),
                        file_name="AR_Extracted_Insights_Pro.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
            else:
                st.warning("No keywords found. The document might be a scanned image (requires OCR).")