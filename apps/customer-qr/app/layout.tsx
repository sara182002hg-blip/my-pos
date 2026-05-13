import type { ReactNode } from "react";
import type { Metadata, Viewport } from "next";
import PwaInstall from "./pwa-install";
import "./globals.css";

export const metadata: Metadata = {
  title: "MyPOS QR Ordering",
  description: "Scan, order, and request bill from your table.",
  applicationName: "MyPOS QR",
  manifest: "/manifest.webmanifest",
  icons: {
    icon: "/icons/icon.svg",
    apple: "/icons/icon.svg"
  },
  appleWebApp: {
    capable: true,
    title: "MyPOS QR",
    statusBarStyle: "black-translucent"
  }
};

export const viewport: Viewport = {
  themeColor: "#09131c"
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="th">
      <body>
        {children}
        <PwaInstall />
      </body>
    </html>
  );
}
