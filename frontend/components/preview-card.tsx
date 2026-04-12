"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { getResults, type ResultsResponse } from "@/lib/api";

type CardState = "loading" | "ready" | "error";

export default function PreviewCard({ jobId }: { jobId: string }) {
  const [state, setState] = useState<CardState>("loading");
  const [data, setData] = useState<ResultsResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function fetchResults() {
      try {
        const result = await getResults(jobId);
        if (cancelled) return;
        setData(result);
        setState("ready");
      } catch (err) {
        if (cancelled) return;
        setError(err instanceof Error ? err.message : "Failed to load results");
        setState("error");
      }
    }

    fetchResults();
    return () => {
      cancelled = true;
    };
  }, [jobId]);

  if (state === "loading") {
    return (
      <div className="flex justify-center">
        <svg
          className="h-6 w-6 animate-spin text-gray-400"
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
    );
  }

  if (state === "error") {
    return (
      <div className="text-center">
        <p className="text-sm text-red-600">{error}</p>
        <Link
          href="/"
          className="mt-4 inline-block rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
        >
          Back to Upload
        </Link>
      </div>
    );
  }

  return (
    <div className="mx-auto w-full max-w-md text-center">
      {/* Success icon */}
      <div className="mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-full bg-gray-900">
        <svg
          className="h-8 w-8 text-white"
          viewBox="0 0 20 20"
          fill="currentColor"
        >
          <path
            fillRule="evenodd"
            d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
            clipRule="evenodd"
          />
        </svg>
      </div>

      <h2 className="text-xl font-bold text-gray-900">
        Your guide is ready!
      </h2>
      <p className="mt-2 text-sm text-gray-500">
        Download your PDF paint-by-number guide below.
      </p>

      {/* Download button */}
      {data?.pdf_url ? (
        <a
          href={data.pdf_url}
          target="_blank"
          rel="noopener noreferrer"
          className="mt-6 inline-block rounded-lg bg-gray-900 px-8 py-3 text-sm font-medium text-white transition-colors hover:bg-gray-800"
        >
          Download PDF
        </a>
      ) : (
        <p className="mt-6 text-sm text-gray-400">
          PDF is being prepared...
        </p>
      )}

      {/* Start over */}
      <div className="mt-8">
        <Link
          href="/"
          className="text-sm text-gray-500 underline hover:text-gray-700"
        >
          Create another guide
        </Link>
      </div>
    </div>
  );
}
