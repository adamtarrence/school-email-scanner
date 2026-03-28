import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "SchoolSkim - Your school emails, skimmed.",
  description:
    "Turn the firehose of school emails into a 2-minute daily digest. Action items, events, and updates — grouped by child.",
  openGraph: {
    title: "SchoolSkim - Your school emails, skimmed.",
    description:
      "Turn the firehose of school emails into a 2-minute daily digest.",
    type: "website",
    url: "https://schoolskim.com",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={inter.className}>
      <body className="min-h-screen bg-white text-gray-900 antialiased">
        {children}
      </body>
    </html>
  );
}
