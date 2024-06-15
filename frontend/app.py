import os
import zipfile
import io

from flask import Flask, render_template, request, jsonify, send_file
from minio import Minio
from minio.error import S3Error
import requests

from frontend.config import FrontendConfig

app = Flask(__name__)

# MinIO client configuration
minio_client = Minio(
    FrontendConfig.BACKEND_STORAGE_URL,
    access_key=FrontendConfig.STORAGE_ACCESS_KEY,
    secret_key=FrontendConfig.STORAGE_SECRET_KEY,
    secure=False
)

PROCESSING_STATUS = {}

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
            
            # Initialize processing status
            PROCESSING_STATUS[file.filename] = {'status': 'Uploaded'}

    return jsonify({'message': 'Files uploaded successfully. Ready to be processed.'})

@app.route('/process/<filename>', methods=['POST'])
def process_file(filename):
    try:
        # send a request to the backend to process the video, with filename and processing_Status
        
        response = requests.post(f'{FrontendConfig.BACKEND_URL}/process-video', files={'file': open(f'/tmp/{filename}', 'rb')})
        success = response.status_code == 200

        if success:
            PROCESSING_STATUS[filename] = {'status': 'Processing'}
        else:
            PROCESSING_STATUS[filename] = {'status': 'Failed'}

        return jsonify({'message': 'File processing started successfully'})
            
        
        
        if success:
            return jsonify({'message': 'File processed successfully'})
        else:
            return jsonify({'error': 'File processing failed'})        

    except S3Error as e:
        return jsonify({'error': str(e)})

@app.route('/status/<filename>', methods=['GET'])
def check_status(filename):
    status = PROCESSING_STATUS.get(filename, {'status': 'File not found'})
    return jsonify(status)

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

        PROCESSING_STATUS.clear()

        return jsonify({'message': 'All results deleted successfully'})
    except S3Error as e:
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    app.run(debug=True)
