from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from fastapi.responses import JSONResponse
import os
import uuid
from image_processing import encode_image, get_image_analysis, process_response
from celery_app import celery_app
from auth import get_api_key
from blur_check import image_preops
import json
from openai import OpenAI
import base64

# Constants
UPLOAD_DIR = 'uploads'
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Initialize FastAPI app
app = FastAPI(
    title="GPT-4 Vision Image Processing",
    description="API for processing images using GPT-4 Vision model",
    version="1.0.0"
)

@celery_app.task(name='image_processing.process_image_task', 
                bind=True,
                max_retries=3,
                default_retry_delay=60)
def process_image_task(self, image_path: str):
    """
    Celery task to process an image using GPT-4 Vision model.
    """
    try:
        # Run pre-processing
        preops_result, preops_error = image_preops(image_path)
        if preops_result is None:
            # Store error for retrieval with 422 code
            return {"error": preops_error, "status_code": 422}

        # Encode the processed image (JPEG bytes) to base64
        encoded_image = encode_image(preops_result)
        openai_response = get_image_analysis(encoded_image)
        result = process_response(openai_response)
        return result
    except Exception as e:
        try:
            self.retry(exc=e)
        except self.MaxRetriesExceededError:
            return {"error": f"Image processing failed after 3 retries: {str(e)}", "status_code": 500}
    finally:
        try:
            os.remove(image_path)
        except FileNotFoundError:
            pass

@app.post("/read_text")
async def process_image(
    image: UploadFile = File(...),
    api_key: str = Depends(get_api_key)
):
    """
    Queue an image for processing using GPT-4 Vision model.
    Returns a task ID for tracking the processing status.
    """
    try:
        # Save the uploaded image to disk
        task_id = str(uuid.uuid4())
        image_path = os.path.join(UPLOAD_DIR, f"{task_id}_{image.filename}")
        with open(image_path, "wb") as f:
            f.write(await image.read())
        # Queue the task
        task = process_image_task.apply_async(args=[image_path], task_id=task_id)
        return JSONResponse(
            status_code=202,
            content={"id": task_id}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to queue image: {str(e)}")

@app.get("/id")
async def get_task_status(
    task_id: str,
    api_key: str = Depends(get_api_key)
):
    """
    Get the status and result of a processing task.
    """
    try:
        task = celery_app.AsyncResult(task_id)
        # Check task state
        if task.state == 'PENDING':
            return JSONResponse(
                status_code=202,
                content={"status": "Processing"}
            )
        elif task.state == 'SUCCESS':
            result = task.result
            if isinstance(result, dict) and result.get("status_code") == 422:
                return JSONResponse(
                    status_code=422,
                    content={"error": result.get("error")}
                )
            return JSONResponse(
                status_code=200,
                content=result
            )
        elif task.state == 'FAILURE':
            return JSONResponse(
                status_code=500,
                content={"error": str(task.result)}
            )
        else:
            return JSONResponse(
                status_code=404,
                content={"error": "Task ID not found"}
            )
    except Exception as e:
        return JSONResponse(
            status_code=400,
            content={"error": str(e)}
        )

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
