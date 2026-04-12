"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { startProcess } from "@/lib/api";

type Region = "eu" | "cis" | "global";

const REGIONS: { value: Region; label: string; hint: string }[] = [
  { value: "eu", label: "Europe", hint: "Allegro, Amazon.de" },
  { value: "cis", label: "CIS", hint: "Wildberries" },
  { value: "global", label: "Global", hint: "Amazon.com" },
];

type FormState = "idle" | "submitting" | "error";

export default function SettingsForm({ uploadId }: { uploadId: string }) {
  const router = useRouter();
  const [nClusters, setNClusters] = useState(14);
  const [region, setRegion] = useState<Region>("eu");
  const [state, setState] = useState<FormState>("idle");
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async () => {
    setState("submitting");
    setError(null);

    try {
      const result = await startProcess({
        upload_id: uploadId,
        n_clusters: nClusters,
        region,
      });
      router.push(`/processing/${result.job_id}`);
    } catch (err) {
      setState("error");
      setError(err instanceof Error ? err.message : "Failed to start processing.");
    }
  };

  return (
    <div className="mx-auto w-full max-w-md space-y-8">
      {/* Color Zones Slider */}
      <div>
        <label className="block text-sm font-medium font-heading text-zinc-700">
          Color Zones
        </label>
        <p className="mt-1 text-xs text-slate-400">
          How many distinct color regions to detect
        </p>
        <div className="mt-3 flex items-center gap-4">
          <input
            type="range"
            min={4}
            max={24}
            value={nClusters}
            onChange={(e) => setNClusters(Number(e.target.value))}
            className="h-2 w-full cursor-pointer appearance-none rounded-lg bg-zinc-200 accent-pink-500"
          />
          <span className="w-16 text-right text-sm font-medium text-zinc-900">
            {nClusters} zones
          </span>
        </div>
      </div>

      {/* Region Selector */}
      <div>
        <label className="block text-sm font-medium font-heading text-zinc-700">
          Paint Region
        </label>
        <p className="mt-1 text-xs text-slate-400">
          Where to find paints and buy links
        </p>
        <div className="mt-3 space-y-2">
          {REGIONS.map((r) => (
            <label
              key={r.value}
              className={`flex cursor-pointer items-center gap-3 rounded-lg border px-4 py-3 transition-colors ${
                region === r.value
                  ? "border-pink-500 bg-pink-50"
                  : "border-zinc-200 hover:border-zinc-300"
              }`}
            >
              <input
                type="radio"
                name="region"
                value={r.value}
                checked={region === r.value}
                onChange={() => setRegion(r.value)}
                className="accent-pink-500"
              />
              <div>
                <span className="text-sm font-medium text-zinc-900">
                  {r.label}
                </span>
                <span className="ml-2 text-xs text-slate-400">{r.hint}</span>
              </div>
            </label>
          ))}
        </div>
      </div>

      {/* Error */}
      {error && (
        <p className="text-center text-sm text-red-600">{error}</p>
      )}

      {/* Submit */}
      <button
        onClick={handleSubmit}
        disabled={state === "submitting"}
        className="w-full rounded-lg bg-pink-500 px-6 py-3 text-sm font-medium text-white transition-colors hover:bg-pink-600 disabled:cursor-not-allowed disabled:opacity-50"
      >
        {state === "submitting" ? (
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
            Starting...
          </span>
        ) : (
          "Start Processing"
        )}
      </button>
    </div>
  );
}
