import type { Metadata } from "next";
import { Geist } from "next/font/google";
import "./globals.css";

const geist = Geist({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Olimpia Milano Analytics",
  description: "EA7 Emporio Armani Milano — Basketball Analytics",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="it" className="h-full">
      <body className={`${geist.className} bg-gray-950 text-white min-h-full`}>{children}</body>
    </html>
  );
}
