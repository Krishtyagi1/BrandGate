from io import BytesIO

import pytest
from PIL import Image

from ingestion.image_projection import project_image


def synthetic_image():
    image = Image.new("RGB", (240, 100), "white")
    output = BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()


def test_image_requires_explicit_transcript_verification():
    projection = project_image(synthetic_image(), verified_text="Synthetic image transcript")
    assert projection["coverage"]["text_complete"]
    assert projection["coverage"]["exclusions"]
    assert projection["image"]["ocr_status"] == "manual_transcript"


def test_malformed_image_rejected():
    with pytest.raises(ValueError):
        project_image(b"not an image", verified_text="Test")
