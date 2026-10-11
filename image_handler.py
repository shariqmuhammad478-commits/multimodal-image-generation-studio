"""
Image Handler Module
Implements:
- Memory-Safe Streaming for Binary Payloads (Slide 13)
- Threat of Truncated Data Stream (Slide 14)
- Forcing Rigorous Pixel-Level Decode (Slide 15)
"""

import os
import io
from datetime import datetime
from typing import Tuple, Optional
from PIL import Image
import config


class ImageIntegrityError(Exception):
    """Raised when image is truncated or corrupted"""
    pass


def save_image_bytes(
    image_bytes: bytes,
    prompt: str,
    aspect_ratio: str,
    engine: str = "openai"
) -> str:
    """
    Save binary image data safely to local storage.
    Returns the full file path.
    """
    # Create safe filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_prompt = "".join(c if c.isalnum() or c in " _-" else "" for c in prompt[:40]).strip().replace(" ", "_")
    filename = f"{timestamp}_{engine}_{safe_prompt}.png"
    filepath = os.path.join(config.OUTPUT_DIR, filename)

    # Write bytes directly (already in memory from API)
    with open(filepath, "wb") as f:
        f.write(image_bytes)

    return filepath


def download_and_stream_to_file(
    url: str,
    filepath: str,
    timeout: tuple = config.REQUEST_TIMEOUT
) -> str:
    """
    Memory-Safe Streaming (Slide 13)
    Rule 1: Never load high-res image entirely into RAM with basic requests.get()
    Rule 2: Enable chunking → stream=True
    Rule 3: Write sequentially using iter_content(chunk_size=65536)
    """
    import requests

    try:
        with requests.get(url, stream=True, timeout=timeout) as response:
            response.raise_for_status()
            with open(filepath, "wb") as f:
                for chunk in response.iter_content(chunk_size=config.CHUNK_SIZE):
                    if chunk:  # filter out keep-alive chunks
                        f.write(chunk)
        return filepath
    except requests.exceptions.ConnectTimeout as e:
        raise ConnectionError(
            "ConnectTimeout while streaming image. FAIL FAST as per Slide 10."
        ) from e
    except requests.exceptions.ReadTimeout as e:
        raise TimeoutError(
            "ReadTimeout while streaming image. Server slow or large payload."
        ) from e


def verify_image_integrity(filepath: str) -> bool:
    """
    Forcing a Rigorous Pixel-Level Decode (Slide 15)

    Implementation:
    Image.open().load() wrapped in try...except

    Mechanism:
    Calling .load() forces Pillow to fully decode the entire image stream,
    pixel by pixel, rather than just reading headers.

    Outcome:
    If file cut off prematurely → OSError: broken data stream
    → discard corrupted asset and request retry.

    Why not imghdr.what() or Image.verify()?
    (Slide 14) They only read block structure + CRC headers at the beginning.
    They report success even on truncated files → silent disaster.
    """
    try:
        with Image.open(filepath) as img:
            img.load()  # ← CRITICAL: full pixel decode
        return True
    except OSError as e:
        # broken data stream / truncated
        if os.path.exists(filepath):
            os.remove(filepath)  # discard corrupted asset
        raise ImageIntegrityError(
            f"Truncated or corrupted image detected (OSError: {e}). "
            "File discarded. Pipeline should automatically request a retry."
        ) from e
    except Exception as e:
        if os.path.exists(filepath):
            os.remove(filepath)
        raise ImageIntegrityError(f"Image integrity check failed: {e}") from e


def process_and_save(
    image_bytes: bytes,
    prompt: str,
    aspect_ratio: str,
    engine: str = "openai"
) -> Tuple[str, Image.Image]:
    """
    Full pipeline:
    1. Save bytes to disk
    2. Force pixel-level integrity verification
    3. Return filepath + opened PIL Image (for display)
    """
    filepath = save_image_bytes(image_bytes, prompt, aspect_ratio, engine)

    # Integrity check — Slide 15
    verify_image_integrity(filepath)

    # Open for display (after successful verification)
    img = Image.open(filepath)
    return filepath, img
