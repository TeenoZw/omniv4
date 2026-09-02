"""Small dependency-free PDF rendering helpers for export summaries."""
from __future__ import annotations

from io import BytesIO
import textwrap


PAGE_WIDTH = 612
PAGE_HEIGHT = 792
LEFT_MARGIN = 48
TOP_Y = 760
LINE_HEIGHT = 15
MAX_LINES_PER_PAGE = 44


def _escape_pdf_text(value: str) -> str:
    return value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _wrap_line(value: str, width: int = 92) -> list[str]:
    if not value:
        return [""]
    return textwrap.wrap(value, width=width, break_long_words=True, break_on_hyphens=False) or [""]


def _build_lines(title: str, sections: list[tuple[str, list[str]]]) -> list[str]:
    lines = [title, ""]
    for heading, values in sections:
        lines.extend(_wrap_line(heading.upper(), width=72))
        for value in values:
            prefix = "- " if value else ""
            wrapped = _wrap_line(f"{prefix}{value}" if value else "", width=96)
            lines.extend(wrapped)
        lines.append("")
    return lines


def _render_page(lines: list[str]) -> bytes:
    commands = ["BT", "/F1 11 Tf", f"{LEFT_MARGIN} {TOP_Y} Td", f"{LINE_HEIGHT} TL"]
    for index, line in enumerate(lines):
        if index > 0:
            commands.append("T*")
        commands.append(f"({_escape_pdf_text(line)}) Tj")
    commands.append("ET")
    return "\n".join(commands).encode("latin-1", errors="replace")


def build_simple_pdf(title: str, sections: list[tuple[str, list[str]]]) -> bytes:
    """Render a basic multi-page PDF for audit exports without extra dependencies."""
    lines = _build_lines(title, sections)
    pages = [lines[i : i + MAX_LINES_PER_PAGE] for i in range(0, len(lines), MAX_LINES_PER_PAGE)] or [[title]]

    objects: list[bytes] = []

    def add_object(payload: bytes) -> int:
        objects.append(payload)
        return len(objects)

    catalog_id = add_object(b"<< /Type /Catalog /Pages 2 0 R >>")
    pages_id = add_object(b"<< /Type /Pages /Count 0 /Kids [] >>")
    font_id = add_object(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")

    page_ids: list[int] = []
    for page_lines in pages:
        content = _render_page(page_lines)
        content_id = add_object(
            f"<< /Length {len(content)} >>\nstream\n".encode("latin-1") + content + b"\nendstream"
        )
        page_id = add_object(
            (
                "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {width} {height}] "
                "/Resources << /Font << /F1 {font} 0 R >> >> /Contents {content} 0 R >>"
            )
            .format(width=PAGE_WIDTH, height=PAGE_HEIGHT, font=font_id, content=content_id)
            .encode("latin-1")
        )
        page_ids.append(page_id)

    kids = " ".join(f"{page_id} 0 R" for page_id in page_ids)
    objects[pages_id - 1] = f"<< /Type /Pages /Count {len(page_ids)} /Kids [{kids}] >>".encode("latin-1")

    buffer = BytesIO()
    buffer.write(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]
    for object_id, payload in enumerate(objects, start=1):
        offsets.append(buffer.tell())
        buffer.write(f"{object_id} 0 obj\n".encode("latin-1"))
        buffer.write(payload)
        buffer.write(b"\nendobj\n")

    xref_offset = buffer.tell()
    buffer.write(f"xref\n0 {len(objects) + 1}\n".encode("latin-1"))
    buffer.write(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        buffer.write(f"{offset:010d} 00000 n \n".encode("latin-1"))

    buffer.write(
        (
            "trailer\n"
            f"<< /Size {len(objects) + 1} /Root {catalog_id} 0 R >>\n"
            "startxref\n"
            f"{xref_offset}\n"
            "%%EOF"
        ).encode("latin-1")
    )
    return buffer.getvalue()
