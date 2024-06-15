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
            await fetch(`/process/${file}`, {
                method: 'POST'
            });
            // Start checking status immediately after initiating the processing
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


        if (result.status === 'Processing') {
            statusDiv.innerHTML = `<p>${filename}: ${result.status} ${result.current_frame}/${result.total_frames} </p>`;
        }
        else
        {
            statusDiv.innerHTML = `<p>${filename}: ${result.status}</p>`;
        }

        




        if (result.status === 'Completed' || result.status.startsWith('Error')) {
            listProcessedResults();
        }
    } catch (error) {
        statusDiv.innerHTML = `<p>${filename}: Error checking status: ${error}</p>`;
    }
}


async function listUploadedFiles() {
    const resultsDiv = document.getElementById('upload-status');
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

async function deleteAllInputFiles() {
    if (confirm('Are you sure you want to delete all input files?')) {
        const response = await fetch('/delete-input', {
            method: 'DELETE'
        });
        const result = await response.json();
        const statusDiv = document.getElementById('upload-status');
        statusDiv.innerHTML = `<p>${result.message}</p>`; // Overwrite the content

        listUploadedFiles();
    } else {
        const statusDiv = document.getElementById('upload-status');
        statusDiv.innerHTML = `<p>Deletion of input files canceled.</p>`; // Overwrite the content if the user cancels
    }
}

async function deleteAllOutputFiles() {
    if (confirm('Are you sure you want to delete all output files?')) {
        const response = await fetch('/delete-output', {
            method: 'DELETE'
        });
        const result = await response.json();
        const statusDiv = document.getElementById('results');
        statusDiv.innerHTML = `<p>${result.message}</p>`; // Overwrite the content

        listProcessedResults();
    } else {
        const statusDiv = document.getElementById('results');
        statusDiv.innerHTML = `<p>Deletion of output files canceled.</p>`; // Overwrite the content if the user cancels
    }
}

document.addEventListener('DOMContentLoaded', () => {
    listUploadedFiles();
    listProcessedResults();
});
