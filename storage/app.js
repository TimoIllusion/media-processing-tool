const express = require('express');
const path = require('path');
const Minio = require('minio');
const multer = require('multer');
const fetch = require('node-fetch');
const { MINIO_ENDPOINT, MINIO_PORT, MINIO_USE_SSL, MINIO_ACCESS_KEY, MINIO_SECRET_KEY, INPUT_BUCKET_NAME, OUTPUT_BUCKET_NAME, BACKEND_URL } = require('./config');

const app = express();
const port = 3000;

// MinIO configuration
const minioClient = new Minio.Client({
  endPoint: MINIO_ENDPOINT,
  port: MINIO_PORT,
  useSSL: MINIO_USE_SSL,
  accessKey: MINIO_ACCESS_KEY,
  secretKey: MINIO_SECRET_KEY
});

// Ensure both buckets exist
[minioClient.bucketExists(INPUT_BUCKET_NAME), minioClient.bucketExists(OUTPUT_BUCKET_NAME)].forEach((bucketPromise, idx) => {
  bucketPromise.then(exists => {
    if (!exists) {
      const bucketName = idx === 0 ? INPUT_BUCKET_NAME : OUTPUT_BUCKET_NAME;
      minioClient.makeBucket(bucketName, 'us-east-1', err => {
        if (err) {
          console.log(`Error creating bucket ${bucketName}:`, err);
        } else {
          console.log(`Bucket ${bucketName} created successfully.`);
        }
      });
    }
  }).catch(err => {
    console.log('Error checking bucket existence:', err);
  });
});

// Set up multer for file uploads
const storage = multer.memoryStorage();
const upload = multer({ storage: storage });

app.use(express.static('public'));

app.post('/upload', upload.array('videos', 10), (req, res) => {
  const files = req.files;
  if (!files || files.length === 0) {
    return res.status(400).send('No files uploaded.');
  }

  let uploadPromises = files.map(file => {
    return new Promise((resolve, reject) => {
      const fileName = path.basename(file.originalname);
      minioClient.putObject(INPUT_BUCKET_NAME, fileName, file.buffer, file.size, function(err, etag) {
        if (err) {
          reject(err);
        } else {
          resolve(`File ${fileName} uploaded successfully.`);
        }
      });
    });
  });

  Promise.all(uploadPromises)
    .then(results => {
      res.send(results.join('<br>'));
    })
    .catch(error => {
      res.status(500).send(error.message);
    });
});

app.post('/process/:filename', async (req, res) => {
  const { filename } = req.params;
  try {
    const response = await fetch(`${BACKEND_URL}/process-media-file`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ filename })
    });
    const responseData = await response.json();
    const success = responseData.success;
    if (success) {
      res.json({ message: 'File processing started successfully' });
    } else {
      res.json({ error: 'File processing failed' });
    }
  } catch (error) {
    res.json({ error: error.message });
  }
});

app.get('/status/:filename', async (req, res) => {
  const { filename } = req.params;
  try {
    const response = await fetch(`${BACKEND_URL}/status/${filename}`);
    const result = await response.json();
    res.json(result);
  } catch (error) {
    res.json({ error: error.message });
  }
});

app.get('/download/:filename', (req, res) => {
  const { filename } = req.params;
  const filePath = path.join('/tmp', filename);
  minioClient.fgetObject(OUTPUT_BUCKET_NAME, filename, filePath, err => {
    if (err) {
      return res.json({ error: 'File not found' });
    }
    res.sendFile(filePath);
  });
});

app.get('/list-files', async (req, res) => {
  const stream = minioClient.listObjects(INPUT_BUCKET_NAME, '', true);
  const files = [];
  stream.on('data', obj => files.push(obj.name));
  stream.on('end', () => res.json(files));
  stream.on('error', err => res.status(500).json({ error: err.message }));
});

app.get('/list-results', async (req, res) => {
  const stream = minioClient.listObjects(OUTPUT_BUCKET_NAME, '', true);
  const results = [];
  stream.on('data', obj => results.push(obj.name));
  stream.on('end', () => res.json(results));
  stream.on('error', err => res.status(500).json({ error: err.message }));
});

app.get('/download-all-results', async (req, res) => {
  const zipBuffer = Buffer.alloc(0);
  const zip = new require('node-zip')();
  const stream = minioClient.listObjects(OUTPUT_BUCKET_NAME, '', true);
  stream.on('data', async obj => {
    const data = await minioClient.getObject(OUTPUT_BUCKET_NAME, obj.name);
    zip.file(obj.name, data);
  });
  stream.on('end', () => {
    const data = zip.generate({ base64: false, compression: 'DEFLATE' });
    res.set('Content-Type', 'application/zip');
    res.set('Content-Disposition', 'attachment; filename=all_results.zip');
    res.send(data);
  });
  stream.on('error', err => res.status(500).json({ error: err.message }));
});

app.delete('/delete-input', async (req, res) => {
  const stream = minioClient.listObjects(INPUT_BUCKET_NAME, '', true);
  stream.on('data', obj => minioClient.removeObject(INPUT_BUCKET_NAME, obj.name));
  stream.on('end', () => res.json({ message: 'All input files deleted successfully' }));
  stream.on('error', err => res.status(500).json({ error: err.message }));
});

app.delete('/delete-output', async (req, res) => {
  const stream = minioClient.listObjects(OUTPUT_BUCKET_NAME, '', true);
  stream.on('data', obj => minioClient.removeObject(OUTPUT_BUCKET_NAME, obj.name));
  stream.on('end', () => res.json({ message: 'All output files deleted successfully' }));
  stream.on('error', err => res.status(500).json({ error: err.message }));
});

app.get('/reset', async (req, res) => {
  try {
    await fetch(`${BACKEND_URL}/reset`);
    res.json({ message: 'Backend reset successfully' });
  } catch (error) {
    res.json({ error: error.message });
  }
});

app.listen(port, () => {
  console.log(`App running at http://localhost:${port}`);
});
