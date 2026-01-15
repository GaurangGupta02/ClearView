import os
import tempfile
import matplotlib.pyplot as plt
import streamlit as st
from modules.extractor import extract_text_from_pdf
from modules.replacer import load_abbreviations, replace_with_abbreviations
from modules.abbreviator import abbreviate_pdf

# ---------------- LIGHTWEIGHT SUMMARIZER (NO MODELS) ----------------

def lightweight_summarizer(text, num_sentences=10):
    import re
    from collections import Counter

    text = text.replace("\n", " ")
    sentences = re.split(r'(?<=[.!?]) +', text)

    if len(sentences) <= num_sentences:
        return text

    words = re.findall(r'\w+', text.lower())
    freq = Counter(words)

    scores = {}
    for s in sentences:
        scores[s] = sum(freq[w] for w in re.findall(r'\w+', s.lower()))

    top_sentences = sorted(scores, key=scores.get, reverse=True)[:num_sentences]
    return " ".join(s for s in sentences if s in top_sentences)

# -------------------------------------------------------------------

# Page Config
st.set_page_config(page_title="DocMinimizer", layout="wide")
st.title("📄 ClearView")

uploaded_file = st.file_uploader("Upload your PDF", type=["pdf"])

# -------------------------------------------------------------------
# 🔹 FIXED LIGHT MODE STYLING (NO NIGHT MODE)
# -------------------------------------------------------------------

background_color = "#0d7fdd"
text_color = "#F0EFEFFF"
widget_color = "#193675"

st.markdown(f"""
<style>
.stApp {{
    background-color: {background_color};
    color: {text_color};
}}

.stTextArea textarea,
.stTextInput input,
.stButton button,
.stDownloadButton button {{
    background-color: {widget_color};
    color: {text_color};
}}

[data-testid="stMetric"] {{
    background-color: {widget_color};
    padding: 10px;
    border-radius: 6px;
}}

h1, h2, h3, h4, h5, h6 {{
    color: {text_color} !important;
}}

🔤 TABLE FIX 
[data-testid="stTable"] table {{
    background-color: #193675 !important;
    color: #F0EFEF !important;
}}

[data-testid="stTable"] th,
[data-testid="stTable"] td {{
    background-color: #193675 !important;
    color: #F0EFEF !important;
    border: none !important;
}}
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------------------------

if uploaded_file:
    include_reference_pages = st.toggle(
        "Include abbreviation reference pages",
        value=False
    )

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_input:
        temp_input.write(uploaded_file.read())
        input_path = temp_input.name

    output_path = input_path.replace(".pdf", "_minimized.pdf")

    original_text_pages = extract_text_from_pdf(input_path)

    # ---------------- PDF SUMMARY ----------------
    st.markdown("## 📝 Smart PDF Summary")

    full_text = " ".join(original_text_pages)
    num_pages = len(original_text_pages)

    with st.spinner("Generating summary..."):
        if num_pages == 1:
            summary = lightweight_summarizer(full_text, num_sentences=6)
        else:
            summary = lightweight_summarizer(full_text, num_sentences=15)

        st.text_area("Document Summary", summary, height=300)

    # --------------------------------------------

    abbreviations = load_abbreviations("config/abbreviations.json")
    replaced_pages = replace_with_abbreviations(original_text_pages, abbreviations)

    used_abbr = abbreviate_pdf(
        input_path,
        output_path,
        abbreviations,
        return_used=True,
        include_reference_pages=include_reference_pages
    )

    original_size = os.path.getsize(input_path)
    minimized_size = os.path.getsize(output_path)
    percent_reduction = (
        (original_size - minimized_size) / original_size * 100
        if original_size else 0
    )

    # Text Comparison
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📄 Original Text")
        st.text_area("Before", "\n\n".join(original_text_pages[:2]), height=400)
    with col2:
        st.subheader("📉 Minimized Text")
        st.text_area("After", "\n\n".join(replaced_pages[:2]), height=400)

    st.markdown("---")

    # Metrics
    st.subheader("📊 Compression Summary")
    c1, c2, c3 = st.columns(3)
    c1.metric("Original Size (KB)", f"{original_size/1024:.2f}")
    c2.metric("Minimized Size (KB)", f"{minimized_size/1024:.2f}")
    c3.metric("Reduction (%)", f"{percent_reduction:.2f}%")

    st.metric(
        "Total Replacements",
        sum(v["count"] for v in used_abbr.values())
    )

    # Compression Graph
    st.subheader("📉 Compression Effectiveness")
    fig, ax = plt.subplots(figsize=(5, 3))
    ax.bar(
        ["Original", "Minimized"],
        [original_size/1024, minimized_size/1024]
    )
    ax.set_ylabel("File Size (KB)")
    st.pyplot(fig)

    # Top Abbreviations
    if used_abbr:
        st.subheader("🔢 Top Abbreviations Used")
        sorted_abbr = sorted(
            used_abbr.items(),
            key=lambda x: x[1]["count"],
            reverse=True
        )[:10]

        labels = [k for k, _ in sorted_abbr]
        counts = [v["count"] for _, v in sorted_abbr]

        fig2, ax2 = plt.subplots(figsize=(6, 4))
        ax2.barh(labels, counts)
        ax2.set_xlabel("Replacement Count")
        ax2.invert_yaxis()
        st.pyplot(fig2)

    # Reading Time
    st.subheader("⏱️ Reading Time Estimation")
    words_original = sum(len(p.split()) for p in original_text_pages)
    words_minimized = sum(len(p.split()) for p in replaced_pages)

    r1, r2, r3 = st.columns(3)
    r1.metric("Original Time (min)", f"{words_original/200:.2f}")
    r2.metric("Minimized Time (min)", f"{words_minimized/200:.2f}")
    r3.metric(
        "Time Saved (min)",
        f"{(words_original - words_minimized)/200:.2f}"
    )

    st.markdown("---")

    # Abbreviation Table
    st.subheader("🔤 Replaced Abbreviations")

    if used_abbr:
        table_data = [
            {
                "Full Form": full,
                "Abbreviation": data["abbr"],
                "Replacement Count": data["count"]
            }
            for full, data in used_abbr.items()
        ]
        st.table(table_data)
    else:
        st.info("No abbreviations were used in this document.")

    # Download
    with open(output_path, "rb") as f:
        st.download_button(
            "📥 Download Minimized PDF",
            f,
            file_name="minimized_output.pdf",
            mime="application/pdf"
        )
