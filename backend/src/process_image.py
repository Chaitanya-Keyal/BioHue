import cv2
import numpy as np
from src.config import Thresholds


def extract_prominent_region(
    image: bytes,
    saturation_thresh: int = 50,
    morph_kernel_size: int = 5,
    min_area_ratio: float = 0.001,
) -> tuple[cv2.typing.MatLike | None, float | None]:
    """
    Extracts the most prominent colored region from an image.

    Assumes that the region of interest is more saturated than other areas in the image.

    Args:
        image (bytes): The input image in bytes.
        saturation_thresh (int): Threshold for the saturation channel (0-255).
        morph_kernel_size (int): Size of the structuring element for morphological operations.
        min_area_ratio (float): Minimum area ratio of a contour to be considered valid.

    Returns:
        tuple: A tuple containing the cropped region with an alpha channel (colored region opaque,
               rest transparent) and the percentage area of the region relative to the whole image.
               Returns (None, None) if no valid region is found.
    """

    img = cv2.imdecode(np.frombuffer(image, np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        return None, None

    h, w, _ = img.shape

    # Convert image to HSV color space
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    s_channel = hsv[:, :, 1]

    # Apply a slight Gaussian blur to reduce noise in the saturation channel
    s_blur = cv2.GaussianBlur(s_channel, (5, 5), 0)

    # Threshold the saturation channel to get regions with significant color
    _, mask = cv2.threshold(s_blur, saturation_thresh, 255, cv2.THRESH_BINARY)

    # Define a structuring element and perform morphological operations to clean up the mask
    kernel = cv2.getStructuringElement(
        cv2.MORPH_ELLIPSE, (morph_kernel_size, morph_kernel_size)
    )
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=2)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)

    # Find contours in the cleaned mask
    contours_info = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = contours_info[0] if len(contours_info) == 2 else contours_info[1]
    if not contours:
        return None, None

    # Select the largest contour
    largest_contour = max(contours, key=cv2.contourArea)
    contour_area = cv2.contourArea(largest_contour)
    image_area = h * w

    # Filter out contours that are too small relative to the image area
    if contour_area < min_area_ratio * image_area:
        return None, None

    # Create a mask for the largest colored region
    mask_colored = np.zeros((h, w), dtype=np.uint8)
    cv2.drawContours(mask_colored, [largest_contour], -1, 255, thickness=cv2.FILLED)

    # Convert original image to BGRA (to add an alpha channel)
    img_with_alpha = cv2.cvtColor(img, cv2.COLOR_BGR2BGRA)
    # Set the alpha channel using the mask (colored area opaque, rest transparent)
    img_with_alpha[:, :, 3] = mask_colored

    x, y, w_box, h_box = cv2.boundingRect(largest_contour)
    region = img_with_alpha[y : y + h_box, x : x + w_box]
    percent_region = (contour_area / image_area) * 100

    return region, percent_region


def compute_metric(image: cv2.typing.MatLike, expression: str) -> float:
    image = image.astype(np.float32)
    b, g, r, _ = cv2.split(image)

    # Avoid division by zero
    g = np.where(g == 0, 1, g)
    b = np.where(b == 0, 1, b)
    r = np.where(r == 0, 1, r)

    return float(
        eval(
            expression.strip().lower(),
            {"r": np.mean(r), "g": np.mean(g), "b": np.mean(b)},
        )
    )


def classify_result(value: float, thresholds: Thresholds) -> str:
    if eval(thresholds.negative, {"value": value}):
        return "Negative"
    elif eval(thresholds.positive, {"value": value}):
        return "Positive"
    else:
        return "Moderate"
