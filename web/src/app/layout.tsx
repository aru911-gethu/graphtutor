import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "thinknx | Adaptive Personal Learning Agent",
  description: "Learn with adaptive visual themes, dynamic prerequisite graphs, and FSRS spaced repetition.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="bg-[#090d16] text-gray-100 flex flex-col min-h-screen">
        <header className="border-b border-gray-800 bg-[#0d121f]/90 backdrop-blur sticky top-0 z-50">
          <div className="max-w-7xl mx-auto px-4 h-16 flex items-center justify-between">
            <Link href="/" className="flex items-center space-x-2">
              <span className="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center font-bold text-lg text-white shadow-lg shadow-indigo-500/30">
                nx
              </span>
              <span className="text-xl font-bold tracking-tight text-white">thinknx</span>
            </Link>

            <nav className="flex items-center space-x-1 sm:space-x-4 text-sm font-medium">
              <Link href="/dashboard" className="px-3 py-1.5 rounded-md hover:bg-gray-800 text-gray-300 hover:text-white transition">
                Dashboard
              </Link>
              <Link href="/graph" className="px-3 py-1.5 rounded-md hover:bg-gray-800 text-gray-300 hover:text-white transition">
                Graph Canvas
              </Link>
              <Link href="/review" className="px-3 py-1.5 rounded-md hover:bg-gray-800 text-gray-300 hover:text-white transition">
                Reviews
              </Link>
              <Link href="/ingest" className="px-3 py-1.5 rounded-md hover:bg-gray-800 text-gray-300 hover:text-white transition">
                Add Knowledge
              </Link>
              <Link href="/settings" className="px-3 py-1.5 rounded-md hover:bg-gray-800 text-gray-300 hover:text-white transition">
                Settings
              </Link>
            </nav>
          </div>
        </header>

        <main className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6 lg:p-8">
          {children}
        </main>
      </body>
    </html>
  );
}