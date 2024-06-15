import os

class BackendConfig:
    STORAGE_ENDPOINT = os.getenv('MINIO_ENDPOINT', 'minio')
    STORAGE_PORT = int(os.getenv('MINIO_PORT', 9000))
    STORAGE_ACCESS_KEY = os.getenv('MINIO_ACCESS_KEY', 'minioadmin')
    STORAGE_SECRET_KEY = os.getenv('MINIO_SECRET_KEY', 'minioadmin')
    INPUT_BUCKET_NAME = 'video-uploads'
    OUTPUT_BUCKET_NAME = 'output'
    USE_SSL = os.getenv('MINIO_USE_SSL', 'false').lower() in ('true', '1')
    PORT = 5001