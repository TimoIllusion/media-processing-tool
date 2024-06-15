from flask import Flask, request, jsonify
import os

from engine import AIBackend
# create an api for a backend, that i can send http requests to to process a video by giving it a filename and bucket name

class BackendAPI:
    def __init__(self):
        self.app = Flask(__name__)
        self.app.config['UPLOAD_FOLDER'] = '/tmp'
        self.app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024 * 1024
        self.app.add_url_rule('/process-video', view_func=self.process_video, methods=['POST'])
        self.app.add_url_rule('/health', view_func=self.health, methods=['GET'])
        self.engine = AIBackend()

    def health(self):
        return jsonify({'status': 'ok'})

    def process_video(self):
        if 'file' not in request.files:
            return jsonify({'error': 'No file part'})
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No selected file'})
        if file:
            file_path = os.path.join(self.app.config['UPLOAD_FOLDER'], file.filename)
            file.save(file_path)
            success = self.ai_model.process_video(file_path)
            os.remove(file_path)
            if success:
                return jsonify({'message': 'File processed successfully'})
            else:
                return jsonify({'error': 'File processing failed'})
        return jsonify({'error': 'Unknown error'})

    def run(self):
        self.app.run(host='