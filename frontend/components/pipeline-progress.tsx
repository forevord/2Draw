"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { getStatus, type StatusResult } from "@/lib/api";

const STEPS = [
  { key: "image", label: "Image segmentation", threshold: 10 },
  { key: "color_match", label: "Color matching", threshold: 30 },
  { key: "parallel", label: "Search & painting guide", threshold: 60 },
  { key: "pdf", label: "PDF generation", threshold: 90 },
  { key: "done", label: "Complete", threshold: 100 },
] as const;

const POLL_INTERVAL = 2000;

function stepStatus(progress: number, threshold: number) {
  if (progress > threshold) return "complete";
  if (progress >= threshold) return "active";
  return "pending";
}

export default function PipelineProgress({ jobId }: { jobId: string }) {
  const router = useRouter();
  const [status, setStatus] = useState<StatusResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    let cancelled = false;

    const poll = async () => {
      try {
        const result = await getStatus(jobId);
        if (cancelled) return;
        setStatus(result);
        setError(null);

        if (result.status === "complete") {
          if (intervalRef.current) clearInterval(intervalRef.current);
          router.push(`/preview/${jobId}`);
        } else if (result.status === "failed") {
          if (intervalRef.current) clearInterval(intervalRef.current);
          setError("Processing failed. Please try again.");
        }
      } catch (err) {
        if (cancelled) return;
        setError(err instanceof Error ? err.message : "Connection error");
      }
    };

    poll();
    intervalRef.current = setInterval(poll, POLL_INTERVAL);

    return () => {
      cancelled = true;
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [jobId, router]);

  const progress = status?.progress ?? 0;

  return (
    <div className="mx-auto w-full max-w-md space-y-8">
      {/* Step list */}
      <div className="space-y-3">
        {STEPS.map((step) => {
          const s = stepStatus(progress, step.threshold);
          return (
            <div key={step.key} className="flex items-center gap-3">
              {/* Icon */}
              {s === "complete" && (
                <div className="flex h-6 w-6 items-center justify-center rounded-full bg-pink-500 text-white">
                  <svg className="h-3.5 w-3.5" viewBox="0 0 20 20" fill="currentColor">
                    <path
                      fillRule="evenodd"
                      d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                      clipRule="evenodd"
                    />
                  </svg>
                </div>
              )}
              {s === "active" && (
                <div className="flex h-6 w-6 items-center justify-center rounded-full border-2 border-pink-500">
                  <svg
                    className="h-3.5 w-3.5 animate-spin text-pink-500"
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
                </div>
              )}
              {s === "pending" && (
                <div className="h-6 w-6 rounded-full border-2 border-zinc-200" />
              )}

              {/* Label */}
              <span
                className={`text-sm ${
                  s === "complete"
                    ? "font-medium text-zinc-900"
                    : s === "active"
                      ? "font-medium text-zinc-900"
                      : "text-slate-400"
                }`}
              >
                {step.label}
              </span>
            </div>
          );
        })}
      </div>

      {/* Progress bar */}
      <div>
        <div className="h-2 overflow-hidden rounded-full bg-zinc-100">
          <div
            className="h-full rounded-full bg-pink-500 transition-all duration-500 ease-out"
            style={{ width: `${progress}%` }}
          />
        </div>
        <p className="mt-2 text-center text-sm text-slate-500">{progress}%</p>
      </div>

      {/* Error */}
      {error && (
        <div className="text-center">
          <p className="text-sm text-red-600">{error}</p>
          <Link
            href="/"
            className="mt-3 inline-block rounded-lg border border-zinc-300 px-4 py-2 text-sm font-medium text-zinc-700 hover:bg-zinc-50"
          >
            Back to Upload
          </Link>
        </div>
      )}
    </div>
  );
}
