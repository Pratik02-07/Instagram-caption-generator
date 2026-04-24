import warnings

from PIL import Image
import torch
from transformers import BlipForConditionalGeneration, BlipProcessor
from transformers.utils import logging as hf_logging


# Keep runtime output clean in Streamlit by silencing verbose transformer internals.
warnings.filterwarnings("ignore", message=r"Accessing `__path__`.*")
hf_logging.set_verbosity_error()


processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")

device = "cuda" if torch.cuda.is_available() else "cpu"
model.to(device)


def generate_blip_caption(image_path: str) -> str:
    image = Image.open(image_path).convert("RGB")
    inputs = processor(image, return_tensors="pt").to(device)

    output = model.generate(**inputs, max_length=50)
    caption = processor.decode(output[0], skip_special_tokens=True)

    return caption
