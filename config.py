"""
Multimodal Image Generation Studio - Configuration
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ======================
# API KEYS
# ======================
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
STABILITY_API_KEY = os.getenv("STABILITY_API_KEY", "")

# Default engine
DEFAULT_ENGINE = "stability"

# ======================
# ASPECT RATIOS → Exact resolutions
# ======================
ASPECT_RATIOS = {
    "16:9 Landscape": {
        "width": 1344,
        "height": 768,
        "pixel_volume": 1032192,
        "target": "Web banners, presentations"
    },
    "1:1 Square": {
        "width": 1024,
        "height": 1024,
        "pixel_volume": 1048576,
        "target": "Avatars, product grids"
    },
    "9:16 Vertical": {
        "width": 768,
        "height": 1344,
        "pixel_volume": 1032192,
        "target": "Mobile reels, wallpapers"
    }
}

# OpenAI size mapping (kept for compatibility)
OPENAI_SIZES = {
    "16:9 Landscape": "1792x1024",
    "1:1 Square": "1024x1024",
    "9:16 Vertical": "1024x1792"
}

# ======================
# NETWORK SETTINGS
# ======================
CONNECT_TIMEOUT = 3.05
READ_TIMEOUT = 90
REQUEST_TIMEOUT = (CONNECT_TIMEOUT, READ_TIMEOUT)

# ======================
# STREAMING
# ======================
CHUNK_SIZE = 65536

# ======================
# RETRY SETTINGS
# ======================
MAX_RETRIES = 3
BASE_DELAY = 2.0
MAX_DELAY = 25.0
RETRYABLE_STATUS_CODES = {429, 503, 502, 504}

# ======================
# STYLE PRESETS
# ======================
STYLE_PRESETS = {
    "None (Default)": "",
    "Cyberpunk": ", cyberpunk style, neon lights, futuristic city, highly detailed",
    "Minimalism": ", minimalist style, clean lines, simple composition, elegant",
    "Photorealistic": ", photorealistic, ultra detailed, 8k resolution, sharp focus",
    "Oil Painting": ", oil painting style, classical art, rich textures, brush strokes",
    "Anime": ", anime style, vibrant colors, detailed illustration",
    "Watercolor": ", watercolor painting, soft edges, artistic, delicate"
}

# ======================
# PATHS
# ======================
OUTPUT_DIR = "generated_images"
os.makedirs(OUTPUT_DIR, exist_ok=True)
