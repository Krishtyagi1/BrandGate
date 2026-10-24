from io import BytesIO
from zipfile import ZIP_DEFLATED, ZipFile

import pytest
from docx import Document

from ingestion.document_projection import project_document


def fixture_doc():
    doc = Document()
    doc.add_heading("Synthetic policy", 1)
    p = doc.add_paragraph("Cloudberry ")
    p.add_run("Daily Cleanser").bold = True
    doc.add_table(rows=1, cols=1).cell(0, 0).text = "Price: INR 799"
    doc.sections[0].header.paragraphs[0].text = "Private header"
    doc.sections[0].footer.paragraphs[0].text = "Footer 🪷"
    stream = BytesIO()
    doc.save(stream)
    return stream.getvalue()


def test_projection_body_table_header_footer_and_exact_anchors():
    data = fixture_doc()
    result = project_document(data)
    assert result["coverage"]["text_complete"]
    assert "Cloudberry Daily Cleanser" in result["text"]
    assert "Price: INR 799" in result["text"]
    assert "Private header" in result["text"]
    assert "Footer 🪷" in result["text"]
    for block in result["blocks"]:
        assert result["text"][block["start"] : block["end"]] == block["quote"]
    assert data == data  # projection receives immutable bytes, no write path


def test_tracked_changes_and_unsupported_parts_block_final_submission():
    source = fixture_doc()
    output = BytesIO()
    with ZipFile(BytesIO(source)) as original, ZipFile(output, "w", ZIP_DEFLATED) as modified:
        for entry in original.infolist():
            data = original.read(entry.filename)
            if entry.filename == "word/document.xml":
                data = data.replace(
                    b"<w:body>",
                    b'<w:body><w:p><w:ins w:id="7"><w:r><w:t>Inserted</w:t></w:r></w:ins></w:p>',
                )
            modified.writestr(entry, data)
        modified.writestr(
            "word/footnotes.xml",
            '<w:footnotes xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:footnote><w:p><w:r><w:t>Uncovered note</w:t></w:r></w:p></w:footnote></w:footnotes>',
        )
    result = project_document(output.getvalue())
    assert result["unresolved_changes"] == 1
    assert not result["coverage"]["text_complete"]
    assert any("footnotes" in x for x in result["coverage"]["unsupported"])


def test_invalid_package_rejected():
    with pytest.raises(ValueError):
        project_document(b"not a zip")


@pytest.mark.parametrize("part", ["word/charts/chart1.xml", "word/diagrams/data1.xml"])
def test_unhandled_drawing_text_cannot_receive_complete_coverage(part):
    output = BytesIO()
    with ZipFile(BytesIO(fixture_doc())) as source, ZipFile(output, "w") as target:
        for entry in source.infolist():
            target.writestr(entry, source.read(entry.filename))
        target.writestr(
            part,
            '<a:root xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"><a:t>Hidden promotional claim</a:t></a:root>',
        )
    result = project_document(output.getvalue())
    assert not result["coverage"]["text_complete"]
    assert any(part in item for item in result["coverage"]["unsupported"])
