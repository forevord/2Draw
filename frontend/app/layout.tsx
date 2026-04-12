import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "2Draw — AI Paint-by-Number Generator",
  description:
    "Upload a photo and get a segmented canvas, matched paints, and a printable PDF guide.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-zinc-50 font-body antialiased">{children}</body>
    </html>
  );
}
