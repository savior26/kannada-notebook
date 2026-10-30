from pathlib import Path
from myapp.ocr.ocr_schema import OCRPageResult, OCRDocumentResult
from PIL import Image
from myapp.ocr.preprocessing import preprocess_image
from myapp.ocr.pdf_processor import pdf_to_images
from myapp.ocr.handwriting_engine import extract_handwritten_text_with_gemini
from myapp.ocr.tesseract_engine import KannadaTesseractOCR
class OCRService:

    # Change this threshold after testing your dataset
    TESSERACT_CONFIDENCE_THRESHOLD = 70.0

    def __init__(self):

        # Existing Tesseract OCR engine
        self.ocr_engine = KannadaTesseractOCR()

        
    # ---------------------------------------------------------
    # CLASSIFICATION
    # ---------------------------------------------------------

    def classify_document(
        self,
        confidence: float
    ) -> str:

        if confidence >= self.TESSERACT_CONFIDENCE_THRESHOLD:

            return "PRINTED"

        return "HANDWRITTEN_OR_UNCLEAR"

    # ---------------------------------------------------------
    # PROCESS IMAGE
    # ---------------------------------------------------------

    def process_image(
        self,
        image: Image.Image,
        page_number: int = 1
    ):

        # -----------------------------------------------------
        # STEP 1: PREPROCESS IMAGE
        # -----------------------------------------------------

        processed_image = preprocess_image(
            image
        )

        # -----------------------------------------------------
        # STEP 2: FIRST TRY TESSERACT
        # -----------------------------------------------------

        result = self.ocr_engine.process(
            processed_image
        )

        tesseract_text = result["text"]
        tesseract_confidence = result["confidence"]

        # -----------------------------------------------------
        # STEP 3: CLASSIFY
        # -----------------------------------------------------

        document_classification = self.classify_document(
            tesseract_confidence
        )

        # -----------------------------------------------------
        # STEP 4: PRINTED DOCUMENT
        # -----------------------------------------------------

        if document_classification == "PRINTED":

            final_text = tesseract_text

            extraction_method = "tesseract"

        # -----------------------------------------------------
        # STEP 5: HANDWRITTEN / LOW CONFIDENCE
        # -----------------------------------------------------

        else:

            try:

                final_text = (
                    extract_handwritten_text_with_gemini(
                        image
                    )
                )

                extraction_method = (
                    "gemini_handwritten_ocr"
                )

            except Exception as e:

                # If Gemini fails, keep Tesseract result
                final_text = tesseract_text

                extraction_method = (
                    "tesseract_fallback"
                )

                print(
                    "Gemini OCR failed:",
                    str(e)
                )

        # -----------------------------------------------------
        # STEP 6: CREATE PAGE RESULT
        # -----------------------------------------------------

        page_result = OCRPageResult(
            page_number=page_number,

            raw_text=final_text,

            confidence=tesseract_confidence,

            words=result["words"],

            preprocessing_method=(
                "resize + grayscale + denoise + "
                "CLAHE + adaptive threshold"
            ),

            # Add these fields to your schema
            document_classification=(
                document_classification
            ),

            extraction_method=(
                extraction_method
            )
        )

        return page_result

    # ---------------------------------------------------------
    # PROCESS PDF
    # ---------------------------------------------------------

    def process_pdf(
        self,
        file_path: str
    ):

        pages = pdf_to_images(
            file_path
        )

        results = []

        for page in pages:

            result = self.process_image(
                page["image"],
                page["page_number"]
            )

            results.append(
                result
            )

        # -----------------------------------------------------
        # COMBINE TEXT
        # -----------------------------------------------------

        full_text = "\n\n".join(
            result.raw_text
            for result in results
        )

        # -----------------------------------------------------
        # CONFIDENCE
        # -----------------------------------------------------

        confidence_values = [
            result.confidence
            for result in results
        ]

        average_confidence = (
            sum(confidence_values)
            / len(confidence_values)
            if confidence_values
            else 0
        )

        # -----------------------------------------------------
        # DOCUMENT TYPE
        # -----------------------------------------------------

        classifications = [
            result.document_classification
            for result in results
        ]

        if all(
            c == "PRINTED"
            for c in classifications
        ):

            document_classification = "PRINTED"

        elif all(
            c == "HANDWRITTEN_OR_UNCLEAR"
            for c in classifications
        ):

            document_classification = (
                "HANDWRITTEN_OR_UNCLEAR"
            )

        else:

            document_classification = "MIXED"

        # -----------------------------------------------------
        # DOCUMENT RESULT
        # -----------------------------------------------------

        return OCRDocumentResult(
            filename=Path(file_path).name,

            document_type="pdf",

            total_pages=len(results),

            text=full_text,

            average_confidence=round(
                average_confidence,
                2
            ),

            pages=results,

            document_classification=(
                document_classification
            )
        )

    # ---------------------------------------------------------
    # PROCESS FILE
    # ---------------------------------------------------------

    def process_file(
        self,
        file_path: str
    ):

        extension = (
            Path(file_path)
            .suffix
            .lower()
        )

        # -----------------------------------------------------
        # PDF
        # -----------------------------------------------------

        if extension == ".pdf":

            return self.process_pdf(
                file_path
            )

        # -----------------------------------------------------
        # IMAGE
        # -----------------------------------------------------

        if extension in [
            ".jpg",
            ".jpeg",
            ".png",
            ".tif",
            ".tiff",
            ".webp"
        ]:

            image = Image.open(
                file_path
            ).convert("RGB")

            page_result = self.process_image(
                image
            )

            return OCRDocumentResult(
                filename=Path(
                    file_path
                ).name,

                document_type="image",

                total_pages=1,

                text=page_result.raw_text,

                average_confidence=(
                    page_result.confidence
                ),

                pages=[
                    page_result
                ],

                document_classification=(
                    page_result.document_classification
                )
            )

        raise ValueError(
            "Unsupported file type"
        )



kannada_ocr = OCRService()
