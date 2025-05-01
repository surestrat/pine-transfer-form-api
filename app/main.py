import logging
import traceback
import os
from fastapi import FastAPI, Depends, BackgroundTasks, Body, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.schemas import SubmissionData
from app.services import submit_form_service, get_database, check_appwrite_health
from app.email_service import send_email
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("api.log")],
)
logger = logging.getLogger("pine-api")

# Load environment variables
load_dotenv()

app = FastAPI(title="Pine API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("ALLOWED_ORIGIN", "http://localhost:3000")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/submit-form")
async def submit_form(
    background_tasks: BackgroundTasks,
    submission: SubmissionData = Body(...),
    database=Depends(get_database),
):
    try:
        return await submit_form_service(
            submission=submission,
            background_tasks=background_tasks,
            database=database,
            send_email=send_email,
        )
    except Exception as e:
        error_detail = str(e)
        stack_trace = traceback.format_exc()
        logger.error(f"Error processing form submission: {error_detail}")
        logger.error(f"Stack trace: {stack_trace}")
        raise HTTPException(status_code=500, detail=error_detail)


@app.get("/health")
async def health_check():
    """
    Health check endpoint that verifies:
    - Application is running
    - Appwrite connection is healthy
    """
    try:
        result = check_appwrite_health()
        appwrite_ok = result[0]
        appwrite_msg = result[1]
        status = "healthy" if appwrite_ok else "degraded"

        response = {
            "status": status,
            "appwrite": {
                "ok": appwrite_ok,
                "message": appwrite_msg,
            },
        }

        # Add the optional metadata if available
        if len(result) > 2:
            response["appwrite"]["metadata"] = result[2]

        return response
    except Exception as e:
        return {
            "status": "unhealthy",
            "appwrite": {
                "ok": False,
                "message": str(e),
            },
        }


@app.get("/ping")
async def ping():
    return {"message": "Pine API is running"}


@app.options("/{path:path}")
async def options_route(path: str):
    return JSONResponse(
        content={"message": "OK"},
        headers={
            "Access-Control-Allow-Origin": os.getenv("ALLOWED_ORIGIN", "*"),
            "Access-Control-Allow-Methods": "POST, GET, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization, Accept",
            "Access-Control-Max-Age": "86400",
        },
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    logger.error(f"HTTP error: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {str(exc)}")
    logger.error(traceback.format_exc())
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)},
    )


if __name__ == "__main__":
    import uvicorn

    try:
        logger.info("Starting Pine API server")
        uvicorn.run("app.main:app", host="0.0.0.0", port=4000, reload=True)
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        logger.error(traceback.format_exc())
