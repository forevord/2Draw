import type { Metadata } from "next";
import Link from "next/link";
import SettingsForm from "@/components/settings-form";

export const metadata: Metadata = { title: "Settings — 2Draw" };

export default function SettingsPage({
  searchParams,
}: {
  searchParams: { uploadId?: string };
}) {
  const uploadId = searchParams.uploadId;

  if (!uploadId) {
    return (
      <main className="flex min-h-screen flex-col items-center justify-center p-8">
        <h1 className="text-2xl font-bold text-zinc-900">
          No image uploaded
        </h1>
        <p className="mt-2 text-slate-500">
          Please upload an image first.
        </p>
        <Link
          href="/"
          className="mt-4 rounded-lg bg-pink-500 px-6 py-2 text-sm font-medium text-white hover:bg-pink-600"
        >
          Go to Upload
        </Link>
      </main>
    );
  }

  return (
    <main className="flex min-h-screen flex-col items-center justify-center px-4 py-16">
      <div className="mb-10 text-center">
        <h1 className="font-heading text-3xl font-bold tracking-tight text-zinc-900">
          Configure Your Guide
        </h1>
        <p className="mt-2 text-slate-500">
          Choose how many color zones and your paint region.
        </p>
      </div>
      <SettingsForm uploadId={uploadId} />
    </main>
  );
}
