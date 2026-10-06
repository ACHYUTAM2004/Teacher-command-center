from fastapi import FastAPI
import sentry_sdk

# Initialize Sentry for FastAPI error tracking
sentry_sdk.init(dsn="", traces_sample_rate=1.0)

app = FastAPI(
    title="Teacher Command Center API",
    version="1.0.0",
    docs_url="/api/v1/docs"
)

@app.get("/health")
async def health_check():
    return {"status": "ok"}