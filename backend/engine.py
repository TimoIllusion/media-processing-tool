import os
import json

import numpy as np
import cv2
import tensorflow_hub as hub
from minio import Minio
from tqdm import tqdm
from loguru import logger

from config import BackendConfig

class AIBackend:
    def __init__(self):
        self.detector = hub.load("https://tfhub.dev/tensorflow/ssd_mobilenet_v2/2")
        
        self.minio_client = Minio(
            BackendConfig.STORAGE_HOST,
            access_key=BackendConfig.STORAGE_ACCESS_KEY,
            secret_key=BackendConfig.STORAGE_SECRET_KEY,
            secure=False
            )
        
        self.input_bucket = BackendConfig.INPUT_BUCKET_NAME
        self.output_bucket = BackendConfig.OUTPUT_BUCKET_NAME

    def fetch_and_process_video(self, file_name, processing_status) -> bool:
        # Download the file from MinIO
        file_path = os.path.join("/tmp", file_name)
        self.minio_client.fget_object(self.input_bucket, file_name, file_path)
        
        # Process the file
        result_path = self.process_video(file_name, processing_status)
        
        # Upload the result JSON to the 'output' bucket
        if result_path is not None:
            self.minio_client.fput_object(self.output_bucket, f"{file_name}.json", result_path)
            os.remove(result_path)
            
            return True
        else:
            return False

    def process_video(self, file_name, processing_status):
        try:
            # Load video
            file_path = os.path.join("/tmp", file_name)
            cap = cv2.VideoCapture(file_path)
            
            frame_results = []
            
            frame_count = 0
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            processing_status[file_name] = {
                'status': 'Processing',
                'current_frame': frame_count,
                'total_frames': total_frames
            }
            
            progress = tqdm(total=total_frames, desc=f"Processing {file_name}")
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break
                
                frame_predictions = self.process_image(frame)
                
                frame_results.append({
                    'frame': frame_count,
                    'predictions': frame_predictions
                })
                
                frame_count += 1
                processing_status[file_name]['current_frame'] = frame_count
                progress.update(1)

            cap.release()
            
            result_data = {
                'file_name': file_name,
                'frame_results': frame_results
            }

            # Save the results to a JSON file
            result_path = os.path.join("/tmp", f"{file_name}.json")
            with open(result_path, 'w') as f:
                json.dump(result_data, f)
                
            processing_status[file_name] = {
                'status': 'Completed',
                'current_frame': frame_count,
                'total_frames': total_frames
            }

            return result_path

        except Exception as e:
            processing_status[file_name]['status'] = f'Error: {str(e)}'
            raise
        
    def process_image(self, frame):
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.detector(frame_rgb[np.newaxis, ...])
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
        return frame_predictions