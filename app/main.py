from fastapi import FastAPI
app=FastAPI(
    title="url-shortener",
    version="1.0.0",
    description="aA PRODUCTION GRADE MULTI-TENANT URL_SHORTENER",
)
@app.get("/health")
async def health():
    return{"status":"ok", "message":"service is alive"}
