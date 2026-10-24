from test_image_projection import synthetic_image


def test_pdf_image_body_with_selectable_header_is_incomplete(workspace):
    from io import BytesIO

    from pypdf import PdfWriter
    from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject, NumberObject

    owner, org, _ = workspace
    writer = PdfWriter()
    page = writer.add_blank_page(width=300, height=300)
    image = DecodedStreamObject()
    image.set_data(b"\xff\xff\xff")
    image.update(
        {
            NameObject("/Type"): NameObject("/XObject"),
            NameObject("/Subtype"): NameObject("/Image"),
            NameObject("/Width"): NumberObject(1),
            NameObject("/Height"): NumberObject(1),
            NameObject("/ColorSpace"): NameObject("/DeviceRGB"),
            NameObject("/BitsPerComponent"): NumberObject(8),
        }
    )
    font = DictionaryObject(
        {
            NameObject("/Type"): NameObject("/Font"),
            NameObject("/Subtype"): NameObject("/Type1"),
            NameObject("/BaseFont"): NameObject("/Helvetica"),
        }
    )
    page[NameObject("/Resources")] = DictionaryObject(
        {
            NameObject("/XObject"): DictionaryObject(
                {NameObject("/Im1"): writer._add_object(image)}
            ),
            NameObject("/Font"): DictionaryObject({NameObject("/F1"): writer._add_object(font)}),
        }
    )
    content = DecodedStreamObject()
    content.set_data(b"BT /F1 12 Tf 20 280 Td (Page 1) Tj ET q 250 0 0 250 20 20 cm /Im1 Do Q")
    page[NameObject("/Contents")] = writer._add_object(content)
    output = BytesIO()
    writer.write(output)
    result = owner.post(
        f"/api/organisations/{org}/drafts/upload",
        files={"file": ("mixed.pdf", output.getvalue(), "application/pdf")},
    )
    assert result.status_code == 201, result.text
    projection = result.json()["current_version"]["projection"]
    assert "Page 1" in projection["text"]
    assert not projection["coverage"]["text_complete"]
    assert "Page 1" in projection["coverage"]["unsupported"][0]


def test_image_original_and_verified_transcript_bound_to_revision(workspace):
    owner, org, _ = workspace
    base = f"/api/organisations/{org}/drafts"
    data = synthetic_image()
    result = owner.post(base + "/upload", files={"file": ("synthetic.png", data, "image/png")})
    assert result.status_code == 201, result.text
    draft = result.json()
    version = draft["current_version"]
    assert draft["format"] == "image"
    assert not version["projection"]["coverage"]["text_complete"]
    body = {
        "expected_current_version_id": version["id"],
        "text": "Synthetic transcript",
        "verified": False,
    }
    assert owner.post(f"{base}/{draft['id']}/transcript", json=body).status_code == 422
    body["verified"] = True
    saved = owner.post(f"{base}/{draft['id']}/transcript", json=body)
    assert saved.status_code == 201, saved.text
    current = saved.json()
    assert current["projection"]["coverage"]["text_complete"]
    assert current["projection"]["coverage"]["exclusions"]
    assert current["artifact_sha256"] != version["artifact_sha256"]
    assert owner.get(f"{base}/{draft['id']}/versions/{current['id']}/download").content == data


def test_restoring_creates_new_revision_and_preserves_history(workspace):
    owner, org, _ = workspace
    base = f"/api/organisations/{org}/drafts"
    draft = owner.post(base, json={"text": "Original content"}).json()
    second = owner.post(
        f"{base}/{draft['id']}/versions",
        json={
            "expected_current_version_id": draft["current_version_id"],
            "text": "Changed content",
        },
    ).json()
    body = {
        "expected_current_version_id": second["id"],
        "source_version_id": draft["current_version_id"],
    }
    restored = owner.post(f"{base}/{draft['id']}/restore", json=body)
    assert restored.status_code == 201, restored.text
    assert restored.json()["text"] == "Original content" and restored.json()["revision"] == 3
    assert restored.json()["id"] != draft["current_version_id"]
    assert owner.post(f"{base}/{draft['id']}/restore", json=body).status_code == 409
    assert len(owner.get(f"{base}/{draft['id']}").json()["versions"]) == 3
