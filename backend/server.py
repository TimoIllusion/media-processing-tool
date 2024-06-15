from flask import Flask, request, jsonify

from engine import AIBackend
from config import BackendConfig

app = Flask(__name__)
backend = AIBackend()

@app.route('/process-media-file', methods=['POST'])
def process_media_file():
    data = request.json
    filename = data.get('filename')
    processing_status = data.get('processing_status')

    if filename is None:
        return jsonify({'error': 'Filename not provided.'}), 401

    if processing_status is None:
        return jsonify({'error': 'Processing failed. processing_status is None'}), 402

    result = backend.fetch_and_process_video(filename, processing_status)
    
    # the response should be the processing status
    
    if result:
        return jsonify({'processing_status': processing_status})
    else:
        return jsonify({'error': "Processing failed."})

if __name__ == '__main__':
    app.run(host='localhost', port=BackendConfig.PORT)