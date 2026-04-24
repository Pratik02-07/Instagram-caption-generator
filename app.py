import os
import json
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

from blip_model import generate_blip_caption
from llm_caption import generate_instagram_captions


def load_env_file(env_path: str = ".env") -> None:
    path = Path(env_path)
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'").strip()

        if key and key not in os.environ:
            os.environ[key] = value


st.set_page_config(page_title="Instagram Caption Generator", page_icon="📸")

st.title("Instagram Caption Generation")
st.write(
    "Upload an image to generate a base scene caption with BLIP, then create "
    "Instagram captions."
)

def resolve_openrouter_api_key() -> str:
    load_env_file()

    api_key = os.getenv("OPENROUTER_API_KEY", "")
    if api_key:
        return api_key

    # Access Streamlit secrets safely: this can raise when secrets.toml is absent.
    try:
        return st.secrets["OPENROUTER_API_KEY"]
    except Exception:
        return ""


api_key = resolve_openrouter_api_key()

left_col, right_col = st.columns(2, gap="large")

with left_col:
    tone = st.selectbox(
        "Choose caption type",
        ["Aesthetic", "Romantic", "Savage", "Deep", "Funny"],
    )

    content_type = st.selectbox(
        "Content type",
        ["Instagram Post"],
    )

    uploaded_file = st.file_uploader("Upload image", type=["jpg", "jpeg", "png"])

    if uploaded_file:
        temp_path = Path("temp.jpg")
        temp_path.write_bytes(uploaded_file.read())

        st.image(str(temp_path), caption="Uploaded Image", width="stretch")

        with st.spinner("Generating base caption with BLIP..."):
            try:
                base_caption = generate_blip_caption(str(temp_path))
            except Exception as exc:
                st.error(f"BLIP caption generation failed: {exc}")
                st.stop()

        st.subheader("Base Caption (BLIP)")
        st.write(base_caption)

        state_signature = f"{uploaded_file.name}:{tone}:{content_type}:{base_caption}"
        if st.session_state.get("caption_state_signature") != state_signature:
            st.session_state["caption_state_signature"] = state_signature
            st.session_state["generated_captions"] = []
            st.session_state["selected_caption"] = ""
            st.session_state["copy_requested_caption"] = ""

        if not api_key:
            st.warning(
                "OpenRouter API key missing. Add OPENROUTER_API_KEY to `.env`, set it in your "
                "shell environment, or use `.streamlit/secrets.toml`."
            )
            st.stop()

with right_col:
    st.subheader("Choose your best caption")
    if uploaded_file and st.button("Generate 5 Instagram Captions", use_container_width=True):
        with st.spinner("Generating captions..."):
            try:
                captions = generate_instagram_captions(
                    base_caption=base_caption,
                    tone=tone,
                    content_type=content_type,
                    api_key=api_key,
                    n=5,
                )
                st.session_state["generated_captions"] = captions
                if captions:
                    st.session_state["selected_caption"] = captions[0]
            except Exception as exc:
                st.error(f"OpenRouter caption generation failed: {exc}")
                st.stop()

    captions = st.session_state.get("generated_captions", [])
    if captions:
        for idx, caption in enumerate(captions, start=1):
            with st.container(border=True):
                st.markdown(f"**Caption {idx}**")
                st.write(caption)
                if st.button(f"Copy Caption {idx}", key=f"select_caption_{idx}"):
                    st.session_state["selected_caption"] = caption
                    st.session_state["copy_requested_caption"] = caption

        copy_requested_caption = st.session_state.get("copy_requested_caption", "")
        if copy_requested_caption:
            components.html(
                f"""
                <script>
                const caption = {json.dumps(copy_requested_caption)};
                navigator.clipboard.writeText(caption).catch(() => {{}});
                </script>
                """,
                height=0,
            )
            st.success("Caption copied to clipboard.")
            st.session_state["copy_requested_caption"] = ""
    else:
        st.info("Upload an image and generate 5 captions.")
