"use client";

import Link from "next/link";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center px-4 py-16">
      <h1 className="font-heading text-3xl font-bold tracking-tight text-zinc-900">
        Something went wrong
      </h1>
      <p className="mt-3 text-sm text-slate-500">{error.message}</p>
      <div className="mt-6 flex gap-3">
        <button
          onClick={reset}
          className="cursor-pointer rounded-lg bg-pink-500 px-6 py-2 text-sm font-medium text-white transition-colors hover:bg-pink-600"
        >
          Try again
        </button>
        <Link
          href="/"
          className="rounded-lg border border-zinc-300 px-6 py-2 text-sm font-medium text-zinc-700 transition-colors hover:bg-zinc-50"
        >
          Back to Upload
        </Link>
      </div>
    </main>
  );
}
