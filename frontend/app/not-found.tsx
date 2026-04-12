import Link from "next/link";

export default function NotFound() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center px-4 py-16">
      <h1 className="font-heading text-6xl font-bold tracking-tighter text-zinc-900">
        404
      </h1>
      <p className="mt-3 text-lg text-slate-500">Page not found</p>
      <Link
        href="/"
        className="mt-6 rounded-lg bg-pink-500 px-6 py-2 text-sm font-medium text-white transition-colors hover:bg-pink-600"
      >
        Back to Upload
      </Link>
    </main>
  );
}
