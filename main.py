from backend.main import app


@app.get("/api/health")
def health_check():
    return {"status": "Slide2Study Backend Active"}
