async function uploadFiles() {
    const input = document.getElementById('file-input');
    const files = input.files;
    const uploadStatusDiv = document.getElementById('upload-status');
    uploadStatusDiv.innerHTML = '';

    const formData = new FormData();
    for (const file of files) {
        formData.append('file', file);
    }

    try {
        const response = await fetch('/upload', {
            method: 'POST',
            body: formData
        });
        const result = await response.json();
        uploadStatusDiv.innerHTML = `<p>${result.message}</p>`;
        listUploadedFiles(); // Call listUploadedFiles to refresh the list
    } catch (error) {
        uploadStatusDiv.innerHTML = `<p>Error uploading files: ${error}</p>`;
    }
}

async function processFiles() {
    const response = await fetch('/list-files');
    const files = await response.json();

    const processStatusDiv = document.getElementById('process-status');
    processStatusDiv.innerHTML = '';

    for (const file of files) {
        try {
            const processResponse = await fetch(`/process/${file}`, {
                method: 'POST'
            });
            const processResult = await processResponse.json();
            processStatusDiv.innerHTML += `<p>${file}: ${processResult.message}</p>`;
            checkStatus(file);
        } catch (error) {
            processStatusDiv.innerHTML += `<p>${file}: Error processing file: ${error}</p>`;
        }
    }
}

async function checkAllStatus() {
    const response = await fetch('/list-files');
    const files = await response.json();

    for (const file of files) {
        checkStatus(file);
    }
}

async function checkStatus(filename) {
    const statusDiv = document.getElementById(`status-${filename}`) || document.createElement('div');
    statusDiv.id = `status-${filename}`;
    statusDiv.classList.add('progress');
    document.getElementById('process-status').appendChild(statusDiv);

    try {
        const response = await fetch(`/status/${filename}`);
        const result = await response.json();
        if (result.status === 'Completed' || result.status.startsWith('Error')) {
            statusDiv.innerHTML = `<p>${filename}: ${result.status}</p>`;
            listProcessedResults();
        } else {
            statusDiv.innerHTML = `<p>${filename}: ${result.status} (Frame ${result.current_frame} of ${result.total_frames})</p>`;
        }
    } catch (error) {
        statusDiv.innerHTML = `<p>${filename}: Error checking status: ${error}</p>`;
    }
}

async function listUploadedFiles() {
    const resultsDiv = document.getElementById('results');
    resultsDiv.innerHTML = ''; // Clear the content before appending new results

    const response = await fetch('/list-files');
    const files = await response.json();

    files.forEach(file => {
        resultsDiv.innerHTML += `<p>Uploaded: ${file}</p>`;
    });
}

async function listProcessedResults() {
    const resultsDiv = document.getElementById('results');
    resultsDiv.innerHTML = ''; // Clear the content before appending new results

    const response = await fetch('/list-results');
    const results = await response.json();

    results.forEach(result => {
        resultsDiv.innerHTML += `<p><a href="/download/${result}">${result}</a></p>`;
    });
}

async function downloadAllResults() {
    window.location.href = '/download-all-results';
}

async function deleteAllFiles() {
    if (confirm('Are you sure you want to delete all files and results?')) {
        const response = await fetch('/delete-all', {
            method: 'DELETE'
        });
        const result = await response.json();
        const statusDiv = document.getElementById('process-status');
        statusDiv.innerHTML = `<p>${result.message}</p>`; // Overwrite the content

        listUploadedFiles();
        listProcessedResults();
    } else {
        const statusDiv = document.getElementById('process-status');
        statusDiv.innerHTML = `<p>Deletion canceled.</p>`; // Overwrite the content if the user cancels
    }
}

document.addEventListener('DOMContentLoaded', () => {
    listUploadedFiles();
    listProcessedResults();
});