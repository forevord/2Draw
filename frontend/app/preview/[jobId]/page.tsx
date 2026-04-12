import PreviewCard from "@/components/preview-card";

export default function PreviewPage({
  params,
}: {
  params: { jobId: string };
}) {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center px-4 py-16">
      <PreviewCard jobId={params.jobId} />
    </main>
  );
}
