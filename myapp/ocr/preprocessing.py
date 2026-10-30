import cv2
import numpy as np
from PIL import Image


def pil_to_cv(image: Image.Image) -> np.ndarray:
    """
    Convert PIL image to OpenCV BGR format.
    """
    rgb = np.array(image.convert("RGB"))
    return cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)


def cv_to_pil(image: np.ndarray) -> Image.Image:
    """
    Convert OpenCV BGR image to PIL image.
    """
    rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    return Image.fromarray(rgb)


def resize_for_ocr(image: np.ndarray, min_width: int = 1600) -> np.ndarray:
    """
    Increase image resolution when the source is too small.
    """

    height, width = image.shape[:2]

    if width >= min_width:
        return image

    scale = min_width / width

    new_width = int(width * scale)
    new_height = int(height * scale)

    return cv2.resize(
        image,
        (new_width, new_height),
        interpolation=cv2.INTER_CUBIC
    )


def grayscale(image: np.ndarray) -> np.ndarray:
    """
    Convert image to grayscale.
    """
    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)


def denoise(image: np.ndarray) -> np.ndarray:
    """
    Remove small noise while preserving characters.
    """
    return cv2.fastNlMeansDenoising(
        image,
        None,
        h=10,
        templateWindowSize=7,
        searchWindowSize=21
    )


def enhance_contrast(image: np.ndarray) -> np.ndarray:
    """
    Improve local contrast using CLAHE.
    """

    clahe = cv2.createCLAHE(
        clipLimit=2.0,
        tileGridSize=(8, 8)
    )

    return clahe.apply(image)


def adaptive_threshold(image: np.ndarray) -> np.ndarray:
    """
    Convert image to binary form.
    """

    return cv2.adaptiveThreshold(
        image,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        31,
        11
    )


def preprocess_image(image: Image.Image) -> Image.Image:
    """
    Complete preprocessing pipeline.
    """

    cv_image = pil_to_cv(image)

    # 1. Increase resolution
    cv_image = resize_for_ocr(cv_image)

    # 2. Grayscale
    gray = grayscale(cv_image)

    # 3. Denoise
    gray = denoise(gray)

    # 4. Contrast enhancement
    gray = enhance_contrast(gray)

    # 5. Threshold
    binary = adaptive_threshold(gray)

    return cv_to_pil(binary)