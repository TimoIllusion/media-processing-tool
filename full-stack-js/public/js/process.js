async function processFiles() {
    const processStatusDiv = document.getElementById('process-status');
    processStatusDiv.innerHTML = ''; // Clear the content before processing
  
    const response = await fetch(LIST_FILES_ENDPOINT);
    const files = await response.json();
  
    for (const file of files) {
      try {
        await fetch(`${PROCESS_ENDPOINT}/${file}`, {
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
  
    const response = await fetch(RESET_ENDPOINT);
    const results = await response.json();
  
    statusDiv.innerHTML = `<p>${results.message}</p>`;
  }
  
  async function checkAllStatus() {
    const processStatusDiv = document.getElementById('process-status');
    processStatusDiv.innerHTML = ''; // Clear the content before checking all status
  
    const response = await fetch(LIST_FILES_ENDPOINT);
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
      const response = await fetch(`${STATUS_ENDPOINT}/${filename}`);
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
  