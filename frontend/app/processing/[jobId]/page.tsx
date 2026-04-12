import type { Metadata } from "next";
import PipelineProgress from "@/components/pipeline-progress";

export const metadata: Metadata = { title: "Processing — 2Draw" };

export default function ProcessingPage({
  params,
}: {
  params: { jobId: string };
}) {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center px-4 py-16">
      <div className="mb-10 text-center">
        <h1 className="font-heading text-3xl font-bold tracking-tight text-zinc-900">
          Processing Your Guide
        </h1>
        <p className="mt-2 text-sm text-slate-400">This may take a minute</p>
      </div>
      <PipelineProgress jobId={params.jobId} />
    </main>
  );
}
