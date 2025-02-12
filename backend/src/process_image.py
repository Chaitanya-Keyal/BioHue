import cv2
import numpy as np


def extract_prominent_circle(image: bytes) -> cv2.typing.MatLike | None:
    img = cv2.imdecode(np.frombuffer(image, np.uint8), cv2.IMREAD_COLOR)
    h, w, _ = img.shape
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    blurred = cv2.GaussianBlur(gray, (9, 9), 2)

    min_radius = int(np.sqrt(0.1 * (h * w / np.pi)))  # Minimum 10% of image area
    max_radius = int(np.sqrt(0.6 * (h * w / np.pi)))  # Maximum 60% of image area

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
        return None

    circles = np.uint16(np.around(circles))
    x, y, radius = circles[0][0]

    mask = np.zeros((h, w), dtype=np.uint8)
    cv2.circle(mask, (x, y), radius, 255, -1)
    extracted = cv2.bitwise_and(img, img, mask=mask)

    x1, y1, x2, y2 = (
        max(x - radius, 0),
        max(y - radius, 0),
        min(x + radius, w),
        min(y + radius, h),
    )

    circle = extracted[y1:y2, x1:x2]
    cv2.imwrite("detected_circle.png", circle)

    return circle


def compute_rg_ratio(image: cv2.typing.MatLike) -> float:
    image = image.astype(np.float32)
    b, g, r = cv2.split(image)
    g[g == 0] = 1  # Avoid division by zero
    return float(np.mean(r) / np.mean(g))


def classify_result(rg_ratio: float) -> str:
    if rg_ratio < 1.5:
        return "Negative"
    elif rg_ratio > 2:
        return "Positive"
    else:
        return "Moderate"
