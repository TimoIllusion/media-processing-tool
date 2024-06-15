from flask import Flask, request, jsonify
from engine import AIBackend
from config import BackendConfig

from loguru import logger

app = Flask(__name__)
backend = AIBackend()

# Dictionary to store the processing status
# TODO: use db
PROCESSING_STATUS = {}

@app.route('/process-media-file', methods=['POST'])
def process_media_file():
    try:
        data = request.json
        filename = data.get('filename', None)
        
        if filename is None:
            return jsonify({'error': 'Filename not provided.'}), 401
        
        if filename not in PROCESSING_STATUS:
            PROCESSING_STATUS[filename] = {'status': 'Processing', 'current_frame': 0, 'total_frames': 0}
        else:
            logger.warning(f"File {filename} has been processed already.")
            return jsonify({'success': True}), 200

        result = backend.fetch_and_process_video(filename, PROCESSING_STATUS)
        logger.info(f"Result: {result}")
        
        if result:
            return jsonify({'success': True}), 200
        else:
            PROCESSING_STATUS[filename]['status'] = 'Failed'
            return jsonify({'error': "Processing failed.", 'success': False}), 403
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500

@app.route('/status/<filename>', methods=['GET'])
def check_status(filename):
    logger.debug(f"Checking status of {filename}")
    logger.debug(f"Processing status: {PROCESSING_STATUS}")
    if filename not in PROCESSING_STATUS:
        return jsonify({'status': 'File not yet processed.'}), 404
    else:
        return PROCESSING_STATUS[filename]

if __name__ == '__main__':
    app.run(host='localhost', port=BackendConfig.PORT, debug=True)
