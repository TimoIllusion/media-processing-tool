function uploadFiles() {
    const formData = new FormData();
    const files = document.getElementById('videos').files;
    for (let i = 0; i < files.length; i++) {
        formData.append('videos', files[i]);
    }

    fetch('/upload', {
        method: 'POST',
        body: formData
    }).then(response => response.text())
        .then(result => {
            alert(result);
            listUploadedFiles(); // Call listUploadedFiles to refresh the list
        }).catch(error => {
            console.error('Error:', error);
        });
}

function uploadDirectory() {
    const formData = new FormData();
    const files = document.getElementById('directory').files;
    for (let i = 0; i < files.length; i++) {
        formData.append('videos', files[i], files[i].webkitRelativePath || files[i].name);
    }

    fetch('/upload', {
        method: 'POST',
        body: formData
    }).then(response => response.text())
        .then(result => {
            alert(result);
            listUploadedFiles(); // Call listUploadedFiles to refresh the list
        }).catch(error => {
            console.error('Error:', error);
        });
}

async function processFiles() {
    const processStatusDiv = document.getElementById('process-status');
    processStatusDiv.innerHTML = ''; // Clear the content before processing

    const response = await fetch('/list-files');
    const files = await response.json();

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

async function resetProcessingState() {
    const statusDiv = document.getElementById('process-status');
    statusDiv.innerHTML = ''; // Clear the content before resetting

    const response = await fetch('/reset');
    const results = await response.json();

    statusDiv.innerHTML = `<p>${results.message}</p>`;
}

async function checkAllStatus() {
    const processStatusDiv = document.getElementById('process-status');
    processStatusDiv.innerHTML = ''; // Clear the content before checking all status

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

        if (result.status === undefined) {
            throw new Error('Status property is undefined');
        }

        if (result.status === 'Processing') {
            statusDiv.innerHTML = `<p>${filename}: ${result.status} ${result.current_frame}/${result.total_frames} </p>`;
        } else {
            statusDiv.innerHTML = `<p>${filename}: ${result.status}</p>`;
        }

        if (result.status === 'Completed' || result.status.startsWith('Error')) {
            listProcessedResults();
        }
    } catch (error) {
        statusDiv.innerHTML = `<p>${filename}: Error checking status: ${error.message}</p>`;
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