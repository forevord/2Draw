/**
 * Backend API client helpers (PS-10).
 *
 * All functions target the FastAPI backend at /api/v1.
 */

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface UploadResult {
  upload_id: string;
  filename: string;
  size: number;
}

export interface ProcessParams {
  upload_id: string;
  n_clusters?: number;
  region?: "eu" | "cis" | "global";
}

export interface ProcessResult {
  job_id: string;
}

export interface StatusResult {
  agent: string;
  progress: number;
  status: string;
}

// ---------------------------------------------------------------------------
// API calls
// ---------------------------------------------------------------------------

export async function uploadImage(file: File): Promise<UploadResult> {
  const form = new FormData();
  form.append("file", file);

  const res = await fetch(`${API_BASE}/upload`, {
    method: "POST",
    body: form,
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Upload failed (${res.status})`);
  }

  return res.json();
}

export async function startProcess(
  params: ProcessParams,
): Promise<ProcessResult> {
  const res = await fetch(`${API_BASE}/process`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(params),
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Process failed (${res.status})`);
  }

  return res.json();
}

export async function getStatus(jobId: string): Promise<StatusResult> {
  const res = await fetch(`${API_BASE}/status/${jobId}`);

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Status check failed (${res.status})`);
  }

  return res.json();
}
