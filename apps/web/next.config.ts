import type { NextConfig } from "next";

const apiUrl = process.env.DOCMORPH_API_URL ?? "http://localhost:8000";

const nextConfig: NextConfig = {
  // Docker builds set DOCMORPH_STANDALONE=1 to emit a minimal self-contained server.
  output: process.env.DOCMORPH_STANDALONE === "1" ? "standalone" : undefined,
  poweredByHeader: false,
  // The browser talks to the API through /api on the web origin, so there is no
  // CORS surface in the default deployment.
  async rewrites() {
    return [{ source: "/api/:path*", destination: `${apiUrl}/:path*` }];
  },
  async headers() {
    return [
      {
        source: "/:path*",
        headers: [
          { key: "X-Content-Type-Options", value: "nosniff" },
          { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
          { key: "X-Frame-Options", value: "DENY" },
        ],
      },
    ];
  },
};

export default nextConfig;
