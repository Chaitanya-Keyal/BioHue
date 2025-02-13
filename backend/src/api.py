import base64

import cv2
from fastapi import APIRouter, HTTPException, UploadFile, status
from fastapi.responses import JSONResponse
from src.process_image import (
    classify_result,
    compute_rg_ratio,
    extract_prominent_circle,
)

router = APIRouter()


@router.post("/classify")
async def classify_image(image: UploadFile):
    contents = await image.read()

    circle, area = extract_prominent_circle(contents)
    if circle is None or area is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No prominent circle detected in the image",
        )

    rg_ratio = compute_rg_ratio(circle)
    result = classify_result(rg_ratio)

    _, circle_buffer = cv2.imencode(".png", circle)
    circle_base64 = base64.b64encode(circle_buffer).decode("utf-8")

    return JSONResponse(
        {
            "result": result,
            "rg_ratio": rg_ratio,
            "circle": circle_base64,
            "area": area,
        }
    )
