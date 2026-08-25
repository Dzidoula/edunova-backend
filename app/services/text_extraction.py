from typing import Tuple

from pypdf import PdfReader

try:
    import pytesseract
    from PIL import Image, ImageEnhance, ImageFilter, ImageOps

    HAS_OCR = True
except ImportError:
    HAS_OCR = False

try:
    from pdf2image import convert_from_path

    HAS_PDF2IMAGE = True
except ImportError:
    HAS_PDF2IMAGE = False

try:
    import easyocr

    HAS_EASYOCR = True
except ImportError:
    HAS_EASYOCR = False


def extract_text_from_pdf_native(file_path: str, max_pages: int = 30) -> str:
    try:
        reader = PdfReader(file_path)
        parts = []
        for i, page in enumerate(reader.pages[:max_pages]):
            t = (page.extract_text() or "").strip()
            if t:
                parts.append(f"--- Page {i + 1} ---\n{t}")
        return "\n\n".join(parts)
    except Exception as e:
        print(f"[PDF] {e}")
        return ""


def _ocr_preprocess(img: "Image.Image") -> "Image.Image":
    if img.mode not in ("L", "1"):
        img = img.convert("L")

    w, h = img.size
    if max(w, h) < 1200:
        scale = 1200 / max(w, h)
        img = img.resize((int(w * scale), int(h * scale)), Image.Resampling.LANCZOS)

    img = ImageOps.autocontrast(img, cutoff=1)
    img = ImageEnhance.Contrast(img).enhance(1.6)
    img = ImageEnhance.Sharpness(img).enhance(1.4)
    img = img.filter(ImageFilter.MedianFilter(size=3))

    hist = img.histogram()
    total = sum(hist)
    acc = 0
    threshold = 128
    for i, count in enumerate(hist):
        acc += count
        if acc >= total * 0.5:
            threshold = i
            break
    threshold = max(90, min(180, threshold - 10))
    img = img.point(lambda x: 255 if x > threshold else 0, mode="1")
    return img.convert("L")


def _tesseract_config(psm: int = 6) -> str:
    return f"--oem 3 --psm {psm} -c preserve_interword_spaces=1"


def _ocr_pil_image(img: "Image.Image", lang: str = "fra+eng") -> str:
    if not HAS_OCR:
        return ""

    candidates = []
    processed = _ocr_preprocess(img)
    variants = [(processed, 6), (processed, 4), (processed, 3)]
    try:
        gray = img.convert("L")
        w, h = gray.size
        if max(w, h) < 1400:
            scale = 1400 / max(w, h)
            gray = gray.resize((int(w * scale), int(h * scale)), Image.Resampling.LANCZOS)
        variants.append((gray, 6))
    except Exception:
        pass

    langs_to_try = [lang, "fra", "eng"]
    for variant_img, psm in variants:
        for lg in langs_to_try:
            try:
                t = pytesseract.image_to_string(variant_img, lang=lg, config=_tesseract_config(psm))
                t = (t or "").strip()
                if t:
                    candidates.append(t)
            except Exception:
                continue
        if candidates and len(max(candidates, key=len)) > 80:
            break

    if not candidates:
        return ""

    def score(text: str) -> float:
        letters = sum(c.isalpha() for c in text)
        return len(text) * 0.7 + letters * 0.3

    return max(candidates, key=score)


class OpticalRecognitionModel:
    def __init__(self, engine: str = "auto"):
        if engine == "auto":
            self.engine = "easyocr" if HAS_EASYOCR else "tesseract"
        else:
            self.engine = engine
        self._easy_reader = None

    def _get_easy_reader(self):
        if self._easy_reader is None and HAS_EASYOCR:
            self._easy_reader = easyocr.Reader(["fr", "en"], gpu=False, verbose=False)
        return self._easy_reader

    def recognize_image(self, img: "Image.Image", lang: str = "fra+eng") -> str:
        if self.engine == "easyocr" and HAS_EASYOCR:
            return self._recognize_easyocr(img)
        return _ocr_pil_image(img, lang=lang)

    def recognize_file(self, file_path: str, lang: str = "fra+eng") -> str:
        if not file_path:
            return ""
        lower = file_path.lower()
        if lower.endswith(".pdf"):
            return self.recognize_pdf(file_path, lang=lang)
        if not HAS_OCR and not HAS_EASYOCR:
            return ""
        try:
            img = Image.open(file_path) if HAS_OCR else None
            if img is None:
                return ""
            return self.recognize_image(img, lang=lang)
        except Exception as e:
            print(f"[OCR model file] {e}")
            return ""

    def recognize_pdf(self, file_path: str, max_pages: int = 12, lang: str = "fra+eng") -> str:
        if not HAS_PDF2IMAGE:
            return ""
        try:
            images = convert_from_path(file_path, first_page=1, last_page=max_pages, dpi=300, fmt="png")
            parts = []
            for i, img in enumerate(images):
                t = self.recognize_image(img, lang=lang)
                if t:
                    parts.append(f"--- Page {i + 1} (OCR:{self.engine}) ---\n{t}")
            return "\n\n".join(parts)
        except Exception as e:
            print(f"[OCR model PDF] {e}")
            return ""

    def _recognize_easyocr(self, img: "Image.Image") -> str:
        try:
            import numpy as np

            reader = self._get_easy_reader()
            if reader is None:
                return _ocr_pil_image(img) if HAS_OCR else ""
            arr = np.array(img.convert("RGB"))
            lines = reader.readtext(arr, detail=0, paragraph=True)
            return "\n".join(str(x) for x in lines).strip()
        except Exception as e:
            print(f"[EasyOCR] {e}")
            return _ocr_pil_image(img) if HAS_OCR else ""


def ocr_image_file(file_path: str, lang: str = "fra+eng", engine: str = "auto") -> str:
    return OpticalRecognitionModel(engine=engine).recognize_file(file_path, lang=lang)


def ocr_pdf_scanned(file_path: str, max_pages: int = 12, lang: str = "fra+eng", engine: str = "auto") -> str:
    return OpticalRecognitionModel(engine=engine).recognize_pdf(file_path, max_pages=max_pages, lang=lang)


def extract_text_from_file(
    file_path: str, use_ocr_if_needed: bool = True, ocr_engine: str = "auto"
) -> Tuple[str, str]:
    """Retourne (texte, méthode) où méthode ∈ native|ocr|txt|empty|unsupported."""
    if not file_path:
        return "", "empty"
    lower = file_path.lower()

    if lower.endswith((".txt", ".md")):
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read(), "txt"
        except Exception:
            return "", "empty"

    if lower.endswith((".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff")):
        if use_ocr_if_needed and HAS_OCR:
            text = ocr_image_file(file_path, engine=ocr_engine)
            return text, ("ocr" if text else "empty")
        return "", "unsupported"

    if lower.endswith(".pdf"):
        text = extract_text_from_pdf_native(file_path)
        if use_ocr_if_needed and len(text.strip()) < 80:
            ocr_text = ocr_pdf_scanned(file_path, engine=ocr_engine)
            if len(ocr_text.strip()) > len(text.strip()):
                return ocr_text, "ocr"
        return text, ("native" if text.strip() else "empty")

    return "", "unsupported"
