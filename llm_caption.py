import os
import re
from typing import List

import requests


def _variation_instruction(index: int) -> str:
    variation_bank = [
        "Straight, minimal, and intimate.",
        "Cinematic and observant.",
        "Quietly reflective, like a thought you keep to yourself.",
        "Playful and lightly witty, but still natural.",
        "Poetic and restrained, with a soft finish.",
    ]
    return variation_bank[index % len(variation_bank)]


def _caption_profile(index: int) -> dict[str, str]:
    profiles = [
        {
            "name": "minimal",
            "shape": "one short sentence, no hook",
            "emoji": "0-1 emoji",
            "hashtags": "2-3 hashtags",
            "avoid": "avoid poetic wording and avoid metaphors",
        },
        {
            "name": "cinematic",
            "shape": "one short cinematic line",
            "emoji": "0-1 emoji",
            "hashtags": "2-3 hashtags",
            "avoid": "avoid sounding dreamy or overdescribed",
        },
        {
            "name": "reflective",
            "shape": "one thoughtful line",
            "emoji": "0-1 emoji",
            "hashtags": "2 hashtags max",
            "avoid": "avoid generic vibe words",
        },
        {
            "name": "playful",
            "shape": "one relaxed line with a tiny bit of attitude",
            "emoji": "1 emoji max",
            "hashtags": "2-3 hashtags",
            "avoid": "avoid being too silly or meme-heavy",
        },
        {
            "name": "poetic",
            "shape": "one soft line with a quiet ending",
            "emoji": "0-1 emoji",
            "hashtags": "2 hashtags max",
            "avoid": "avoid long emotional sentences",
        },
    ]

    return profiles[index % len(profiles)]


def _clean_caption(text: str) -> str:
    cleaned = str(text).strip()
    cleaned = cleaned.strip('"').strip("'")
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    cleaned = re.sub(r"[ \t]+", " ", cleaned)
    return cleaned.strip()


def build_prompt(base_caption: str, tone: str, content_type: str, variation_instruction: str) -> str:
    tone_map = {
        "Aesthetic": "soft, minimal, calm",
        "Romantic": "emotional, love-filled, warm",
        "Savage": "bold, confident, attitude",
        "Deep": "thoughtful, introspective",
        "Funny": "witty, sarcastic, playful",
    }

    vibe_hint_map = {
        "Aesthetic": "clean visuals, subtle mood, quiet confidence",
        "Romantic": "warmth, closeness, longing, affection",
        "Savage": "main-character energy, confidence, unbothered",
        "Deep": "reflection, growth, inner peace, life moments",
        "Funny": "casual chaos, sarcasm, meme-like humor",
    }

    style = tone_map.get(tone, "natural")
    vibe_hint = vibe_hint_map.get(tone, "natural vibe")

    prompt = f"""
You are a real Instagram user writing one high-quality caption, not an AI assistant.

Scene summary: {base_caption}
Mood: {tone}
Style: {style}
Vibe hint: {vibe_hint}
Content type: {content_type}
Variation target: {variation_instruction}

Quality rules:
- sound emotionally real, specific, and human
- keep it SHORT and intentional
- avoid generic fillers like "just soaking in the moment", "quiet vibes", "golden hour vibes"
- do not describe clothing; focus on feeling, setting, memory, confidence, or atmosphere
- subtly infer context if possible (travel, architecture, culture, nostalgia, freedom)
- avoid repeating wording used in common influencer templates
- prefer plain words over over-written poetic language
- make this one clearly different from the other captions you might write for the same image

Formatting:
- 1 short line preferred; 2 lines max only if necessary
- 0-2 natural emojis max
- 2-4 relevant hashtags in the last line
- total caption should feel compact, not lengthy
- no labels, no quotes, no extra explanation

Platform behavior:
- Post: calmer reflective tone

Return only the final caption text.
"""

    return prompt


def generate_instagram_captions(
    base_caption: str,
    tone: str,
    content_type: str,
    api_key: str,
    n: int = 5,
) -> List[str]:
    base_url = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1").rstrip("/")
    endpoint = f"{base_url}/chat/completions"

    models_env = os.getenv(
        "OPENROUTER_MODELS",
        "openrouter/auto,meta-llama/llama-3.1-8b-instruct:free,microsoft/phi-3-mini-128k-instruct:free",
    )
    model_candidates = [m.strip() for m in models_env.split(",") if m.strip()]

    if not model_candidates:
        model_candidates = ["openrouter/auto"]

    captions: List[str] = []
    seen: set[str] = set()
    attempts = 0
    max_attempts = max(n * 4, 8)

    max_tokens = int(os.getenv("OPENROUTER_MAX_TOKENS", "90"))
    temperature = float(os.getenv("OPENROUTER_TEMPERATURE", "0.86"))
    top_p = float(os.getenv("OPENROUTER_TOP_P", "0.92"))

    while len(captions) < n and attempts < max_attempts:
        variation_instruction = _variation_instruction(attempts)
        profile = _caption_profile(attempts)
        prompt = build_prompt(base_caption, tone, content_type, variation_instruction)
        prompt += f"\n\nCaption profile: {profile['name']}\n"
        prompt += f"Structure: {profile['shape']}\n"
        prompt += f"Emoji budget: {profile['emoji']}\n"
        prompt += f"Hashtag budget: {profile['hashtags']}\n"
        prompt += f"Avoid: {profile['avoid']}\n"
        attempts += 1

        last_error = None
        for model_name in model_candidates:
            response = requests.post(
                endpoint,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": os.getenv("APP_URL", "http://localhost:8501"),
                    "X-OpenRouter-Title": os.getenv("APP_NAME", "Instagram Caption Generator"),
                },
                json={
                    "model": model_name,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": temperature,
                    "top_p": top_p,
                    "max_tokens": max_tokens,
                    "presence_penalty": 0.35,
                    "frequency_penalty": 0.2,
                },
                timeout=60,
            )

            if response.ok:
                payload = response.json()
                content = payload["choices"][0]["message"].get("content", "")
                cleaned = _clean_caption(content)
                normalized = cleaned.lower()
                if cleaned and normalized not in seen:
                    captions.append(cleaned)
                    seen.add(normalized)
                last_error = None
                break

            try:
                error_payload = response.json()
                error_message = error_payload.get("error", {}).get("message") or error_payload
            except ValueError:
                error_message = response.text

            # 404 is commonly returned when a specific model route is unavailable.
            if response.status_code == 404:
                last_error = (
                    f"Model '{model_name}' unavailable (404) at {endpoint}. "
                    f"Trying fallback model. Details: {error_message}"
                )
                continue

            raise RuntimeError(
                f"OpenRouter request failed ({response.status_code}) for model '{model_name}': "
                f"{error_message}"
            )

        if last_error is not None:
            raise RuntimeError(last_error)

    if not captions:
        raise RuntimeError("No captions were generated. Try another model fallback chain.")

    return captions
