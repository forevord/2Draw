export default function SettingsPage({
  searchParams,
}: {
  searchParams: { uploadId?: string };
}) {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-8">
      <h1 className="text-3xl font-bold tracking-tight text-gray-900">
        Settings
      </h1>
      <p className="mt-4 text-gray-500">
        Upload ID: {searchParams.uploadId ?? "—"}
      </p>
      <p className="mt-2 text-sm text-gray-400">
        Configure zones, brands, and region. Coming in PS-11.
      </p>
    </main>
  );
}
