from pathlib import Path

from docx import Document
from pypdf import PdfReader


PARSER_VERSION = "resume_parser_v1"


def extract_pdf_text(file_path):
    reader = PdfReader(file_path)

    pages = []

    for page in reader.pages:
        text = page.extract_text()

        if text:
            pages.append(text)

    return "\n\n".join(pages)


def extract_docx_text(file_path):
    document = Document(file_path)

    paragraphs = [
        paragraph.text
        for paragraph in document.paragraphs
        if paragraph.text.strip()
    ]

    return "\n".join(paragraphs)


def extract_txt_text(file_path):
    return Path(file_path).read_text(
        encoding="utf-8"
    )


def extract_resume_text(file_path):
    file_path = Path(file_path)

    suffix = file_path.suffix.lower()

    if suffix == ".pdf":
        file_type = "pdf"
        text = extract_pdf_text(file_path)

    elif suffix == ".docx":
        file_type = "docx"
        text = extract_docx_text(file_path)

    elif suffix == ".txt":
        file_type = "txt"
        text = extract_txt_text(file_path)

    else:
        raise ValueError(
            "Supported resume formats: "
            "PDF, DOCX and TXT."
        )

    text = text.strip()

    if not text:
        raise ValueError(
            "No text could be extracted "
            "from the resume."
        )

    return file_type, text