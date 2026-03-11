import type { Metadata } from "next";
import { IBM_Plex_Mono, Instrument_Serif, Manrope } from "next/font/google";
import type { ReactNode } from "react";
import "./globals.css";

const bodyFont = Manrope({
  variable: "--font-body",
  subsets: ["latin"],
});

const monoFont = IBM_Plex_Mono({
  variable: "--font-mono",
  subsets: ["latin"],
  weight: ["400", "500"],
});

const displayFont = Instrument_Serif({
  variable: "--font-display",
  subsets: ["latin"],
  weight: "400",
});

export const metadata: Metadata = {
  title: "RelayOps",
  description: "Operations workflow platform for orchestrating requests, summaries, and downstream system execution.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={`${bodyFont.variable} ${monoFont.variable} ${displayFont.variable} antialiased`}>{children}</body>
    </html>
  );
}
