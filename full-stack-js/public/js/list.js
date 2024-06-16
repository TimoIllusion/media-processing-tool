async function listUploadedFiles() {
    const resultsDiv = document.getElementById('upload-status');
    resultsDiv.innerHTML = ''; // Clear the content before appending new results
  
    const response = await fetch(LIST_FILES_ENDPOINT);
    const files = await response.json();
  
    files.forEach(file => {
      resultsDiv.innerHTML += `<p>Uploaded: ${file}</p>`;
    });
  }
  
  async function listProcessedResults() {
    const resultsDiv = document.getElementById('results');
    resultsDiv.innerHTML = ''; // Clear the content before appending new results
  
    const response = await fetch(LIST_RESULTS_ENDPOINT);
    const results = await response.json();
  
    results.forEach(result => {
      resultsDiv.innerHTML += `<p><a href="/download/${result}">${result}</a></p>`;
    });
  }
  
  async function downloadAllResults() {
    window.location.href = DOWNLOAD_ALL_RESULTS_ENDPOINT;
  }
  
  async function deleteAllInputFiles() {
    if (confirm('Are you sure you want to delete all input files?')) {
      const response = await fetch(DELETE_INPUT_ENDPOINT, {
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
      const response = await fetch(DELETE_OUTPUT_ENDPOINT, {
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
  