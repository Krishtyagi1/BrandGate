"""Bounded, read-only OOXML projection. The original DOCX remains immutable."""

import hashlib
import re
import unicodedata
from io import BytesIO
from xml.etree import ElementTree as ET
from zipfile import BadZipFile, ZipFile

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def canonical(text):
    return unicodedata.normalize("NFC", text.replace("\r\n", "\n").replace("\r", "\n"))


def project_document(data):
    try:
        archive = ZipFile(BytesIO(data))
    except BadZipFile:
        raise ValueError("This is not a valid DOCX package.") from None
    with archive:
        entries = archive.infolist()
        if len(entries) > 1000 or sum(x.file_size for x in entries) > 30 * 1024 * 1024:
            raise ValueError("DOCX expands beyond the supported 30 MB / 1000-part limit.")
        names = archive.namelist()
        if len(set(names)) != len(names) or "word/document.xml" not in names:
            raise ValueError("Invalid DOCX package entries.")
        if any("vbaProject" in x or x.endswith(".bin") for x in names):
            raise ValueError("Macro or embedded binary documents are unsupported.")
        blocks, unsupported, exclusions, text_parts = (
            [],
            [],
            ["Document page layout requires human inspection."],
            [],
        )
        unresolved = 0
        parts = ["word/document.xml"] + sorted(
            x for x in names if re.fullmatch(r"word/(header|footer)\d+\.xml", x)
        )
        offset = 0
        for name in names:
            if name.endswith(".rels"):
                raw = archive.read(name)
                if b"<!DOCTYPE" in raw or b"<!ENTITY" in raw:
                    raise ValueError("XML declarations are unsupported.")
                try:
                    tree = ET.fromstring(raw)
                except ET.ParseError:
                    raise ValueError("Document relationship XML is damaged.") from None
                if any(
                    x.attrib.get("TargetMode") == "External"
                    and not x.attrib.get("Type", "").endswith("/hyperlink")
                    for x in tree
                ):
                    raise ValueError("Remote linked resources must be removed before editing.")
            if name.startswith("word/") and name.endswith(".xml") and name not in parts:
                raw = archive.read(name)
                if b"<!DOCTYPE" in raw or b"<!ENTITY" in raw:
                    raise ValueError("XML declarations are unsupported.")
                try:
                    extra = ET.fromstring(raw)
                except ET.ParseError:
                    raise ValueError("Document XML is damaged.") from None
                if any(kind in name for kind in ("footnote", "endnote", "glossary")) or any(
                    node.tag.rsplit("}", 1)[-1] in ("t", "v", "instrText", "delText")
                    and (node.text or "").strip()
                    for node in extra.iter()
                ):
                    unsupported.append(name)
        for part in parts:
            raw = archive.read(part)
            if b"<!DOCTYPE" in raw or b"<!ENTITY" in raw:
                raise ValueError("XML declarations are unsupported.")
            try:
                root = ET.fromstring(raw)
            except ET.ParseError:
                raise ValueError("Document XML is damaged.") from None
            unresolved += sum(
                1
                for x in root.iter()
                if x.tag in (W + "ins", W + "del", W + "moveFrom", W + "moveTo")
            )
            if any(
                node.tag != W + "t"
                and node.tag.rsplit("}", 1)[-1] in ("t", "v")
                and (node.text or "").strip()
                for node in root.iter()
            ):
                unsupported.append(part + ": unsupported drawing text")
            if any(
                x.tag
                in (W + "txbxContent", W + "altChunk", W + "fldSimple", W + "fldChar", W + "object")
                for x in root.iter()
            ):
                unsupported.append(
                    part + ": text boxes, fields, embedded objects or alternate content"
                )
            for number, paragraph in enumerate(root.iter(W + "p")):
                pieces = []
                for node in paragraph.iter():
                    if node.tag == W + "t":
                        pieces.append(node.text or "")
                    elif node.tag == W + "tab":
                        pieces.append("\t")
                    elif node.tag in (W + "br", W + "cr"):
                        pieces.append("\n")
                text = canonical("".join(pieces))
                if text:
                    if text_parts:
                        offset += 1
                    blocks.append(
                        {
                            "part": part,
                            "block_id": f"{part}:p{number}",
                            "start": offset,
                            "end": offset + len(text),
                            "quote": text,
                        }
                    )
                    text_parts.append(text)
                    offset += len(text)
        if any(x.startswith("word/media/") for x in names):
            exclusions.append("Embedded images and visual layout require human inspection.")
        text = "\n".join(text_parts)
        if not text.strip() or len(text) > 200000:
            raise ValueError(
                "Document must contain between 1 and 200,000 supported text characters."
            )
        return {
            "text": text,
            "blocks": blocks,
            "unresolved_changes": unresolved,
            "coverage": {
                "text_complete": not unsupported,
                "unsupported": unsupported,
                "exclusions": exclusions,
                "parts": parts,
            },
            "file_sha256": hashlib.sha256(data).hexdigest(),
        }
