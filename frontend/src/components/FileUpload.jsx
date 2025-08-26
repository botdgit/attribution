import React, { useState } from 'react';

export default function FileUpload() {
  const [file, setFile] = useState(null);
  const [status, setStatus] = useState('idle');

  const handleFile = (e) => {
    setFile(e.target.files[0]);
  }

  const upload = async () => {
    if (!file) return;
    setStatus('uploading');
    const res = await fetch('/v1/uploads/url', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({ filename: file.name }) });
    const body = await res.json();
    const uploadUrl = body.url;
    const objectPath = body.object;
    await fetch(uploadUrl, { method: 'PUT', body: file, headers: { 'Content-Type': 'application/octet-stream' } });
    setStatus('done');
    // optional: inform backend to start processing (Cloud Function listens to bucket notification)
    console.log('uploaded to', objectPath);
  }

  return (
    <div>
      <input type="file" accept=".csv" onChange={handleFile} />
      <button onClick={upload} disabled={!file}>Upload CSV</button>
      <div>Status: {status}</div>
    </div>
  )
}
