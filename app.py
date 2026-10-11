"""
Multimodal Image Generation Studio
DecodeLabs Industrial Training Kit – Batch 2026
"""

import streamlit as st
import os

import config
from api_client import (
    get_client,
    SafetyRejectionError,
    NetworkFailureError,
    InferenceFailureError,
    ImageGenerationError,
)
from image_handler import process_and_save, ImageIntegrityError


st.set_page_config(
    page_title="Multimodal Image Generation Studio | DecodeLabs",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
<style>
    .main-header {
        font-size: 2.3rem;
        font-weight: 700;
        color: #1a5f4a;
        margin-bottom: 0.15rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #555;
        margin-bottom: 1.4rem;
    }
    .info-box {
        padding: 0.85rem 1.1rem;
        border-radius: 0.5rem;
        background-color: #eef6fb;
        border-left: 5px solid #2980b9;
        font-size: 0.92rem;
        margin-bottom: 1rem;
    }
    .error-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #fdecea;
        border-left: 5px solid #c0392b;
    }
</style>
""",
    unsafe_allow_html=True,
)


def main():
    st.markdown(
        '<p class="main-header">🎨 Multimodal Image Generation Studio</p>',
        unsafe_allow_html=True,
    )
    # st.markdown(
    #     '<p class="sub-header">Project 3 · DecodeLabs Industrial Training Kit · Batch 2026</p>',
    #     unsafe_allow_html=True,
    # )

    st.markdown(
        """
    <div class="info-box">
    This studio converts natural language descriptions into high-quality digital artwork.
    It handles exact resolution mapping, secure API calls, binary streaming, and image integrity checks.
    </div>
    """,
        unsafe_allow_html=True,
    )

    st.markdown("---")

    # Sidebar
    with st.sidebar:
        st.header("⚙️ Configuration")

        engine = st.selectbox(
            "Image Generation Engine",
            options=["stability", "openai"],
            index=0,
            help="stability = Stable Image Core\nopenai = gpt-image series",
        )

        aspect_ratio = st.selectbox(
            "Aspect Ratio",
            options=list(config.ASPECT_RATIOS.keys()),
            index=1,
        )

        ratio_info = config.ASPECT_RATIOS[aspect_ratio]
        st.caption(f"Resolution: {ratio_info['width']} × {ratio_info['height']}")
        st.caption(f"Target use: {ratio_info['target']}")

        style = st.selectbox(
            "Style Preset",
            options=list(config.STYLE_PRESETS.keys()),
            index=0,
        )

        st.markdown("---")
        st.subheader("API Keys")
        st.write(f"Stability: {'✅ Loaded' if config.STABILITY_API_KEY else '❌ Missing'}")
        st.write(f"OpenAI: {'✅ Loaded' if config.OPENAI_API_KEY else '❌ Missing'}")

        if not config.STABILITY_API_KEY and not config.OPENAI_API_KEY:
            st.error("Please add at least one API key in the .env file.")

    # Main area
    col1, col2 = st.columns([1.3, 1])

    with col1:
        st.subheader("📝 Prompt")
        prompt = st.text_area(
            "Describe the image you want to create",
            height=140,
            placeholder="A serene Japanese garden at dusk with cherry blossoms falling, soft golden light, ultra detailed...",
        )

        char_limit = 10000 if engine == "stability" else 4000
        st.caption(f"Characters: {len(prompt)} / {char_limit}")

        generate_btn = st.button(
            "🚀 Generate Artwork", type="primary", use_container_width=True
        )

    with col2:
        st.subheader("📊 Status")
        status_placeholder = st.empty()
        status_placeholder.info("Ready. Enter a prompt and click Generate.")

    if generate_btn:
        if not prompt.strip():
            st.warning("Please enter a prompt first.")
            return

        if engine == "stability" and not config.STABILITY_API_KEY:
            st.error("Stability API key is missing. Add it to the .env file.")
            return
        if engine == "openai" and not config.OPENAI_API_KEY:
            st.error("OpenAI API key is missing. Add it to the .env file.")
            return

        style_suffix = config.STYLE_PRESETS.get(style, "")

        try:
            status_placeholder.info("Preparing request...")
            client = get_client(engine)

            status_placeholder.info("Generating image... (this may take 10–40 seconds)")
            image_bytes, metadata = client.generate(
                prompt=prompt,
                aspect_ratio=aspect_ratio,
                style_suffix=style_suffix,
            )

            status_placeholder.info("Saving and verifying image...")
            filepath, img = process_and_save(
                image_bytes=image_bytes,
                prompt=prompt,
                aspect_ratio=aspect_ratio,
                engine=engine,
            )

            status_placeholder.success("✅ Image generated successfully!")

            st.markdown("---")
            st.subheader("Generated Artwork")
            st.image(
                img,
                caption=f"{aspect_ratio} · {metadata.get('engine', engine)}",
                use_container_width=True,
            )

            col_a, col_b = st.columns(2)
            with col_a:
                st.write("**Details**")
                st.json(metadata)
            with col_b:
                with open(filepath, "rb") as f:
                    st.download_button(
                        label="⬇️ Download PNG",
                        data=f,
                        file_name=os.path.basename(filepath),
                        mime="image/png",
                    )
                st.success(f"Saved to: `{filepath}`")

        except SafetyRejectionError as e:
            status_placeholder.error("Safety filter triggered")
            st.markdown(
                f'<div class="error-box"><b>Content blocked</b><br>{str(e)}</div>',
                unsafe_allow_html=True,
            )

        except NetworkFailureError as e:
            status_placeholder.error("Connection problem")
            st.markdown(
                f'<div class="error-box"><b>Network error</b><br>{str(e)}</div>',
                unsafe_allow_html=True,
            )

        except InferenceFailureError as e:
            status_placeholder.error("Timeout")
            st.markdown(
                f'<div class="error-box"><b>Server timeout</b><br>{str(e)}</div>',
                unsafe_allow_html=True,
            )

        except ImageIntegrityError as e:
            status_placeholder.error("Image integrity check failed")
            st.markdown(
                f'<div class="error-box"><b>Corrupted image</b><br>{str(e)}</div>',
                unsafe_allow_html=True,
            )

        except ImageGenerationError as e:
            status_placeholder.error("Generation failed")
            st.markdown(
                f'<div class="error-box"><b>Error</b><br>{str(e)}</div>',
                unsafe_allow_html=True,
            )

        except Exception as e:
            status_placeholder.error("Unexpected error")
            st.exception(e)

    st.markdown("---")
    st.caption("DecodeLabs · Batch 2026")


if __name__ == "__main__":
    main()
