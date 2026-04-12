"use client";

import { useCallback, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { uploadImage } from "@/lib/api";

const MAX_SIZE = 20 * 1024 * 1024; // 20 MB
const ACCEPTED_TYPES = ["image/jpeg", "image/png"];

type UploadState = "idle" | "selected" | "uploading" | "error";

export default function UploadDropzone() {
  const router = useRouter();
  const inputRef = useRef<HTMLInputElement>(null);
  const [state, setState] = useState<UploadState>("idle");
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [dragOver, setDragOver] = useState(false);

  const handleFile = useCallback((f: File) => {
    setError(null);

    if (!ACCEPTED_TYPES.includes(f.type)) {
      setError("Only JPEG and PNG files are supported.");
      return;
    }
    if (f.size > MAX_SIZE) {
      setError("File must be under 20 MB.");
      return;
    }

    setFile(f);
    setPreview(URL.createObjectURL(f));
    setState("selected");
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragOver(false);
      const f = e.dataTransfer.files[0];
      if (f) handleFile(f);
    },
    [handleFile],
  );

  const handleUpload = async () => {
    if (!file) return;

    setState("uploading");
    setError(null);

    try {
      const result = await uploadImage(file);
      router.push(`/settings?uploadId=${result.upload_id}`);
    } catch (err) {
      setState("error");
      setError(err instanceof Error ? err.message : "Upload failed.");
    }
  };

  const reset = () => {
    setFile(null);
    setPreview(null);
    setState("idle");
    setError(null);
    if (inputRef.current) inputRef.current.value = "";
  };

  return (
    <div className="mx-auto w-full max-w-lg">
      {/* Dropzone area */}
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setDragOver(true);
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
        onClick={() => state === "idle" && inputRef.current?.click()}
        className={`relative flex min-h-[240px] cursor-pointer flex-col items-center justify-center rounded-2xl border-2 border-dashed transition-colors ${
          dragOver
            ? "border-pink-500 bg-pink-50"
            : "border-zinc-300 hover:border-zinc-400"
        } ${state !== "idle" ? "cursor-default" : ""}`}
      >
        <input
          ref={inputRef}
          type="file"
          accept="image/jpeg,image/png"
          className="hidden"
          onChange={(e) => {
            const f = e.target.files?.[0];
            if (f) handleFile(f);
          }}
        />

        {state === "idle" && (
          <div className="text-center">
            <svg
              className="mx-auto mb-3 h-10 w-10 text-zinc-400"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
              <polyline points="17 8 12 3 7 8" />
              <line x1="12" y1="3" x2="12" y2="15" />
            </svg>
            <p className="text-sm font-medium text-zinc-600">
              Drop an image here or click to browse
            </p>
            <p className="mt-1 text-xs text-slate-400">JPEG or PNG, up to 20 MB</p>
          </div>
        )}

        {preview && state !== "idle" && (
          <div className="flex flex-col items-center gap-4 p-4">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={preview}
              alt="Preview"
              className="max-h-48 rounded-lg object-contain"
            />
            <p className="text-sm text-slate-500">{file?.name}</p>
          </div>
        )}
      </div>

      {/* Error message */}
      {error && (
        <p className="mt-3 text-center text-sm text-red-600">{error}</p>
      )}

      {/* Action buttons */}
      {state === "selected" && (
        <div className="mt-4 flex justify-center gap-3">
          <button
            onClick={reset}
            className="cursor-pointer rounded-lg border border-zinc-300 px-4 py-2 text-sm font-medium text-zinc-700 transition-colors hover:bg-zinc-50"
          >
            Change
          </button>
          <button
            onClick={handleUpload}
            className="cursor-pointer rounded-lg bg-pink-500 px-6 py-2 text-sm font-medium text-white transition-colors hover:bg-pink-600"
          >
            Upload & Continue
          </button>
        </div>
      )}

      {state === "uploading" && (
        <div className="mt-4 flex justify-center">
          <div className="flex items-center gap-2 text-sm text-slate-500">
            <svg
              className="h-4 w-4 animate-spin"
              viewBox="0 0 24 24"
              fill="none"
            >
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
              />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
              />
            </svg>
            Uploading...
          </div>
        </div>
      )}

      {state === "error" && (
        <div className="mt-4 flex justify-center">
          <button
            onClick={reset}
            className="cursor-pointer rounded-lg border border-zinc-300 px-4 py-2 text-sm font-medium text-zinc-700 transition-colors hover:bg-zinc-50"
          >
            Try again
          </button>
        </div>
      )}
    </div>
  );
}
