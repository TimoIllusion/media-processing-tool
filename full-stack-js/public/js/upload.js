function uploadFiles() {
  const formData = new FormData();
  const files = document.getElementById('videos').files;
  for (let i = 0; i < files.length; i++) {
    formData.append('videos', files[i]);
  }

  fetch(UPLOAD_ENDPOINT, {
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

  fetch(UPLOAD_ENDPOINT, {
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
