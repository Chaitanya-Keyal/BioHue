import cv2
import numpy as np
from src.config import Thresholds


def extract_prominent_region(
    image: bytes,
    saturation_thresh: int = 50,
    morph_kernel_size: int = 5,
    min_area_ratio: float = 0.001,
    glare_thresh: int = 180,
) -> cv2.typing.MatLike | None:
    """
    Extracts the most prominent colored region from an image, replaces glare pixels with
    the average non-glare color, and returns a circular crop.

    The function:
      1. Detects the most saturated region.
      2. Extracts its bounding box.
      3. Replaces glare pixels (where brightness exceeds glare_thresh) with the average color
         computed from non-glare pixels.
      4. Applies a circular mask so that only a perfect circle remains opaque.
      5. Calculates the area of this circular region relative to the whole image.

    Args:
        image (bytes): The input image in bytes.
        saturation_thresh (int): Threshold for the saturation channel (0-255).
        morph_kernel_size (int): Size of the structuring element for morphological operations.
        min_area_ratio (float): Minimum area ratio of a contour to be considered valid.
        glare_thresh (int): Brightness threshold (0-255) above which pixels are considered glare.

    Returns:
        region (cv2.typing.MatLike | None): The circular region with glare pixels replaced by the average color.
    """

    img = cv2.imdecode(np.frombuffer(image, np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        return None, None

    h, w, _ = img.shape

    # Convert image to HSV color space
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    s_channel = hsv[:, :, 1]
    s_blur = cv2.GaussianBlur(s_channel, (5, 5), 0)
    _, mask = cv2.threshold(s_blur, saturation_thresh, 255, cv2.THRESH_BINARY)

    # Clean up the mask with morphological operations
    kernel = cv2.getStructuringElement(
        cv2.MORPH_ELLIPSE, (morph_kernel_size, morph_kernel_size)
    )
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=2)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)

    # Find contours in the mask
    contours_info = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = contours_info[0] if len(contours_info) == 2 else contours_info[1]
    if not contours:
        return None, None

    # Select the largest contour
    largest_contour = max(contours, key=cv2.contourArea)
    contour_area = cv2.contourArea(largest_contour)
    image_area = h * w
    if contour_area < min_area_ratio * image_area:
        return None, None

    # Create an alpha mask for the largest contour and add it to the image.
    mask_colored = np.zeros((h, w), dtype=np.uint8)
    cv2.drawContours(mask_colored, [largest_contour], -1, 255, thickness=cv2.FILLED)
    img_with_alpha = cv2.cvtColor(img, cv2.COLOR_BGR2BGRA)
    img_with_alpha[:, :, 3] = mask_colored

    # Crop the region using the bounding rectangle of the largest contour.
    x, y, w_box, h_box = cv2.boundingRect(largest_contour)
    region = img_with_alpha[y : y + h_box, x : x + w_box].copy()

    # Glare removal:
    # Convert the region's RGB channels (ignoring alpha) to HSV for brightness inspection
    region_rgb = region[:, :, :3]
    region_hsv = cv2.cvtColor(region_rgb, cv2.COLOR_BGR2HSV)
    v_channel = region_hsv[:, :, 2]
    glare_mask = v_channel >= glare_thresh

    # Compute the average color of non-glare pixels
    non_glare_pixels = region_rgb[~glare_mask]
    if non_glare_pixels.size > 0:
        avg_color = np.mean(non_glare_pixels, axis=0).astype(np.uint8)
    else:
        avg_color = np.array([0, 0, 0], dtype=np.uint8)
    # Replace glare pixels with the average color
    region[glare_mask, :3] = avg_color

    # Create a circular mask based on the region's dimensions
    h_region, w_region = region.shape[:2]
    circle_mask = np.zeros((h_region, w_region), dtype=np.uint8)
    c_x, c_y = w_region // 2, h_region // 2
    radius = int(min(w_region, h_region) / 2)
    cv2.circle(circle_mask, (c_x, c_y), radius, 255, thickness=-1)

    # Apply the circular mask to the alpha channel so that only the circle remains opaque
    region[:, :, 3] = circle_mask

    return region


def calculate_hue_angle(r: float, g: float, b: float) -> float:
    """
    Calculate the hue angle (0-360 degrees) from RGB values.

    Args:
        r: Red channel mean (0-255)
        g: Green channel mean (0-255)
        b: Blue channel mean (0-255)

    Returns:
        Hue angle in degrees (0-360)
    """
    # Normalize to 0-1 range
    r_norm = r / 255.0
    g_norm = g / 255.0
    b_norm = b / 255.0

    c_max = max(r_norm, g_norm, b_norm)
    c_min = min(r_norm, g_norm, b_norm)
    delta = c_max - c_min

    # If delta is 0, the color is grayscale (no hue)
    if delta == 0:
        return 0.0

    # Calculate hue based on which channel is max
    if c_max == r_norm:
        hue = 60.0 * (((g_norm - b_norm) / delta) % 6)
    elif c_max == g_norm:
        hue = 60.0 * (((b_norm - r_norm) / delta) + 2)
    else:  # c_max == b_norm
        hue = 60.0 * (((r_norm - g_norm) / delta) + 4)

    # Ensure hue is in 0-360 range
    if hue < 0:
        hue += 360.0

    return hue


def compute_metric(image: cv2.typing.MatLike, expression: str) -> float:
    image = image.astype(np.float32)
    b, g, r, _ = cv2.split(image)

    # Avoid division by zero
    g = np.where(g == 0, 1, g)
    b = np.where(b == 0, 1, b)
    r = np.where(r == 0, 1, r)

    r_mean = float(np.mean(r))
    g_mean = float(np.mean(g))
    b_mean = float(np.mean(b))

    return float(
        eval(
            expression.strip().lower(),
            {
                "r": r_mean,
                "g": g_mean,
                "b": b_mean,
                "hue_angle": lambda r, g, b: calculate_hue_angle(r, g, b),
            },
        )
    )


def classify_result(value: float, thresholds: Thresholds) -> str:
    if eval(thresholds.negative, {"value": value}):
        return "Negative"
    elif eval(thresholds.positive, {"value": value}):
        return "Positive"
    elif thresholds.moderate and eval(thresholds.moderate, {"value": value}):
        return "Moderate"
    else:
        return "Invalid"
