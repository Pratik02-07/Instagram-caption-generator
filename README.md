# Image Caption Generator

Generate short, intentional Instagram captions from any image using BLIP for visual understanding and OpenRouter for caption generation.

[![Python](https://img.shields.io/badge/-Python-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/-Streamlit-FF4B4B)](https://streamlit.io/)
[![Hugging Face](https://img.shields.io/badge/-Transformers-FFD21E?logo=huggingface&logoColor=black)](https://huggingface.co/transformers/)

## Overview

This project turns a single uploaded image into 5 caption options.

Pipeline:

1. BLIP creates a base scene caption from the image.
2. A prompt engine adds tone, style, and content type.
3. OpenRouter generates 5 caption variations.
4. You pick the best caption in the Streamlit UI.

The app is designed for Instagram-style captions that feel human, compact, and context-aware.

## Features

- Image understanding with `Salesforce/blip-image-captioning-base`
- Caption type options: Aesthetic, Romantic, Savage, Deep, Funny
- Content type options: Instagram Post
- 5 generated caption choices per image
- Caption selection that stays visible in the UI
- Environment-variable or `.env` based API key loading
- Free-model fallback support for OpenRouter

## Demo

If you have a deployed version of the app, place the link here.

Example UI preview:

![Caption Generator Demo](resource/demo.gif)

## Caption Generation Flow

```mermaid
sequenceDiagram
    participant User
    participant Streamlit
    participant BLIP
    participant OpenRouter

    User->>Streamlit: Upload image and select settings
    Streamlit->>BLIP: Generate base caption
    BLIP-->>Streamlit: Base caption text
    Streamlit->>OpenRouter: Send prompt with mood + base caption
    OpenRouter-->>Streamlit: Caption option 1
    Streamlit->>OpenRouter: Send next variation prompt
    OpenRouter-->>Streamlit: Caption option 2
    Streamlit->>OpenRouter: Repeat until 5 captions
    Streamlit-->>User: Show caption list and selected caption box
```

---

## How It Works

1. Upload an image.
2. BLIP generates a base caption.
3. The app combines that caption with the chosen mood and platform.
4. OpenRouter returns 5 short caption options.
5. You select the best one and it is shown in the caption box.

## Project Structure

```text
app.py              # Streamlit UI and session-state handling
blip_model.py       # BLIP caption generation
llm_caption.py      # Prompt engine and OpenRouter integration
requirements.txt    # Python dependencies
resource/demo.gif   # Demo preview
```
