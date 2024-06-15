from flask import Flask, request, jsonify, send_from_directory, render_template_string, send_file
from minio import Minio
from minio.error import S3Error
import os
import json
import zipfile
import io
import numpy as np
import tensorflow as tf
import tensorflow_hub as hub
from PIL import Image

app = Flask(__name__)

# MinIO client configuration
minio_client = Minio(
    "localhost:9000",
    access_key="minioadmin",
    secret_key="minioadmin",
    secure=False
)

BUCKET_NAME = "video-uploads"
OUTPUT_BUCKET_NAME = "output"

# Ensure both buckets exist
for bucket in [BUCKET_NAME, OUTPUT_BUCKET_NAME]:
    if not minio_client.bucket_exists(bucket):
        minio_client.make_bucket(bucket)

# Load the pre-trained object detection model
detector = hub.load("https://tfhub.dev/tensorflow/ssd_mobilenet_v2/2")

def process_and_save_result(file_name):
    # Load image
    file_path = os.path.join("/tmp", file_name)
    image = Image.open(file_path)
    image_np = np.array(image)

    # Run object detection
    results = detector(image_np[np.newaxis, ...])
    result = {key: value.numpy() for key, value in results.items()}

    # Format the results into a simple JSON structure
    predictions = []
    for i in range(len(result['detection_scores'][0])):
        if result['detection_scores'][0][i] >= 0.5:  # Filter out low-confidence predictions
            bbox = result['detection_boxes'][0][i].tolist()
            score = result['detection_scores'][0][i].tolist()
            predictions.append({
                'bbox': bbox,
                'score': score
            })

    result_data = {
        'file_name': file_name,
        'status': 'Processed',
        'predictions': predictions
    }

    # Save the results to a JSON file
    result_path = os.path.join("/tmp", f"{file_name}.json")
    with open(result_path, 'w') as f:
        json.dump(result_data, f)

    # Upload the result JSON to the 'output' bucket
    minio_client.fput_object(OUTPUT_BUCKET_NAME, f"{file_name}.json", result_path)
    os.remove(result_path)

@app.route('/')
def index():
    return render_template_string(open("index.html").read())

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
            minio_client.fput_object(BUCKET_NAME, file.filename, file_path)
            
            # Process the file and save the result
            process_and_save_result(file.filename)

            os.remove(file_path)

    return jsonify({'message': 'Files uploaded and processed successfully'})

@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    try:
        file_path = os.path.join("/tmp", filename)
        minio_client.fget_object(BUCKET_NAME, filename, file_path)
        return send_file(file_path, as_attachment=True)
    except S3Error:
        return jsonify({'error': 'File not found'})

@app.route('/list-files', methods=['GET'])
def list_files():
    objects = minio_client.list_objects(BUCKET_NAME)
    files = [obj.object_name for obj in objects]
    return jsonify(files)

@app.route('/list-results', methods=['GET'])
def list_results():
    objects = minio_client.list_objects(OUTPUT_BUCKET_NAME)
    results = [obj.object_name for obj in objects]
    return jsonify(results)

@app.route('/download-all-results', methods=['GET'])
def download_all_results():
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        objects = minio_client.list_objects(OUTPUT_BUCKET_NAME)
        for obj in objects:
            file_data = minio_client.get_object(OUTPUT_BUCKET_NAME, obj.object_name)
            zip_file.writestr(obj.object_name, file_data.read())

    zip_buffer.seek(0)
    return send_file(zip_buffer, mimetype='application/zip', as_attachment=True, download_name='all_results.zip')

@app.route('/delete-all', methods=['DELETE'])
def delete_all_files():
    try:
        objects_to_delete = minio_client.list_objects(BUCKET_NAME)
        for obj in objects_to_delete:
            minio_client.remove_object(BUCKET_NAME, obj.object_name)
        
        results_to_delete = minio_client.list_objects(OUTPUT_BUCKET_NAME)
        for obj in results_to_delete:
            minio_client.remove_object(OUTPUT_BUCKET_NAME, obj.object_name)

        return jsonify({'message': 'All files and results deleted successfully'})
    except S3Error as e:
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    app.run(debug=True)
