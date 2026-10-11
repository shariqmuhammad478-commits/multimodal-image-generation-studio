"""
API Client - Stability AI + OpenAI support
"""

import time
import random
import base64
import requests
from typing import Optional, Dict, Any, Tuple
from openai import OpenAI

import config


class ImageGenerationError(Exception):
    pass


class SafetyRejectionError(ImageGenerationError):
    pass


class NetworkFailureError(ImageGenerationError):
    pass


class InferenceFailureError(ImageGenerationError):
    pass


def exponential_backoff_with_jitter(attempt: int) -> float:
    delay = min(config.BASE_DELAY * (2 ** attempt), config.MAX_DELAY)
    jitter = random.uniform(0, delay * 0.25)
    return delay + jitter


class StabilityImageClient:
    """
    Stability AI - Stable Image Core
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or config.STABILITY_API_KEY
        if not self.api_key:
            raise ValueError("STABILITY_API_KEY not found. Please add it in the .env file.")
        self.base_url = "https://api.stability.ai/v2beta/stable-image/generate/core"

    def generate(
        self,
        prompt: str,
        aspect_ratio: str = "1:1 Square",
        n: int = 1,
        style_suffix: str = ""
    ) -> Tuple[bytes, Dict[str, Any]]:

        if len(prompt) > 10000:
            raise ValueError("Prompt is too long (max 10,000 characters).")

        full_prompt = (prompt + style_suffix).strip()

        ar_map = {
            "16:9 Landscape": "16:9",
            "1:1 Square": "1:1",
            "9:16 Vertical": "9:16"
        }
        ar_str = ar_map.get(aspect_ratio, "1:1")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "image/*"
        }

        data = {
            "prompt": full_prompt,
            "output_format": "png",
            "aspect_ratio": ar_str,
        }

        last_exception = None

        for attempt in range(config.MAX_RETRIES + 1):
            try:
                response = requests.post(
                    self.base_url,
                    headers=headers,
                    files={"none": ""},
                    data=data,
                    timeout=config.REQUEST_TIMEOUT
                )

                if response.status_code in config.RETRYABLE_STATUS_CODES:
                    if attempt < config.MAX_RETRIES:
                        wait = exponential_backoff_with_jitter(attempt)
                        time.sleep(wait)
                        continue
                    raise ImageGenerationError(f"Server busy (HTTP {response.status_code}). Please try again later.")

                if response.status_code == 401:
                    raise ImageGenerationError("Invalid Stability API key. Please check your .env file.")

                if response.status_code == 402 or "insufficient" in response.text.lower() or "credit" in response.text.lower():
                    raise ImageGenerationError(
                        "No credits remaining on your Stability AI account. "
                        "Please add credits at https://platform.stability.ai/account/credits"
                    )

                if response.status_code == 400:
                    error_text = response.text.lower()
                    if any(x in error_text for x in ["content", "moderation", "safety", "policy", "nsfw"]):
                        raise SafetyRejectionError(
                            "Your prompt was blocked by the safety filter. Please try a different description."
                        )
                    raise ImageGenerationError(f"Bad request: {response.text[:300]}")

                if response.status_code != 200:
                    raise ImageGenerationError(f"API error {response.status_code}: {response.text[:300]}")

                image_bytes = response.content

                if not image_bytes or len(image_bytes) < 1000:
                    raise ImageGenerationError("Received empty or invalid image data.")

                metadata = {
                    "engine": "stability-core",
                    "aspect_ratio": aspect_ratio,
                    "width": config.ASPECT_RATIOS.get(aspect_ratio, {}).get("width"),
                    "height": config.ASPECT_RATIOS.get(aspect_ratio, {}).get("height")
                }
                return image_bytes, metadata

            except requests.exceptions.ConnectTimeout as e:
                raise NetworkFailureError(
                    "Could not connect to the server. Please check your internet connection."
                ) from e

            except requests.exceptions.ReadTimeout as e:
                last_exception = e
                if attempt < config.MAX_RETRIES:
                    wait = exponential_backoff_with_jitter(attempt)
                    time.sleep(wait)
                    continue
                raise InferenceFailureError(
                    "The server took too long to respond. Please try again."
                ) from e

            except (SafetyRejectionError, NetworkFailureError, InferenceFailureError, ImageGenerationError):
                raise

            except Exception as e:
                last_exception = e
                if attempt < config.MAX_RETRIES:
                    wait = exponential_backoff_with_jitter(attempt)
                    time.sleep(wait)
                else:
                    raise ImageGenerationError(f"Generation failed: {str(e)}") from e

        raise ImageGenerationError(f"Unexpected failure: {last_exception}")


class OpenAIImageClient:
    """
    OpenAI gpt-image series (secondary option)
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or config.OPENAI_API_KEY
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found. Please add it in the .env file.")
        self.client = OpenAI(api_key=self.api_key)

    def generate(
        self,
        prompt: str,
        aspect_ratio: str = "1:1 Square",
        n: int = 1,
        style_suffix: str = ""
    ) -> Tuple[bytes, Dict[str, Any]]:

        if len(prompt) > 4000:
            raise ValueError("Prompt is too long (max 4,000 characters).")

        full_prompt = (prompt + style_suffix).strip()
        size = config.OPENAI_SIZES.get(aspect_ratio, "1024x1024")

        last_exception = None
        for attempt in range(config.MAX_RETRIES + 1):
            try:
                response = self.client.images.generate(
                    model="gpt-image-2",
                    prompt=full_prompt,
                    size=size,
                    n=1
                )

                image_b64 = getattr(response.data[0], "b64_json", None)
                image_url = getattr(response.data[0], "url", None)

                if image_b64:
                    image_bytes = base64.b64decode(image_b64)
                    source = "b64_json"
                elif image_url:
                    img_response = requests.get(
                        image_url,
                        stream=True,
                        timeout=config.REQUEST_TIMEOUT
                    )
                    img_response.raise_for_status()
                    image_bytes = b"".join(
                        chunk for chunk in img_response.iter_content(chunk_size=config.CHUNK_SIZE) if chunk
                    )
                    source = "url_streamed"
                else:
                    raise SafetyRejectionError("Image was blocked by safety filters.")

                metadata = {
                    "engine": "openai-gpt-image",
                    "model": "gpt-image-2",
                    "size": size,
                    "aspect_ratio": aspect_ratio,
                    "source": source
                }
                return image_bytes, metadata

            except Exception as e:
                error_str = str(e).lower()
                if any(x in error_str for x in ["content_policy", "safety", "moderation", "rejected", "blocked"]):
                    raise SafetyRejectionError("Your prompt was blocked by the safety filter.") from e
                if "credit" in error_str or "quota" in error_str or "billing" in error_str:
                    raise ImageGenerationError(
                        "No credits remaining on your OpenAI account. Please add credits."
                    ) from e

                last_exception = e
                if attempt < config.MAX_RETRIES:
                    time.sleep(exponential_backoff_with_jitter(attempt))
                else:
                    raise ImageGenerationError(f"Generation failed: {e}") from e

        raise ImageGenerationError(f"Unexpected failure: {last_exception}")


def get_client(engine: str = None):
    engine = engine or config.DEFAULT_ENGINE
    if engine == "stability":
        return StabilityImageClient()
    elif engine == "openai":
        return OpenAIImageClient()
    else:
        raise ValueError(f"Unknown engine: {engine}")
