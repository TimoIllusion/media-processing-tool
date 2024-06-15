import os
import zipfile
import io

from flask import Flask, render_template, request, jsonify, send_file
from minio import Minio
from minio.error import S3Error
import requests
from loguru import logger

from config import FrontendConfig

app = Flask(__name__)

logger.info(f"Connecting to MinIO at {FrontendConfig.STORAGE_HOST}")
minio_client = Minio(
    FrontendConfig.STORAGE_HOST,
    access_key=FrontendConfig.STORAGE_ACCESS_KEY,
    secret_key=FrontendConfig.STORAGE_SECRET_KEY,
    secure=False
)
logger.info("Connected to MinIO.")

# Ensure both buckets exist
for bucket in [FrontendConfig.INPUT_BUCKET_NAME, FrontendConfig.OUTPUT_BUCKET_NAME]:
    if not minio_client.bucket_exists(bucket):
        minio_client.make_bucket(bucket)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    files = request.files.getlist('file')
    for file in files:
        if file.filename == '':
            return jsonify({'error': 'No selected file'})
        if file:
            file_path = os.path.join("/tmp", file.filename)
            file.save(file_path)

            # Upload the file to MinIO
            minio_client.fput_object(FrontendConfig.INPUT_BUCKET_NAME, file.filename, file_path)
            os.remove(file_path)

    return jsonify({'message': 'Files uploaded successfully. Ready to be processed.'})

@app.route('/process/<filename>', methods=['POST'])
def process_file(filename):
    try:
        response = requests.post(f"{FrontendConfig.BACKEND_URL}/process-media-file", json={'filename': filename})
        
        # Check if the response contains valid JSON
        try:
            response_data = response.json()
        except ValueError as e:
            logger.error(f"Error decoding JSON response: {e}")
            return jsonify({'error': 'Invalid response from backend.'})

        success = response_data.get('success', False)
        if success:
            return jsonify({'message': 'File processing started successfully'})
        else:
            return jsonify({'error': 'File processing failed'})

    except S3Error as e:
        logger.error(f"S3Error: {e}")
        return jsonify({'error': str(e)})
    except Exception as e:
        logger.error(f"Error: {e}")
        return jsonify({'error': 'An error occurred while processing the file.'})

@app.route('/status/<filename>', methods=['GET'])
def check_status(filename):
    response = requests.get(f"{FrontendConfig.BACKEND_URL}/status/{filename}")
    # just relay response from backend
    return jsonify(response.json())

@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    try:
        file_path = os.path.join("/tmp", filename)
        minio_client.fget_object(FrontendConfig.OUTPUT_BUCKET_NAME, filename, file_path)
        return send_file(file_path, as_attachment=True)
    except S3Error:
        return jsonify({'error': 'File not found'})

@app.route('/list-files', methods=['GET'])
def list_files():
    objects = minio_client.list_objects(FrontendConfig.INPUT_BUCKET_NAME)
    files = [obj.object_name for obj in objects]
    return jsonify(files)

@app.route('/list-results', methods=['GET'])
def list_results():
    objects = minio_client.list_objects(FrontendConfig.OUTPUT_BUCKET_NAME)
    results = [obj.object_name for obj in objects]
    return jsonify(results)

@app.route('/download-all-results', methods=['GET'])
def download_all_results():
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        objects = minio_client.list_objects(FrontendConfig.OUTPUT_BUCKET_NAME)
        for obj in objects:
            file_data = minio_client.get_object(FrontendConfig.OUTPUT_BUCKET_NAME, obj.object_name)
            zip_file.writestr(obj.object_name, file_data.read())

    zip_buffer.seek(0)
    return send_file(zip_buffer, mimetype='application/zip', as_attachment=True, download_name='all_results.zip')

@app.route('/delete-input', methods=['DELETE'])
def delete_all_files():
    try:
        objects_to_delete = minio_client.list_objects(FrontendConfig.INPUT_BUCKET_NAME)
        for obj in objects_to_delete:
            minio_client.remove_object(FrontendConfig.INPUT_BUCKET_NAME, obj.object_name)

        return jsonify({'message': 'All input files deleted successfully'})
    except S3Error as e:
        return jsonify({'error': str(e)})

@app.route('/delete-output', methods=['DELETE'])
def delete_all_output_files():
    try:
        results_to_delete = minio_client.list_objects(FrontendConfig.OUTPUT_BUCKET_NAME)
        for obj in results_to_delete:
            minio_client.remove_object(FrontendConfig.OUTPUT_BUCKET_NAME, obj.object_name)

        return jsonify({'message': 'All results deleted successfully'})
    except S3Error as e:
        return jsonify({'error': str(e)})
    
@app.route('/reset', methods=['GET'])
def reset():
    try:
        requests.get(f"{FrontendConfig.BACKEND_URL}/reset")
        return jsonify({'message': 'Backend reset successfully'})
    except Exception as e:
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    app.run(debug=True)
