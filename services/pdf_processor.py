"""Bounded PDF extraction in a killable subprocess, preserved from global checkout."""

import asyncio
import sys
from pathlib import Path


async def extract_pdf(data: bytes) -> str:
    if len(data) > 8 * 1024 * 1024 or not data.startswith(b"%PDF-"):
        raise ValueError("Send a PDF up to 8 MB")
    worker = Path(__file__).with_name("pdf_worker.py")
    process = await asyncio.create_subprocess_exec(
        sys.executable,
        "-I",
        str(worker),
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.DEVNULL,
    )
    try:
        output, _ = await asyncio.wait_for(process.communicate(data), 15)
    finally:
        if process.returncode is None:
            process.kill()
            await process.wait()
    if process.returncode or len(output) > 20000:
        raise ValueError("Send an unlocked, readable PDF with up to 30 pages")
    return output.decode("utf-8")[:3900]
