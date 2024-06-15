class BackendConfig:
    STORAGE_ACCESS_KEY="minioadmin"
    STORAGE_SECRET_KEY="minioadmin"
    STORAGE_ENDPOINT = "minio"
    INPUT_BUCKET_NAME = "video-uploads"
    OUTPUT_BUCKET_NAME = "output"
    FRONTEND_URL = "http://localhost:5000"
    PORT=5001