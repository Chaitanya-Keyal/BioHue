import base64
import io
import traceback
from datetime import datetime
from typing import List

import cv2
from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from fastapi.responses import JSONResponse
from src.database import Analysis, File, Image, User, fs, images_collection
from src.process_image import (
    classify_result,
    compute_rg_ratio,
    extract_prominent_circle,
)
from src.routes.users import get_current_user

router = APIRouter()


@router.post("")
async def upload_image(image: UploadFile, user: User = Depends(get_current_user)):
    try:
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

        original_image_id = await fs.upload_from_stream(image.filename, contents)
        processed_image_id = await fs.upload_from_stream(
            f"processed_{image.filename}", circle_buffer.tobytes()
        )

        analysis = Analysis(substrate="CPRG", value=rg_ratio, result=result)

        image_data = Image(
            user_id=user.id,
            original_image=File(_id=str(original_image_id)),
            processed_image=File(_id=str(processed_image_id)),
            processed_image_area=area,
            analysis=analysis,
            created_at=datetime.now(),
        )

        await images_collection.insert_one(
            image_data.model_dump(
                by_alias=True,
                exclude_none=True,
            )
        )

        image_data.processed_image.base64 = base64.b64encode(
            circle_buffer.tobytes()
        ).decode()

        return JSONResponse(
            image_data.model_dump(mode="json", exclude={"original_image", "user_id"})
        )

    except Exception as e:
        print(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get("")
async def get_images(user: User = Depends(get_current_user)):
    images = await images_collection.find({"user_id": user.id}).to_list(None)

    images_with_data: List[Image] = []
    for _image in images:
        image = Image(**_image)

        original_image = io.BytesIO()
        await fs.download_to_stream(ObjectId(image.original_image.id), original_image)
        image.original_image.base64 = base64.b64encode(
            original_image.getvalue()
        ).decode()

        if image.processed_image:
            processed_image = io.BytesIO()
            await fs.download_to_stream(
                ObjectId(image.processed_image.id), processed_image
            )
            image.processed_image.base64 = base64.b64encode(
                processed_image.getvalue()
            ).decode()

        images_with_data.append(image)

    images_with_data.sort(key=lambda image: image.created_at, reverse=True)

    return JSONResponse(
        [
            image.model_dump(mode="json", exclude={"user_id"})
            for image in images_with_data
        ]
    )
