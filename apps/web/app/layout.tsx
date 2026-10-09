import type { Metadata, Viewport } from "next";
import type { ReactNode } from "react";
import "@fontsource-variable/inter";
import "@docmorph/ui/styles.css";
import "./globals.css";

export const metadata: Metadata = {
  title: { default: "DocMorph AI", template: "%s · DocMorph AI" },
  description: "Intelligent Documents, Beautiful Experiences",
};

export const viewport: Viewport = {
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#fafafa" },
    { media: "(prefers-color-scheme: dark)", color: "#09090b" },
  ],
};

// Applies the saved theme before first paint so there is no light/dark flash.
const THEME_SCRIPT = `try{var t=localStorage.getItem("dm-theme");if(t==="light"||t==="dark")document.documentElement.dataset.theme=t}catch(e){}`;

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: THEME_SCRIPT }} />
      </head>
      <body>{children}</body>
    </html>
  );
}
