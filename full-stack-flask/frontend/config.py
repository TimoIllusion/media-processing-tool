import os

MINIO_ENDPOINT = os.getenv('MINIO_ENDPOINT', 'minio')
MINIO_PORT = int(os.getenv('MINIO_PORT', 9000))
MINIO_ACCESS_KEY = os.getenv('MINIO_ACCESS_KEY', 'minioadmin')
MINIO_SECRET_KEY = os.getenv('MINIO_SECRET_KEY', 'minioadmin')
INPUT_BUCKET_NAME = os.getenv('INPUT_BUCKET_NAME', 'input')
OUTPUT_BUCKET_NAME = os.getenv('OUTPUT_BUCKET_NAME', 'output')
BACKEND_URL = os.getenv('BACKEND_URL', 'backend:5001')
