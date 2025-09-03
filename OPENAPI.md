# KYC-OCR API Documentation

## Overview

The **KYC-OCR API** provides endpoints to process images using the GPT-4 Vision model, extract structured data, and retrieve processing results asynchronously. The API is secured via API Key authentication and uses Celery with Redis for background task processing.

---

## Base URL

```
http://<host>:8000
```

---

## Authentication

All endpoints require an API key to be provided in the request header:

```
X-API-Key: <your-api-key>
```

You must set the environment variable `API_KEY` on the server to define the valid key.

---

## Endpoints

### 1. Queue Image for Processing

**POST** `/read_text`

Queue an image for processing using the GPT-4 Vision model. Returns a task ID for tracking the processing status.

#### Request
- **Headers:**
    - `X-API-Key: <your-api-key>`
- **Body (multipart/form-data):**
    - `image`: Image file to be processed (required)

#### Response
- **202 Accepted**
    - JSON: `{ "id": "<task_id>" }`
- **500 Internal Server Error**
    - JSON: `{ "detail": "Failed to queue image: <error>" }`

#### Example
```bash
curl -X POST "http://localhost:8000/read_text" \
  -H "X-API-Key: <your-api-key>" \
  -F "image=@/path/to/image.jpg"
```

---

### 2. Get Task Status and Result

**GET** `/id?task_id=<task_id>`

Get the status and result of a processing task.

#### Request
- **Headers:**
    - `X-API-Key: <your-api-key>`
- **Query Parameters:**
    - `task_id`: The ID returned by `/read_text` (required)

#### Response
- **202 Accepted** (Task is processing)
    - JSON: `{ "status": "Processing" }`
- **200 OK** (Task completed successfully)
    - JSON: `<result from GPT-4 Vision, typically a structured JSON document>`
- **400 Bad Request** (Task failed or invalid)
    - JSON: `{ "error": "<error message>" }`
- **404 Not Found** (Task ID not found)
    - JSON: `{ "error": "Task ID not found" }`

#### Example
```bash
curl -X GET "http://localhost:8000/id?task_id=<task_id>" \
  -H "X-API-Key: <your-api-key>"
```

---

## Error Codes

- `401 Unauthorized`: Invalid or missing API key
- `400 Bad Request`: Task failed or invalid request
- `404 Not Found`: Task ID not found
- `500 Internal Server Error`: Server error

---

## Requirements

- Python 3.9+
- FastAPI
- Celery
- Redis
- OpenAI Python SDK
- python-dotenv

See `requirements.txt` for full dependency list.

---

## Running the API

You can run the API using Docker (recommended):

```bash
docker build -t kyc-ocr .
docker run -e API_KEY=<your-api-key> -e OPENAI_API_KEY=<your-openai-key> -p 8000:8000 kyc-ocr
```

Or manually:

```bash
export API_KEY=<your-api-key>
export OPENAI_API_KEY=<your-openai-key>
redis-server &
celery -A celery_app worker --loglevel=info &
python app.py
```

---

## Notes
- The API expects images as file uploads (not base64 strings).
- The result from `/id` will be a JSON document as returned by GPT-4 Vision, or an error message.
- The API is asynchronous: always check the task status before expecting a result. 
