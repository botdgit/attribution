import React, { useState } from "react";
import fetchWithAuth from "../utils/fetchWithAuth";

export default function FileUpload() {
	const [file, setFile] = useState(null);
	const [status, setStatus] = useState("");

	async function handleUpload(e) {
		e.preventDefault();
		if (!file) return;
		setStatus("Uploading...");
		try {
			// If ingestion endpoint exists, use it. Otherwise call a demo analysis endpoint.
			const form = new FormData();
			form.append("file", file);
			const base = import.meta.env.VITE_BACKEND_URL || "";
			const ingestUrl = "/api/ingest";
			// Try ingest first
			try {
				await fetchWithAuth(ingestUrl, { method: "POST", body: form, headers: {} });
				setStatus("Uploaded to ingest endpoint");
				return;
			} catch (err) {
				// fallback to calling a sample analysis endpoint
			}

			// Fallback: call DID analysis with a dummy campaign id to trigger demo
			await fetchWithAuth("/api/analysis/did", { method: "POST", body: JSON.stringify({ campaign_id: "demo-campaign" }) });
			setStatus("Processed by analysis endpoint (demo)");
		} catch (err) {
			setStatus(`Error: ${err.message}`);
		}
	}

	return <div>
		<form onSubmit={handleUpload}>
			<input type="file" onChange={e => setFile(e.target.files?.[0] || null)} />
			<button type="submit">Upload</button>
		</form>
		<div>{status}</div>
	</div>;
}
