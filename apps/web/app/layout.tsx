import type { Metadata } from "next";
import type { ReactNode } from "react";
import "@docmorph/ui/styles.css";
import "./globals.css";
import { TopNav } from "@/components/TopNav";

export const metadata: Metadata = {
  title: "DocMorph AI",
  description: "Intelligent Documents, Beautiful Experiences",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>
        <TopNav />
        {children}
      </body>
    </html>
  );
}
