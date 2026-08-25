from unittest.mock import MagicMock, patch

from app.services import text_extraction


def test_extract_text_from_pdf_native_joins_pages():
    fake_page_1 = MagicMock()
    fake_page_1.extract_text.return_value = "Chapitre 1"
    fake_page_2 = MagicMock()
    fake_page_2.extract_text.return_value = "Chapitre 2"

    fake_reader = MagicMock()
    fake_reader.pages = [fake_page_1, fake_page_2]

    with patch.object(text_extraction, "PdfReader", return_value=fake_reader):
        text = text_extraction.extract_text_from_pdf_native("fake.pdf")

    assert "Chapitre 1" in text
    assert "Chapitre 2" in text


def test_extract_text_from_file_dispatches_txt(tmp_path):
    txt_file = tmp_path / "notes.txt"
    txt_file.write_text("Contenu du cours", encoding="utf-8")

    text, method = text_extraction.extract_text_from_file(str(txt_file))

    assert text == "Contenu du cours"
    assert method == "txt"


def test_extract_text_from_file_falls_back_to_ocr_when_native_is_short():
    with patch.object(text_extraction, "extract_text_from_pdf_native", return_value="a"), \
         patch.object(text_extraction, "ocr_pdf_scanned", return_value="Long texte OCR bien plus riche"):
        text, method = text_extraction.extract_text_from_file("scan.pdf")

    assert method == "ocr"
    assert text == "Long texte OCR bien plus riche"


def test_extract_text_from_file_unsupported_extension():
    text, method = text_extraction.extract_text_from_file("archive.zip")
    assert text == ""
    assert method == "unsupported"
