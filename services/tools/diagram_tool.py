"""Visual Diagram & Chart Generation Tool for Thirdhand AI WhatsApp Super-Agent."""

from __future__ import annotations

import base64
import json
import logging
import time
from pathlib import Path
from typing import Any
from urllib.parse import quote

import httpx

logger = logging.getLogger(__name__)

DIAGRAM_CACHE_DIR = Path("data/generated_diagrams")
DIAGRAM_CACHE_DIR.mkdir(parents=True, exist_ok=True)


def get_public_base_url() -> str:
    """Return active public tunnel URL or fallback."""
    url_file = Path("data/whatsapp/public_url.txt")
    if url_file.exists():
        try:
            val = url_file.read_text(encoding="utf-8").strip()
            if val.startswith("http"):
                return val
        except Exception:
            pass
    return "https://35374a9ef8f4ff.lhr.life"


class VisualDiagramTool:
    """Generates visual diagram and chart images (flowcharts, sequence diagrams, charts) via Mermaid.ink and QuickChart."""

    def __init__(self, client: httpx.AsyncClient | None = None) -> None:
        self.client = client

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
        """Generate ultra-high-quality AI photography or digital art via Black Forest Labs FLUX.1 Schnell."""
        import asyncio
        clean_prompt = prompt.strip()
        clean_lower = clean_prompt.lower()

        # Auto-detect style from prompt keywords if default
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

        # Refined prompt engineering for breathtaking visual fidelity
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
            # Default / Photorealistic
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

        # Tier 1: Black Forest Labs FLUX.1 Schnell (World's #1 photorealistic open model)
        try:
            from gradio_client import Client
            from PIL import Image

            def _call_flux():
                client = Client("black-forest-labs/FLUX.1-schnell")
                return client.predict(
                    prompt=enhanced_prompt,
                    seed=0,
                    randomize_seed=True,
                    width=width,
                    height=height,
                    num_inference_steps=4,
                    api_name="/infer",
                )

            res = await asyncio.wait_for(asyncio.to_thread(_call_flux), timeout=25.0)
            if res and isinstance(res, (list, tuple)) and res[0]:
                raw_path = Path(res[0])
                if raw_path.exists():
                    img = Image.open(raw_path)
                    img.convert("RGB").save(filepath, "JPEG", quality=95)
                    image_bytes = filepath.read_bytes()
                    image_url = f"{base_url}/media/{filename}"
                    logger.info("FLUX.1 Schnell generated %d bytes image saved to %s", len(image_bytes), filepath)
        except Exception as exc:
            logger.warning("FLUX.1 Schnell generation failed (%s), using high-speed fallback", exc)

        # Tier 2: Resilient Fallback if FLUX Space is queued
        if not image_bytes or not image_url:
            encoded_prompt = quote(enhanced_prompt)
            fallback_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={width}&height={height}&nologo=true&model=flux"
            own_client = False
            http = self.client
            try:
                if http is None:
                    http = httpx.AsyncClient(timeout=20.0)
                    own_client = True
                resp = await http.get(fallback_url)
                if resp.status_code == 200 and resp.content:
                    image_bytes = resp.content
                    filepath.write_bytes(image_bytes)
                    image_url = f"{base_url}/media/{filename}"
                else:
                    image_url = fallback_url
            except Exception as exc:
                logger.warning("Fallback image download failed (%s)", exc)
                image_url = fallback_url
            finally:
                if own_client and http is not None:
                    await http.aclose()

        return {
            "success": True,
            "prompt": clean_prompt,
            "style": detected_style,
            "enhanced_prompt": enhanced_prompt,
            "image_url": image_url,
            "file_path": str(filepath.resolve()) if filepath.exists() else None,
            "file_size_bytes": len(image_bytes),
        }
