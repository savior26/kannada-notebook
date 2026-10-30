import pymupdf

from PIL import Image
import io


def pdf_to_images(pdf_path: str, dpi: int = 250):

    document = pymupdf.open(pdf_path)

    images = []

    zoom = dpi / 72

    matrix = pymupdf.Matrix(zoom, zoom)

    for page_number, page in enumerate(document):

        pixmap = page.get_pixmap(
            matrix=matrix,
            alpha=False
        )

        image_bytes = pixmap.tobytes("png")

        image = Image.open(
            io.BytesIO(image_bytes)
        ).convert("RGB")

        images.append(
            {
                "page_number": page_number + 1,
                "image": image
            }
        )

    document.close()

    return images