# Multimodal Image Generation Studio

A production-ready text-to-image generation application built with Streamlit and Stability AI.

This project demonstrates a complete visual generation pipeline — from natural language prompt handling to high-quality image output with proper error handling, timeouts, streaming, and integrity checks.

## Features

- Text-to-image generation using Stability AI
- Multiple aspect ratios (1:1, 16:9, 9:16)
- Style presets for different creative directions
- Dual-timeout network handling (connection + read)
- Memory-safe image streaming (65KB chunks)
- Pixel-level image integrity verification
- Clean and responsive Streamlit interface
- Automatic local saving of generated images

## Tech Stack

- Python 3.10+
- Streamlit
- Requests
- Pillow (PIL)
- python-dotenv
- Stability AI REST API

## Setup Instructions

1. Clone or extract the project folder
2. Create and activate a virtual environment:

```bash
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Mac/Linux
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Create a `.env` file and add your Stability AI API key:

```
STABILITY_API_KEY=your_key_here
```

5. Run the application:

```bash
streamlit run app.py
```

## How to Use

1. Enter a detailed text prompt
2. Select aspect ratio and optional style preset
3. Click **Generate Artwork**
4. View, download, or find the image in the `generated_images` folder

## Project Structure

```
├── app.py                 # Main Streamlit application
├── api_client.py          # API calls, timeouts, retries & safety handling
├── image_handler.py       # Streaming download + integrity verification
├── config.py              # Aspect ratios, timeouts, style presets
├── requirements.txt
├── .env.example
└── generated_images/      # Output folder for generated artworks
```

## Notes

- Make sure you have sufficient credits in your Stability AI account.
- Generated images are saved locally with timestamps for easy organization.
- The application handles network timeouts, content moderation, and corrupted downloads gracefully.

---

**Developed as part of Generative AI Industrial Training**  
Batch 2026 | DecodeLabs
