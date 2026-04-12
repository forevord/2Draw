"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  createCheckout,
  getResults,
  type ResultsResponse,
} from "@/lib/api";

type CardState = "loading" | "ready" | "error" | "checking_out";

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
        setError(
          err instanceof Error ? err.message : "Failed to load results",
        );
        setState("error");
      }
    }

    fetchResults();
    return () => {
      cancelled = true;
    };
  }, [jobId]);

  const handleCheckout = async () => {
    setState("checking_out");
    setError(null);
    try {
      const result = await createCheckout(jobId);
      window.location.href = result.session_url;
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Checkout failed",
      );
      setState("ready");
    }
  };

  if (state === "loading") {
    return (
      <div className="flex justify-center">
        <svg
          className="h-6 w-6 animate-spin text-slate-400"
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
          className="mt-4 inline-block rounded-lg border border-zinc-300 px-4 py-2 text-sm font-medium text-zinc-700 hover:bg-zinc-50"
        >
          Back to Upload
        </Link>
      </div>
    );
  }

  const isPaid = data?.paid === true;

  return (
    <div className="mx-auto w-full max-w-md text-center">
      {/* Success icon */}
      <div className="mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-full bg-pink-500">
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

      <h2 className="font-heading text-xl font-bold text-zinc-900">
        Your guide is ready!
      </h2>
      <p className="mt-2 text-sm text-slate-500">
        {isPaid
          ? "Download your PDF paint-by-number guide below."
          : "Purchase to download your PDF paint-by-number guide."}
      </p>

      {/* Error inline */}
      {error && (
        <p className="mt-3 text-sm text-red-600">{error}</p>
      )}

      {/* CTA: Download (paid) or Purchase (unpaid) */}
      {isPaid && data?.pdf_url ? (
        <a
          href={data.pdf_url}
          target="_blank"
          rel="noopener noreferrer"
          className="mt-6 inline-block rounded-lg bg-zinc-900 px-8 py-3 text-sm font-medium text-white transition-colors hover:bg-zinc-800"
        >
          Download PDF
        </a>
      ) : (
        <button
          onClick={handleCheckout}
          disabled={state === "checking_out"}
          className="mt-6 cursor-pointer rounded-lg bg-pink-500 px-8 py-3 text-sm font-medium text-white transition-colors hover:bg-pink-600 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {state === "checking_out" ? (
            <span className="flex items-center justify-center gap-2">
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
              Redirecting...
            </span>
          ) : (
            "Purchase PDF — $2.99"
          )}
        </button>
      )}

      {/* Start over */}
      <div className="mt-8">
        <Link
          href="/"
          className="text-sm text-pink-500 underline hover:text-pink-600"
        >
          Create another guide
        </Link>
      </div>
    </div>
  );
}
