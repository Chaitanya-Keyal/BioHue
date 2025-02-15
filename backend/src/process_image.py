import cv2
import numpy as np
from src.config import Thresholds


def extract_prominent_circle(
    image: bytes,
) -> tuple[cv2.typing.MatLike | None, float | None]:
    img = cv2.imdecode(np.frombuffer(image, np.uint8), cv2.IMREAD_COLOR)
    h, w, _ = img.shape
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    blurred = cv2.GaussianBlur(gray, (9, 9), 2)

    min_radius = int(np.sqrt(0.025 * (h * w / np.pi)))  # Minimum 2.5% of image area
    max_radius = int(np.sqrt(0.75 * (h * w / np.pi)))  # Maximum 75% of image area

    circles = cv2.HoughCircles(
        blurred,
        cv2.HOUGH_GRADIENT,
        dp=1,
        minDist=max_radius,
        param1=50,
        param2=30,
        minRadius=min_radius,
        maxRadius=max_radius,
    )

    if circles is None:
        return None, None

    circles = np.uint16(np.around(circles))
    x, y, radius = circles[0][0]

    mask = np.zeros((h, w, 4), dtype=np.uint8)
    cv2.circle(mask, (x, y), radius, (255, 255, 255, 255), -1)
    img_with_alpha = cv2.cvtColor(img, cv2.COLOR_BGR2BGRA)
    extracted = cv2.bitwise_and(img_with_alpha, mask)

    x1, y1, x2, y2 = (
        max(x - radius, 0),
        max(y - radius, 0),
        min(x + radius, w),
        min(y + radius, h),
    )

    circle = extracted[y1:y2, x1:x2]

    circle_area = np.pi * (radius**2)
    image_area = h * w
    percent_circle = (circle_area / image_area) * 100

    return circle, percent_circle


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
    if value < thresholds.negative:
        return "Negative"
    elif value > thresholds.positive:
        return "Positive"
    else:
        return "Moderate"
