from flask import Flask, render_template, request, jsonify, send_file
from minio import Minio
from minio.error import S3Error
import os
import json
import zipfile
import io
import numpy as np
import tensorflow as tf
import tensorflow_hub as hub
import cv2
import tqdm
from loguru import logger

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
PROCESSING_STATUS = {}

# Ensure both buckets exist
for bucket in [BUCKET_NAME, OUTPUT_BUCKET_NAME]:
    if not minio_client.bucket_exists(bucket):
        minio_client.make_bucket(bucket)

# Load the pre-trained object detection model
detector = hub.load("https://tfhub.dev/tensorflow/ssd_mobilenet_v2/2")

def process_video(file_name):
    
    if file_name in PROCESSING_STATUS and PROCESSING_STATUS[file_name]['status'] == 'Completed':
        logger.warning(f"File {file_name} has already been processed.")
        return
    
    try:
        # Load video
        file_path = os.path.join("/tmp", file_name)
        cap = cv2.VideoCapture(file_path)
        
        frame_results = []
        
        frame_count = 0
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        PROCESSING_STATUS[file_name] = {
            'status': 'Processing',
            'current_frame': frame_count,
            'total_frames': total_frames
        }
        
        progress = tqdm.tqdm(total=total_frames, desc=f"Processing {file_name}")
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = detector(frame_rgb[np.newaxis, ...])
            result = {key: value.numpy() for key, value in results.items()}

            frame_predictions = []
            for i in range(len(result['detection_scores'][0])):
                if result['detection_scores'][0][i] >= 0.5:  # Filter out low-confidence predictions
                    bbox = result['detection_boxes'][0][i].tolist()
                    score = result['detection_scores'][0][i].tolist()
                    frame_predictions.append({
                        'bbox': bbox,
                        'score': score
                    })
            
            frame_results.append({
                'frame': frame_count,
                'predictions': frame_predictions
            })
            
            frame_count += 1
            PROCESSING_STATUS[file_name]['current_frame'] = frame_count
            progress.update(1)

        cap.release()
        
        result_data = {
            'file_name': file_name,
            'status': 'Processed',
            'frame_results': frame_results
        }

        # Save the results to a JSON file
        result_path = os.path.join("/tmp", f"{file_name}.json")
        with open(result_path, 'w') as f:
            json.dump(result_data, f)

        # Upload the result JSON to the 'output' bucket
        minio_client.fput_object(OUTPUT_BUCKET_NAME, f"{file_name}.json", result_path)
        os.remove(result_path)
        
        PROCESSING_STATUS[file_name]['status'] = 'Completed'
    except Exception as e:
        PROCESSING_STATUS[file_name]['status'] = f'Error: {str(e)}'

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
            minio_client.fput_object(BUCKET_NAME, file.filename, file_path)
            os.remove(file_path)
            
            # Initialize processing status
            PROCESSING_STATUS[file.filename] = {'status': 'Uploaded'}

    return jsonify({'message': 'Files uploaded successfully. Ready to be processed.'})

@app.route('/process/<filename>', methods=['POST'])
def process_file(filename):
    try:
        # Download the file from MinIO
        file_path = os.path.join("/tmp", filename)
        minio_client.fget_object(BUCKET_NAME, filename, file_path)
        
        # Process the file
        process_video(filename)
        
        return jsonify({'message': 'File processed successfully'})
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
        minio_client.fget_object(OUTPUT_BUCKET_NAME, filename, file_path)
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

@app.route('/delete-input', methods=['DELETE'])
def delete_all_files():
    try:
        objects_to_delete = minio_client.list_objects(BUCKET_NAME)
        for obj in objects_to_delete:
            minio_client.remove_object(BUCKET_NAME, obj.object_name)

        return jsonify({'message': 'All input files deleted successfully'})
    except S3Error as e:
        return jsonify({'error': str(e)})
    
@app.route('/delete-output', methods=['DELETE'])
def delete_all_output_files():
    try:
        results_to_delete = minio_client.list_objects(OUTPUT_BUCKET_NAME)
        for obj in results_to_delete:
            minio_client.remove_object(OUTPUT_BUCKET_NAME, obj.object_name)

        PROCESSING_STATUS.clear()

        return jsonify({'message': 'All results deleted successfully'})
    except S3Error as e:
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    app.run(debug=True)
