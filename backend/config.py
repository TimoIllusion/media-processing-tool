import os

class BackendConfig:
    PORT = os.getenv('BACKEND_PORT', 5001)
    STORAGE_ENDPOINT = os.getenv('MINIO_ENDPOINT', 'minio')
    STORAGE_PORT = int(os.getenv('MINIO_PORT', 9000))
    STORAGE_ACCESS_KEY = os.getenv('MINIO_ACCESS_KEY', 'minioadmin')
    STORAGE_SECRET_KEY = os.getenv('MINIO_SECRET_KEY', 'minioadmin')
    INPUT_BUCKET_NAME = os.getenv('INPUT_BUCKET_NAME', 'input')
    OUTPUT_BUCKET_NAME = os.getenv('OUTPUT_BUCKET_NAME', 'output')
    