Sure, here's a README file focusing on the overview, setup, and usage of the Flask-based media processing tool:

# media-processing-tool

A tool to process videos using a web application. Right now a simple detection model from tensorflow hub is used to process the videos.

## Setup

### Prerequisites

- Python 3.7 or higher
- docker and docker-compose installed

### Installation

1. **Clone the repository:**
    ```shell
    https://github.com/TimoIllusion/media-processing-tool.git
    cd media-processing-tool
    ```

2. **Create a virtual environment:**
    ```shell
    python -m venv .env 
    source .env/bin/activate  # On Windows, use `.env\Scripts\activate`
    ```

3. **Install the required dependencies:**
    ```shell
    pip install -r requirements.txt
    ```

4. **Ensure MinIO is running:**

   You can run MinIO using Docker:
   ```shell
   docker-compose up -d
   ```

## Usage

1. **Start the Flask application:**
    ```shell
    python app.py
    ```

2. **Access the application:**

   Open a web browser and navigate to `http://127.0.0.1:5000/` to access the web interface.

3. **Upload Videos:**

   - Go to the "Upload Files" section.
   - Select multiple video files to upload.
   - Click the "Upload" button to upload the videos to MinIO storage.

4. **Process Videos:**

   - Go to the "Process Files" section.
   - Click the "Process All Files" button to process all uploaded videos.
   - The processing status will be displayed for each video.

5. **Manage Results:**

   - Go to the "Manage Results" section.
   - List the current uploaded files by clicking "List Current Uploaded Files".
   - List the processed results by clicking "List Current Results".
   - Download all processed results as a zip file by clicking "Download All Results".
   - Delete all input files from MinIO by clicking "Delete All Input Files".
   - Delete all output files from MinIO by clicking "Delete All Output Files".

6. **Shutdown:**

   - ``Ctrl + C`` to close the app in terminal
   - ``docker compose down``

## License

This project is licensed under the MIT License - see the LICENSE file for details.