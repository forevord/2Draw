import Link from "next/link";
import SettingsForm from "@/components/settings-form";

export default function SettingsPage({
  searchParams,
}: {
  searchParams: { uploadId?: string };
}) {
  const uploadId = searchParams.uploadId;

  if (!uploadId) {
    return (
      <main className="flex min-h-screen flex-col items-center justify-center p-8">
        <h1 className="text-2xl font-bold text-gray-900">
          No image uploaded
        </h1>
        <p className="mt-2 text-gray-500">
          Please upload an image first.
        </p>
        <Link
          href="/"
          className="mt-4 rounded-lg bg-gray-900 px-6 py-2 text-sm font-medium text-white hover:bg-gray-800"
        >
          Go to Upload
        </Link>
      </main>
    );
  }

  return (
    <main className="flex min-h-screen flex-col items-center justify-center px-4 py-16">
      <div className="mb-10 text-center">
        <h1 className="text-3xl font-bold tracking-tight text-gray-900">
          Configure Your Guide
        </h1>
        <p className="mt-2 text-gray-500">
          Choose how many color zones and your paint region.
        </p>
      </div>
      <SettingsForm uploadId={uploadId} />
    </main>
  );
}
