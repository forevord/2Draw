export default function PreviewPage({
  params,
}: {
  params: { jobId: string };
}) {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-8">
      <h1 className="text-3xl font-bold tracking-tight text-gray-900">
        Preview
      </h1>
      <p className="mt-4 text-gray-500">Job: {params.jobId}</p>
      <p className="mt-2 text-sm text-gray-400">
        Canvas preview and palette coming in PS-13.
      </p>
    </main>
  );
}
