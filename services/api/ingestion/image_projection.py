import hashlib
import json
import os
import subprocess
from io import BytesIO
from uuid import uuid4

from PIL import Image, UnidentifiedImageError

from app.config import ROOT

from .document_projection import canonical

Image.MAX_IMAGE_PIXELS = 16_000_000


def project_image(data, verified_text=None):
    try:
        with Image.open(BytesIO(data)) as image:
            if image.format not in ("PNG", "JPEG") or image.width * image.height > 16_000_000:
                raise ValueError("Use a PNG or JPEG with at most 16 million pixels.")
            image.load()
            width, height = image.size
            image_format = image.format
            local = image.convert("RGB")
            local.thumbnail((2400, 2400))
    except (UnidentifiedImageError, Image.DecompressionBombError, OSError):
        raise ValueError("Image could not be decoded safely.") from None
    result = {}
    text = verified_text or ""
    ocr_status = "manual_transcript" if verified_text is not None else "unavailable"
    if verified_text is None and os.name == "nt":
        path = ROOT / ".cache/tmp" / f"ocr-{uuid4()}.png"
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            local.save(path)
            command = [
                os.path.join(
                    os.environ.get("SystemRoot", r"C:\Windows"),
                    "System32/WindowsPowerShell/v1.0/powershell.exe",
                ),
                "-NoProfile",
                "-NonInteractive",
                "-File",
                str(ROOT / "scripts/ocr.ps1"),
                "-ImagePath",
                str(path),
            ]
            process = subprocess.run(
                command,
                capture_output=True,
                text=True,
                encoding="utf-8-sig",
                timeout=20,
                check=False,
            )
            result = json.loads(process.stdout)
            if process.returncode == 0:
                text = result.get("text", "")
                ocr_status = "extracted_unverified"
        except (subprocess.TimeoutExpired, ValueError, OSError):
            result = {}
        finally:
            path.unlink(missing_ok=True)
    text = canonical(text)
    verified = verified_text is not None and bool(text.strip())
    return {
        "text": text,
        "blocks": [
            {
                "part": "image_transcript",
                "block_id": "transcript",
                "start": 0,
                "end": len(text),
                "quote": text,
            }
        ],
        "unresolved_changes": 0,
        "coverage": {
            "text_complete": verified,
            "unsupported": [] if verified else ["OCR transcript requires creator verification."],
            "exclusions": [
                "Image appearance, logo placement and visual accessibility require human inspection."
            ],
            "parts": [
                "Creator-verified image transcript" if verified else "Unverified OCR transcript"
            ],
        },
        "image": {
            "width": width,
            "height": height,
            "format": image_format,
            "ocr_width": local.width,
            "ocr_height": local.height,
            "ocr_status": ocr_status,
            "ocr_engine": result.get("engine"),
            "language": result.get("language"),
            "lines": result.get("lines", []),
        },
        "file_sha256": hashlib.sha256(data).hexdigest(),
    }
