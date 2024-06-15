const express = require('express');
const multer = require('multer');
const Minio = require('minio');
const path = require('path');
const app = express();
const port = 3000;

// MinIO configuration
const minioClient = new Minio.Client({
  endPoint: process.env.MINIO_ENDPOINT || 'localhost',
  port: parseInt(process.env.MINIO_PORT, 10) || 9000,
  useSSL: false,
  accessKey: process.env.MINIO_ACCESS_KEY || 'minio_access_key',
  secretKey: process.env.MINIO_SECRET_KEY || 'minio_secret_key'
});

const bucketName = 'video-uploads';

// Ensure the bucket exists
minioClient.bucketExists(bucketName, function(err) {
  if (err) {
    minioClient.makeBucket(bucketName, 'us-east-1', function(err) {
      if (err) return console.log('Error creating bucket.', err);
      console.log('Bucket created successfully.');
    });
  } else {
    console.log('Bucket already exists.');
  }
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
      minioClient.putObject(bucketName, fileName, file.buffer, file.size, function(err, etag) {
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

app.listen(port, () => {
  console.log(`App running at http://localhost:${port}`);
});
