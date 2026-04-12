import UploadDropzone from "@/components/upload-dropzone";

export default function HomePage() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center px-4 py-16">
      {/* Hero */}
      <div className="mb-16 text-center">
        <h1 className="font-heading text-6xl font-bold tracking-tighter text-zinc-900">
          2Draw
        </h1>
        <p className="mx-auto mt-5 max-w-md text-lg text-slate-500">
          Upload a photo and get a segmented canvas, matched paints, and a
          printable PDF guide — powered by AI.
        </p>
      </div>

      {/* Upload */}
      <UploadDropzone />
    </main>
  );
}
