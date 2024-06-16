from flask import Flask, request, jsonify, render_template, send_file
from minio import Minio
import os
import zipfile
from io import BytesIO
import requests
from config import MINIO_ENDPOINT, MINIO_PORT, MINIO_USE_SSL, MINIO_ACCESS_KEY, MINIO_SECRET_KEY, INPUT_BUCKET_NAME, OUTPUT_BUCKET_NAME, BACKEND_URL

app = Flask(__name__)

# MinIO configuration
minioClient = Minio(
    f"{MINIO_ENDPOINT}:{MINIO_PORT}",
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=MINIO_USE_SSL
)

# Ensure both buckets exist
def ensure_bucket_exists(bucket_name):
    if not minioClient.bucket_exists(bucket_name):
        minioClient.make_bucket(bucket_name)
        print(f"Bucket {bucket_name} created successfully.")
    else:
        print(f"Bucket {bucket_name} already exists.")

ensure_bucket_exists(INPUT_BUCKET_NAME)
ensure_bucket_exists(OUTPUT_BUCKET_NAME)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    files = request.files.getlist('videos')
    if not files:
        return "No files uploaded.", 400

    upload_results = []
    for file in files:
        file_name = file.filename
        file_data = file.read()
        try:
            minioClient.put_object(INPUT_BUCKET_NAME, file_name, BytesIO(file_data), len(file_data))
            upload_results.append(f"File {file_name} uploaded successfully.")
        except Exception as e:
            return str(e), 500

    return "<br>".join(upload_results), 200

@app.route('/process/<filename>', methods=['POST'])
def process_file(filename):
    try:
        response = requests.post(f"{BACKEND_URL}/process-media-file", json={"filename": filename})
        response_data = response.json()
        if response_data.get('success'):
            return jsonify(message='File processing started successfully'), 200
        else:
            return jsonify(error='File processing failed'), 500
    except Exception as e:
        return jsonify(error=str(e)), 500

@app.route('/status/<filename>', methods=['GET'])
def status(filename):
    try:
        response = requests.get(f"{BACKEND_URL}/status/{filename}")
        response_data = response.json()
        return jsonify(response_data), 200
    except Exception as e:
        return jsonify(error=str(e)), 500

@app.route('/download/<filename>', methods=['GET'])
def download(filename):
    try:
        response = minioClient.get_object(OUTPUT_BUCKET_NAME, filename)
        return send_file(BytesIO(response.read()), as_attachment=True, download_name=filename)
    except Exception as e:
        return jsonify(error=str(e)), 404

@app.route('/list-files', methods=['GET'])
def list_files():
    files = [obj.object_name for obj in minioClient.list_objects(INPUT_BUCKET_NAME)]
    return jsonify(files), 200

@app.route('/list-results', methods=['GET'])
def list_results():
    results = [obj.object_name for obj in minioClient.list_objects(OUTPUT_BUCKET_NAME)]
    return jsonify(results), 200

@app.route('/download-all-results', methods=['GET'])
def download_all_results():
    try:
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
            for obj in minioClient.list_objects(OUTPUT_BUCKET_NAME):
                data = minioClient.get_object(OUTPUT_BUCKET_NAME, obj.object_name)
                zip_file.writestr(obj.object_name, data.read())
        zip_buffer.seek(0)
        return send_file(zip_buffer, as_attachment=True, download_name='all_results.zip', mimetype='application/zip')
    except Exception as e:
        return jsonify(error=str(e)), 500

@app.route('/delete-input', methods=['DELETE'])
def delete_input():
    try:
        for obj in minioClient.list_objects(INPUT_BUCKET_NAME):
            minioClient.remove_object(INPUT_BUCKET_NAME, obj.object_name)
        return jsonify(message='All input files deleted successfully'), 200
    except Exception as e:
        return jsonify(error=str(e)), 500

@app.route('/delete-output', methods=['DELETE'])
def delete_output():
    try:
        for obj in minioClient.list_objects(OUTPUT_BUCKET_NAME):
            minioClient.remove_object(OUTPUT_BUCKET_NAME, obj.object_name)
        return jsonify(message='All output files deleted successfully'), 200
    except Exception as e:
        return jsonify(error=str(e)), 500

@app.route('/reset', methods=['GET'])
def reset():
    try:
        response = requests.get(f"{BACKEND_URL}/reset")
        return jsonify(message='Backend reset successfully'), 200
    except Exception as e:
        return jsonify(error=str(e)), 500

if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=True, port=5000)
