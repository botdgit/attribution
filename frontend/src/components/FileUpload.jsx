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
    // We assume a signed upload URL endpoint exists at /api/uploads/url
    const res = await fetch('/api/uploads/url', { method: 'POST' });
    const body = await res.json();
    const uploadUrl = body.url;
    await fetch(uploadUrl, { method: 'PUT', body: file });
    setStatus('done');
  }

  return (
    <div>
      <input type="file" accept=".csv" onChange={handleFile} />
      <button onClick={upload} disabled={!file}>Upload CSV</button>
      <div>Status: {status}</div>
    </div>
  )
}
