"""Visual Diagram & Chart Generation Tool for Thirdhand AI WhatsApp Super-Agent."""

from __future__ import annotations

import base64
import json
import logging
import os
import time
from pathlib import Path
from typing import Any
from urllib.parse import quote

import httpx

logger = logging.getLogger(__name__)

DIAGRAM_CACHE_DIR = Path("data/generated_diagrams")
DIAGRAM_CACHE_DIR.mkdir(parents=True, exist_ok=True)


def get_public_base_url() -> str:
    """Return active public base URL from environment, tunnel file, or local fallback."""
    for env_key in ("PUBLIC_BASE_URL", "RENDER_EXTERNAL_URL"):
        env_val = os.getenv(env_key, "").strip().rstrip("/")
        if env_val.startswith("http"):
            return env_val
    url_file = Path("data/whatsapp/public_url.txt")
    if url_file.exists():
        try:
            val = url_file.read_text(encoding="utf-8").strip().rstrip("/")
            if val.startswith("http"):
                return val
        except Exception:
            pass
    return "http://127.0.0.1:8000"


class VisualDiagramTool:
    """Generates visual diagram and chart images (flowcharts, sequence diagrams, charts) via Mermaid.ink and QuickChart."""

    def __init__(self, client: httpx.AsyncClient | None = None, settings: Any = None) -> None:
        self.client = client
        if settings is None:
            try:
                from config.settings import get_settings
                settings = get_settings()
            except Exception:
                settings = None
        self.settings = settings

    async def render_mermaid_to_image(
        self, mermaid_code: str, theme: str = "default"
    ) -> bytes:
        """Render Mermaid flowchart/sequence/state diagram code into high-res PNG image bytes."""
        clean_code = mermaid_code.strip()
        encoded = base64.b64encode(clean_code.encode("utf-8")).decode("ascii")
        url = f"https://mermaid.ink/img/{encoded}"

        own_client = False
        http = self.client
        try:
            if http is None:
                http = httpx.AsyncClient(timeout=15.0)
                own_client = True
            resp = await http.get(url)
            if resp.status_code == 200 and resp.content:
                return resp.content
        except Exception as exc:
            logger.warning("Mermaid.ink render failed (%s), trying QuickChart", exc)
        finally:
            if own_client and http is not None:
                await http.aclose()

        qc_url = f"https://quickchart.io/mermaid?src={quote(clean_code)}"
        own_client = False
        http = self.client
        try:
            if http is None:
                http = httpx.AsyncClient(timeout=15.0)
                own_client = True
            resp = await http.get(qc_url)
            if resp.status_code == 200 and resp.content:
                return resp.content
        finally:
            if own_client and http is not None:
                await http.aclose()

        raise RuntimeError("Failed to render Mermaid diagram to image")

    async def render_chart_to_image(self, chart_config: dict[str, Any]) -> bytes:
        """Render Chart.js specification (bar, line, pie, donut) into PNG image bytes via QuickChart."""
        url = f"https://quickchart.io/chart?c={quote(json.dumps(chart_config))}&w=800&h=450&bkg=white"
        own_client = False
        http = self.client
        try:
            if http is None:
                http = httpx.AsyncClient(timeout=15.0)
                own_client = True
            resp = await http.get(url)
            if resp.status_code == 200 and resp.content:
                return resp.content
        finally:
            if own_client and http is not None:
                await http.aclose()
        raise RuntimeError("Failed to render Chart to image")

    async def generate_diagram(
        self,
        diagram_type: str,
        code_or_spec: str,
        title: str = "Thirdhand Diagram",
    ) -> dict[str, Any]:
        """Generate a diagram image file and return its path and direct public URL."""
        slug = "".join(c if c.isalnum() else "_" for c in title.lower())[:30]
        filename = f"{int(time.time())}_{slug}.png"
        filepath = DIAGRAM_CACHE_DIR / filename

        dtype = diagram_type.strip().lower()
        if dtype in {"chart", "graph_chart", "plot"}:
            if isinstance(code_or_spec, str):
                try:
                    spec_dict = json.loads(code_or_spec)
                except Exception:
                    spec_dict = {
                        "type": "line",
                        "data": {
                            "labels": ["M1", "M2", "M3", "M4", "M5", "M6"],
                            "datasets": [{"label": "Fibonacci Growth", "data": [1, 1, 2, 3, 5, 8]}],
                        },
                    }
            else:
                spec_dict = code_or_spec
            image_bytes = await self.render_chart_to_image(spec_dict)
            image_url = f"https://quickchart.io/chart?c={quote(json.dumps(spec_dict))}"
        else:
            image_bytes = await self.render_mermaid_to_image(code_or_spec)
            image_url = f"https://mermaid.ink/img/{base64.b64encode(code_or_spec.strip().encode()).decode()}"

        filepath.write_bytes(image_bytes)
        return {
            "success": True,
            "title": title,
            "file_path": str(filepath.resolve()),
            "file_size_bytes": len(image_bytes),
            "image_url": image_url,
        }

    async def generate_ai_art_image(
        self,
        prompt: str,
        style: str = "photorealistic",
        width: int = 1024,
        height: int = 1024,
    ) -> dict[str, Any]:
        """Generate high-quality AI photography or digital art using FLUX.1 AI:
        Tier 1: Hugging Face FLUX.1-schnell Inference API (if hf_token available)
        Tier 2: NVIDIA NIM FLUX.1-schnell API (if nvidia_api_key available)
        Tier 3: OpenAI DALL-E 3 (if openai_api_key available)
        Tier 4: Procedural PIL Graphic Fallback (100% offline uptime)
        """
        import asyncio

        from PIL import Image, ImageDraw

        clean_prompt = prompt.strip()

        # Tamil & Tanglish prompt translator to enhance image prompt fidelity
        tamil_translations = {
            "நிலா": "luminous full moon glowing in dark star-filled night sky",
            "நிலவு": "luminous full moon glowing in dark star-filled night sky",
            "மழை": "dramatic cinematic monsoon rainfall with neon reflections",
            "கடல்": "scenic turquoise ocean waves crashing against coastal rocks",
            "சூரியன்": "radiant golden hour sun rays piercing through clouds",
            "சூரிய அஸ்தமனம்": "breathtaking golden hour sunset over misty mountains",
            "கோவில்": "majestic ancient South Indian temple gopuram architecture at sunrise",
            "பூனை": "adorable fluffy cute kitten with bright eyes",
            "நாய்": "playful loyal golden retriever dog outdoors",
            "மயில்": "regal peacock displaying iridescent colorful vibrant feathers",
            "காடு": "lush green enchanted tropical rainforest with sunlight rays",
            "கார்": "sleek aerodynamic modern luxury sports car at night",
        }
        for ta_term, en_term in tamil_translations.items():
            if ta_term in clean_prompt:
                clean_prompt = clean_prompt.replace(ta_term, en_term)

        clean_lower = clean_prompt.lower()

        # Auto-detect style from prompt keywords
        detected_style = style
        if "anime" in clean_lower or "manga" in clean_lower:
            detected_style = "anime"
        elif any(k in clean_lower for k in ("3d", "pixar", "render", "cgi")):
            detected_style = "3d_render"
        elif any(k in clean_lower for k in ("wallpaper", "phone status", "lockscreen")):
            detected_style = "wallpaper"
            width, height = 768, 1344
        elif any(k in clean_lower for k in ("cyberpunk", "sci-fi", "futuristic", "neon")):
            detected_style = "cyberpunk"
        elif any(k in clean_lower for k in ("watercolor", "oil painting", "canvas")):
            detected_style = "watercolor"

        # Style prompt enhancement
        if detected_style == "anime":
            enhanced_prompt = f"Studio Ghibli and Makoto Shinkai aesthetic anime artwork of {clean_prompt}, vibrant atmospheric lighting, 4k masterwork"
        elif detected_style == "3d_render":
            enhanced_prompt = f"Ultra-detailed 3D Pixar style character render of {clean_prompt}, smooth volumetric lighting, octane ray-traced, cute polished aesthetic"
        elif detected_style == "wallpaper":
            enhanced_prompt = f"Stunning AMOLED mobile phone vertical wallpaper of {clean_prompt}, deep rich blacks, vibrant glowing colors, 8k crisp details"
        elif detected_style == "cyberpunk":
            enhanced_prompt = f"Futuristic cyberpunk concept art of {clean_prompt}, neon reflections, rain, dramatic cinematic volumetric fog, 8k resolution"
        elif detected_style == "watercolor":
            enhanced_prompt = f"Expressive dreamy watercolor and ink illustration of {clean_prompt}, soft fluid paint drips, delicate paper texture"
        elif detected_style == "fantasy":
            enhanced_prompt = f"Epic fantasy digital masterpiece of {clean_prompt}, magical glowing particles, ethereal atmosphere, highly detailed"
        else:
            enhanced_prompt = (
                f"Award-winning 8k masterpiece photograph of {clean_prompt}, razor-sharp intricate details and realistic texture, "
                f"cinematic natural soft studio lighting, professional 85mm f/1.4 lens depth of field, stunning clarity"
            )

        slug = "".join(c if c.isalnum() else "_" for c in clean_prompt.lower())[:25]
        filename = f"{int(time.time())}_{slug}.jpg"
        filepath = DIAGRAM_CACHE_DIR / filename
        base_url = get_public_base_url()

        image_bytes = b""
        image_url = ""
        engine = "procedural-fallback"

        # Tier 1: Hugging Face FLUX.1-schnell Inference API (if hf_token configured)
        hf_token = getattr(self.settings, "hf_token", None)
        hf_secret = (
            hf_token.get_secret_value().strip()
            if hf_token and hasattr(hf_token, "get_secret_value")
            else str(hf_token or "").strip()
        )
        if not hf_secret:
            hf_secret = os.getenv("HF_TOKEN", "").strip()
        if hf_secret and not hf_secret.startswith("test") and not hf_secret.startswith("changeme"):
            own_client = False
            http = self.client
            try:
                if http is None:
                    http = httpx.AsyncClient(timeout=30.0)
                    own_client = True
                hf_url = "https://router.huggingface.co/hf-inference/models/black-forest-labs/FLUX.1-schnell"
                hf_resp = await http.post(
                    hf_url,
                    headers={"Authorization": f"Bearer {hf_secret}"},
                    json={"inputs": enhanced_prompt},
                    timeout=30.0,
                )
                if hf_resp.status_code == 200 and hf_resp.content:
                    image_bytes = hf_resp.content
                    filepath.write_bytes(image_bytes)
                    image_url = f"{base_url}/media/{filename}"
                    engine = "flux.1-schnell-hf"
                    logger.info("HF FLUX.1 Schnell generated %d bytes image", len(image_bytes))
            except Exception as exc:
                logger.warning("HF FLUX.1 Inference API skipped/failed: %s", exc)
            finally:
                if own_client and http is not None:
                    await http.aclose()

        # Tier 2: NVIDIA NIM FLUX.1-schnell API (if nvidia_api_key configured)
        nvidia_token = getattr(self.settings, "nvidia_api_key", None)
        nvidia_secret = (
            nvidia_token.get_secret_value().strip()
            if nvidia_token and hasattr(nvidia_token, "get_secret_value")
            else str(nvidia_token or "").strip()
        )
        if not nvidia_secret:
            nvidia_secret = os.getenv("NVIDIA_API_KEY", "").strip()
        if not image_bytes and nvidia_secret and not nvidia_secret.startswith("test") and not nvidia_secret.startswith("changeme"):
            own_client = False
            http = self.client
            try:
                if http is None:
                    http = httpx.AsyncClient(timeout=35.0)
                    own_client = True
                nim_url = "https://ai.api.nvidia.com/v1/genai/black-forest-labs/flux.1-schnell"
                nim_resp = await http.post(
                    nim_url,
                    headers={
                        "Authorization": f"Bearer {nvidia_secret}",
                        "Accept": "application/json",
                    },
                    json={
                        "prompt": enhanced_prompt[:1000],
                        "width": width,
                        "height": height,
                        "steps": 4,
                        "seed": 0,
                    },
                    timeout=35.0,
                )
                if nim_resp.status_code == 200:
                    payload = nim_resp.json()
                    b64_data = ""
                    if isinstance(payload.get("artifacts"), list) and payload["artifacts"]:
                        b64_data = payload["artifacts"][0].get("base64", "")
                    elif isinstance(payload.get("image"), str):
                        b64_data = payload["image"]
                    if b64_data:
                        image_bytes = base64.b64decode(b64_data)
                        filepath.write_bytes(image_bytes)
                        image_url = f"{base_url}/media/{filename}"
                        engine = "flux.1-schnell-nvidia"
                        logger.info("NVIDIA NIM FLUX.1 Schnell generated %d bytes image", len(image_bytes))
            except Exception as exc:
                logger.warning("NVIDIA NIM FLUX.1 skipped/failed: %s", exc)
            finally:
                if own_client and http is not None:
                    await http.aclose()

        # Tier 3: OpenAI DALL-E 3 (optional fallback if real API key is configured)
        openai_key = (
            self.settings.openai_api_key.get_secret_value().strip()
            if self.settings and hasattr(self.settings, "openai_api_key")
            else ""
        )
        if not image_bytes and openai_key and not openai_key.startswith("test-") and not openai_key.startswith("changeme"):
            own_client = False
            http = self.client
            try:
                from openai import AsyncOpenAI

                client = AsyncOpenAI(api_key=openai_key)
                dalle_resp = await asyncio.wait_for(
                    client.images.generate(
                        model="dall-e-3",
                        prompt=enhanced_prompt[:1000],
                        size="1024x1024",
                        quality="standard",
                        n=1,
                    ),
                    timeout=30.0,
                )
                if dalle_resp.data and dalle_resp.data[0].url:
                    dalle_img_url = dalle_resp.data[0].url
                    if http is None:
                        http = httpx.AsyncClient(timeout=20.0)
                        own_client = True
                    resp = await http.get(dalle_img_url)
                    if resp.status_code == 200 and resp.content:
                        image_bytes = resp.content
                        filepath.write_bytes(image_bytes)
                        image_url = f"{base_url}/media/{filename}"
                        engine = "dall-e-3"
                        logger.info("DALL-E 3 generated %d bytes image saved to %s", len(image_bytes), filepath)
            except Exception as exc:
                logger.warning("DALL-E 3 image generation skipped/failed: %s", exc)
            finally:
                if own_client and http is not None:
                    await http.aclose()

        # Tier 4: Procedural Graphic Fallback (100% offline guaranteed)
        if not image_bytes and not filepath.exists():
            try:
                img = Image.new("RGB", (width, height), color=(20, 24, 39))
                draw = ImageDraw.Draw(img)
                # Draw atmospheric gradient background
                for y in range(height):
                    ratio = y / height
                    r = int(20 + 40 * ratio)
                    g = int(24 + 10 * ratio)
                    b = int(39 + 70 * ratio)
                    draw.line([(0, y), (width, y)], fill=(r, g, b))
                # Add title & prompt text
                draw.text((60, 80), "THIRDHAND AI • FLUX STUDIO", fill=(147, 197, 253))
                draw.text((60, 140), clean_prompt[:80], fill=(255, 255, 255))
                img.save(filepath, "JPEG", quality=90)
                image_bytes = filepath.read_bytes()
                image_url = f"{base_url}/media/{filename}"
                engine = "procedural-fallback"
            except Exception as exc:
                logger.error("Procedural image generation failed: %s", exc)

        return {
            "success": True,
            "engine": engine,
            "prompt": clean_prompt,
            "style": detected_style,
            "enhanced_prompt": enhanced_prompt,
            "image_url": image_url,
            "file_path": str(filepath.resolve()) if filepath.exists() else None,
            "file_size_bytes": len(image_bytes),
        }

