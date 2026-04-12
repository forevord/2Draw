import PipelineProgress from "@/components/pipeline-progress";

export default function ProcessingPage({
  params,
}: {
  params: { jobId: string };
}) {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center px-4 py-16">
      <div className="mb-10 text-center">
        <h1 className="text-3xl font-bold tracking-tight text-gray-900">
          Processing Your Guide
        </h1>
        <p className="mt-2 text-sm text-gray-400">This may take a minute</p>
      </div>
      <PipelineProgress jobId={params.jobId} />
    </main>
  );
}
