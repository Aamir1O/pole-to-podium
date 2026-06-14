import type { Metadata } from "next";
import { Outfit, JetBrains_Mono } from "next/font/google";
import "./globals.css";
import Navbar from "@/components/Navbar";

const outfit = Outfit({
  variable: "--font-sans",
  subsets: ["latin"],
});

const jetbrainsMono = JetBrains_Mono({
  variable: "--font-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Pole to Podium",
  description: "Live constructor standings, ML-powered race prediction models, tyre strategy analyses, and driver comparison metrics for Formula 1.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${outfit.variable} ${jetbrainsMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col bg-black font-sans text-neutral-200">
        <Navbar />
        <main className="flex-1 w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          {children}
        </main>
        <footer className="w-full border-t border-neutral-900 bg-black/40 py-6 text-center text-xs font-mono tracking-widest text-neutral-600 uppercase mt-auto">
          Pole To Podium · Checkered flag data intelligence · 2026
        </footer>
      </body>
    </html>
  );
}
