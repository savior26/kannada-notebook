import pytesseract
from PIL import Image
from pytesseract import Output
from myapp.config.settings import settings
from myapp.ocr.ocr_schema import OCRWord

pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_CMD
class KannadaTesseractOCR:

    def __init__(
        self,
        language: str = settings.OCR_LANGUAGE,
        oem: int = settings.OCR_ENGINE_MODE,
        psm: int = settings.OCR_PAGE_SEGMENTATION
    ):
        self.language = language
        self.oem = oem
        self.psm = psm

    def extract_text(self, image: Image.Image):

        config = (
            f"--oem {self.oem} "
            f"--psm {self.psm}"
        )

        text = pytesseract.image_to_string(
            image,
            lang=self.language,
            config=config
        )

        return text.strip()

    def extract_words(self, image: Image.Image):

        config = (
            f"--oem {self.oem} "
            f"--psm {self.psm}"
        )

        data = pytesseract.image_to_data(
            image,
            lang=self.language,
            config=config,
            output_type=Output.DICT
        )

        words = []

        for i in range(len(data["text"])):

            text = data["text"][i].strip()

            try:
                confidence = float(data["conf"][i])
            except (ValueError, TypeError):
                confidence = -1

            if not text:
                continue

            if confidence < 0:
                continue

            words.append(
                OCRWord(
                    text=text,
                    confidence=confidence,
                    left=int(data["left"][i]),
                    top=int(data["top"][i]),
                    width=int(data["width"][i]),
                    height=int(data["height"][i])
                )
            )

        return words

    def get_confidence(self, words):

        valid = [
            word.confidence
            for word in words
            if word.confidence >= 0
        ]

        if not valid:
            return 0.0

        return round(sum(valid) / len(valid), 2)

    def process(self, image: Image.Image):

        text = self.extract_text(image)

        words = self.extract_words(image)

        confidence = self.get_confidence(words)

        return {
            "text": text,
            "words": words,
            "confidence": confidence
        }