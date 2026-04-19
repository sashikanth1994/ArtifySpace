import streamlit as st
from PIL import Image
from io import BytesIO
import os
from dotenv import load_dotenv

load_dotenv()

from concepts import generate_concepts
from generator import generate_all_concepts

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ArtSpace — AI Art Concept Generator",
    page_icon="🎨",
    layout="wide",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Sans:wght@300;400;500&display=swap');

  html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    background-color: #0f0f0f;
    color: #f0ece4;
  }

  h1, h2, h3 { font-family: 'DM Serif Display', serif; }

  .hero {
    text-align: center;
    padding: 3rem 0 1.5rem 0;
  }
  .hero h1 {
    font-size: 3.2rem;
    letter-spacing: -0.02em;
    color: #f0ece4;
    margin-bottom: 0.3rem;
  }
  .hero p {
    color: #888;
    font-size: 1.05rem;
    font-weight: 300;
  }

  .concept-card {
    background: #1a1a1a;
    border: 1px solid #2a2a2a;
    border-radius: 12px;
    padding: 1.2rem;
    margin-top: 0.5rem;
    height: 100%;
  }
  .concept-title {
    font-family: 'DM Serif Display', serif;
    font-size: 1.25rem;
    color: #e8c97e;
    margin-bottom: 0.4rem;
  }
  .concept-desc {
    font-size: 0.88rem;
    color: #b0a898;
    line-height: 1.6;
    margin-bottom: 0.6rem;
  }
  .concept-placement {
    font-size: 0.78rem;
    color: #666;
    font-style: italic;
  }
  .placement-label {
    color: #555;
    font-weight: 500;
    font-style: normal;
  }

  div[data-testid="stButton"] button {
    background: #e8c97e;
    color: #0f0f0f;
    border: none;
    border-radius: 8px;
    font-family: 'DM Sans', sans-serif;
    font-weight: 500;
    font-size: 1rem;
    padding: 0.6rem 2rem;
    width: 100%;
    cursor: pointer;
    transition: background 0.2s;
  }
  div[data-testid="stButton"] button:hover {
    background: #f5d98a;
  }

  div[data-testid="stFileUploader"] {
    background: #1a1a1a;
    border: 1px dashed #333;
    border-radius: 12px;
    padding: 1rem;
  }

  .stTextArea textarea {
    background: #1a1a1a !important;
    border: 1px solid #2a2a2a !important;
    border-radius: 8px !important;
    color: #f0ece4 !important;
    font-family: 'DM Sans', sans-serif !important;
  }

  .original-label {
    font-size: 0.78rem;
    color: #555;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-bottom: 0.4rem;
  }

  .divider {
    border: none;
    border-top: 1px solid #222;
    margin: 2rem 0;
  }
</style>
""", unsafe_allow_html=True)

# ── Hero ──────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
  <h1>🎨 ArtSpace</h1>
  <p>Upload a photo of any space. Get 3 AI-generated art concepts tailored to it.</p>
</div>
""", unsafe_allow_html=True)

st.markdown("<hr class='divider'>", unsafe_allow_html=True)

# ── Input Section ─────────────────────────────────────────────────────────────
col_left, col_right = st.columns([1, 1], gap="large")

with col_left:
    st.markdown("##### Upload your space")
    uploaded_file = st.file_uploader(
        "Drop a photo of a restaurant, office, gym, park, etc.",
        type=["jpg", "jpeg", "png", "webp"],
        label_visibility="collapsed",
    )
    if uploaded_file:
        st.image(uploaded_file, use_container_width=True)

with col_right:
    st.markdown("##### Describe the vibe *(optional)*")
    user_prompt = st.text_area(
        "Theme, mood, or purpose",
        placeholder="e.g. 'warm and inviting for a cozy coffee shop' or 'bold and energetic for a gym'",
        height=120,
        label_visibility="collapsed",
    )
    st.markdown("<br>", unsafe_allow_html=True)
    generate_btn = st.button("✦ Generate 3 Art Concepts", use_container_width=True)

st.markdown("<hr class='divider'>", unsafe_allow_html=True)

# ── Generation Logic ──────────────────────────────────────────────────────────
if generate_btn:
    if not uploaded_file:
        st.warning("Please upload a photo of a space first.")
    else:
        # Check API keys
        if not os.getenv("ANTHROPIC_API_KEY"):
            st.error("Missing ANTHROPIC_API_KEY in your .env file.")
            st.stop()
        if not os.getenv("REPLICATE_API_TOKEN"):
            st.error("Missing REPLICATE_API_TOKEN in your .env file.")
            st.stop()

        image_bytes = uploaded_file.read()
        media_type = f"image/{uploaded_file.type.split('/')[-1]}"
        if media_type == "image/jpg":
            media_type = "image/jpeg"

        # Step 1: Generate concepts via Claude
        with st.spinner("Analyzing your space with Claude..."):
            try:
                concepts = generate_concepts(image_bytes, media_type, user_prompt)
            except Exception as e:
                st.error(f"Claude error: {e}")
                st.stop()

        # Step 2: Generate images via Replicate
        images = []
        progress = st.progress(0, text="Generating concept images...")
        for i, concept in enumerate(concepts):
            try:
                from generator import generate_concept_image
                img = generate_concept_image(concept["image_prompt"])
                images.append(img)
                progress.progress((i + 1) / len(concepts), text=f"Generated concept {i+1} of {len(concepts)}...")
            except Exception as e:
                st.warning(f"Image generation failed for concept {i+1}: {e}")
                images.append(None)

        progress.empty()

        # ── Results ───────────────────────────────────────────────────────────
        st.markdown("### ✦ Your Art Concepts")
        st.markdown("<br>", unsafe_allow_html=True)

        result_cols = st.columns(3, gap="medium")

        for i, (concept, img) in enumerate(zip(concepts, images)):
            with result_cols[i]:
                if img:
                    buf = BytesIO()
                    img.save(buf, format="WEBP")
                    st.image(buf.getvalue(), use_container_width=True)
                else:
                    st.markdown("*Image generation failed*")

                st.markdown(f"""
                <div class="concept-card">
                  <div class="concept-title">{concept.get('title', 'Untitled')}</div>
                  <div class="concept-desc">{concept.get('description', '')}</div>
                  <div class="concept-placement">
                    <span class="placement-label">Placement:</span> {concept.get('placement', '')}
                  </div>
                </div>
                """, unsafe_allow_html=True)

        # Download section
        st.markdown("<hr class='divider'>", unsafe_allow_html=True)
        st.markdown("##### Save your concepts")
        dl_cols = st.columns(3, gap="medium")
        for i, (concept, img) in enumerate(zip(concepts, images)):
            if img:
                with dl_cols[i]:
                    buf = BytesIO()
                    img.save(buf, format="PNG")
                    st.download_button(
                        label=f"↓ Download Concept {i+1}",
                        data=buf.getvalue(),
                        file_name=f"concept_{i+1}_{concept['title'].replace(' ', '_').lower()}.png",
                        mime="image/png",
                        use_container_width=True,
                    )

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown(
    "<p style='text-align:center; color:#333; font-size:0.8rem;'>Built with Claude + FLUX · ArtSpace MVP</p>",
    unsafe_allow_html=True
)