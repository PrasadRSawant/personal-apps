from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from fastapi.responses import StreamingResponse
from PIL import Image
from io import BytesIO
from app.core.dependencies import get_current_user

router = APIRouter()

@router.post("/resize", summary="Resize image by dimension and/or memory (quality)")
async def resize_image_endpoint(
    file: UploadFile = File(...), 
    width: int = 400, 
    height: int = 400, 
    quality: int = 80, # 1 to 100, affects JPEG size
    current_user: str = Depends(get_current_user) # Protected
):
    """Resizes an image using specified dimensions and quality."""
    if file.content_type not in ["image/jpeg", "image/png", "image/jpg"]:
        raise HTTPException(status_code=400, detail="Invalid image format.")
    
    try:
        image = Image.open(BytesIO(await file.read()))
        resized_image = image.resize((width, height))
        
        img_byte_arr = BytesIO()
        img_format = image.format if image.format in ['JPEG', 'PNG'] else 'JPEG'

        # Use quality only for JPEG to reduce file size (memory)
        if img_format == 'JPEG':
            resized_image.save(img_byte_arr, format=img_format, quality=quality)
        else: # PNG (for transparency)
            resized_image.save(img_byte_arr, format=img_format)
            
        img_byte_arr.seek(0)
        
        return StreamingResponse(
            img_byte_arr, 
            media_type=file.content_type,
            headers={"Content-Disposition": f"attachment; filename=resized-{file.filename}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image processing failed: {e}")

@router.post("/upscale", summary="Increase image dimensions (basic)")
async def upscale_image_endpoint(
    file: UploadFile = File(...), 
    scale_factor: float = 2.0, # e.g., double the size
    current_user: str = Depends(get_current_user) # Protected
):
    """Increases image dimensions by a scale factor."""
    # Basic implementation using resize. Real upscaling is much more complex (ML models).
    if file.content_type not in ["image/jpeg", "image/png", "image/jpg"]:
        raise HTTPException(status_code=400, detail="Invalid image format.")
        
    try:
        image = Image.open(BytesIO(await file.read()))
        new_width = int(image.width * scale_factor)
        new_height = int(image.height * scale_factor)
        
        upscaled_image = image.resize((new_width, new_height), resample=Image.BICUBIC)
        
        img_byte_arr = BytesIO()
        upscaled_image.save(img_byte_arr, format=image.format or 'JPEG')
        img_byte_arr.seek(0)
        
        return StreamingResponse(
            img_byte_arr, 
            media_type=file.content_type,
            headers={"Content-Disposition": f"attachment; filename=upscaled-{file.filename}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image upscaling failed: {e}")