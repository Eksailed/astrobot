import os
import uvicorn

if __name__ == "__main__":
    # Render sets PORT environment variable (e.g., 10000)
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("api.main:app", host="0.0.0.0", port=port, log_level="info")
