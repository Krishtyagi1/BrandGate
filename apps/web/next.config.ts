import type { NextConfig } from "next";
const config: NextConfig = {
  distDir: process.env.INKLOOM_BUILD_DIR || ".next",
  poweredByHeader: false,
  // Small SSE messages must reach the client before the run finishes.
  compress: false,
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${process.env.INKLOOM_API_ORIGIN || "http://127.0.0.1:8000"}/api/:path*`,
      },
    ];
  },
  async headers() {
    return [
      {
        source: "/:path*",
        headers: [
          { key: "X-Content-Type-Options", value: "nosniff" },
          { key: "Referrer-Policy", value: "same-origin" },
          { key: "X-Frame-Options", value: "DENY" },
          {
            key: "Content-Security-Policy",
            value:
              "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; worker-src 'self' blob:; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; font-src 'self' data:; connect-src 'self'; frame-src 'self' blob:; object-src 'none'; base-uri 'self'; form-action 'self'",
          },
        ],
      },
    ];
  },
};
export default config;
