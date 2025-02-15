import base64
import hashlib
import io
import traceback
from datetime import datetime
from typing import List

import cv2
from bson import ObjectId
from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile, status
from fastapi.responses import JSONResponse, Response
from src.config import settings
from src.database import Analysis, File, Image, User, fs, images_collection
from src.process_image import classify_result, compute_metric, extract_prominent_region
from src.routes.users import get_current_user

router = APIRouter(prefix="/images")

SUBSTRATES_CONFIG = settings.substrates


@router.post("")
async def upload_image(
    image: UploadFile,
    substrate: str = Form(...),
    user: User = Depends(get_current_user),
):
    try:
        if substrate not in SUBSTRATES_CONFIG:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid substrate",
            )

        contents = await image.read()

        md5_hash = hashlib.md5(contents).hexdigest()
        existing_image = await images_collection.find_one(
            {
                "md5_hash": md5_hash,
                "user_id": user.id,
                "analysis.substrate": substrate,
            }
        )
        if existing_image:
            return JSONResponse(
                status_code=status.HTTP_409_CONFLICT,
                content={
                    "detail": "This request has already been processed",
                    "image_id": str(existing_image["_id"]),
                },
            )

        region, area = extract_prominent_region(contents)
        if region is None or area is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No prominent circle detected in the image",
            )

        try:
            value = compute_metric(region, SUBSTRATES_CONFIG[substrate].expression)
            result = classify_result(value, SUBSTRATES_CONFIG[substrate].thresholds)
        except Exception as e:
            raise Exception(f"Error in substrate's configuration: {str(e)}")

        _, region_buffer = cv2.imencode(".png", region)

        original_image_id = await fs.upload_from_stream(image.filename, contents)
        processed_image_id = await fs.upload_from_stream(
            f"processed_{image.filename}", region_buffer.tobytes()
        )

        analysis = Analysis(substrate=substrate, value=value, result=result)

        image_data = Image(
            user_id=user.id,
            md5_hash=md5_hash,
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
            region_buffer.tobytes()
        ).decode()

        return JSONResponse(
            image_data.model_dump(mode="json", exclude={"original_image", "user_id"})
        )

    except HTTPException as http_exc:
        raise http_exc
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


@router.delete("/{image_id}")
async def delete_image(image_id: str, user: User = Depends(get_current_user)):
    image = await images_collection.find_one({"_id": image_id})
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found",
        )

    if image["user_id"] != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to delete this image",
        )

    image = Image(**image)
    await images_collection.delete_one({"_id": image_id})
    await fs.delete(ObjectId(image.original_image.id))
    if image.processed_image:
        await fs.delete(ObjectId(image.processed_image.id))

    return Response(status_code=status.HTTP_204_NO_CONTENT)
