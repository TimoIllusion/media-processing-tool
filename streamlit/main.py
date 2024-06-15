import streamlit as st
import os
import json
import time
from multiprocessing import Process, Queue

# Directories for uploads and results
UPLOAD_FOLDER = 'uploads'
RESULT_FOLDER = 'results'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULT_FOLDER, exist_ok=True)

def process_video(file_path, result_queue):
    # Simulate video processing
    time.sleep(5)  # Placeholder for actual processing time
    result_data = {'status': 'completed', 'file': os.path.basename(file_path)}
    result_path = os.path.join(RESULT_FOLDER, f"{os.path.basename(file_path)}.json")
    with open(result_path, 'w') as f:
        json.dump(result_data, f)
    result_queue.put(result_path)

def save_uploaded_file(uploaded_file):
    file_path = os.path.join(UPLOAD_FOLDER, uploaded_file.name)
    with open(file_path, 'wb') as f:
        f.write(uploaded_file.getbuffer())
    return file_path

st.title("Video Upload and Processing App")

if "processes" not in st.session_state:
    st.session_state.processes = {}

uploaded_files = st.file_uploader("Upload videos", type=["mp4", "avi", "mov"], accept_multiple_files=True)

if uploaded_files:
    for uploaded_file in uploaded_files:
        file_path = save_uploaded_file(uploaded_file)
        result_queue = Queue()
        process = Process(target=process_video, args=(file_path, result_queue))
        process.start()
        st.session_state.processes[file_path] = (process, result_queue)
        st.success(f"Uploaded {uploaded_file.name} and started processing.")

st.write("Processing Status:")
for file_path, (process, result_queue) in list(st.session_state.processes.items()):
    if not process.is_alive():
        process.join()
        if not result_queue.empty():
            result_path = result_queue.get()
            st.session_state.processes.pop(file_path)
            st.success(f"Processing completed for {os.path.basename(file_path)}.")
        else:
            st.warning(f"Processing for {os.path.basename(file_path)} has failed.")

if st.button("Refresh Status"):
    st.experimental_rerun()

st.write("Downloaded Results:")
for result_file in os.listdir(RESULT_FOLDER):
    if result_file.endswith(".json"):
        result_file_path = os.path.join(RESULT_FOLDER, result_file)
        with open(result_file_path, 'r') as f:
            result_data = json.load(f)
            st.markdown(f"[{result_file}](/{result_file_path})")
