import type { NextConfig } from "next";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

const nextConfig: NextConfig = {
  allowedDevOrigins: ["127.0.0.1"],
  // 백엔드 프록시 — 브라우저 fetch는 절대 URL 대신 /api/backend 경유(루트 CLAUDE.md 규칙).
  async rewrites() {
    return [
      {
        source: "/api/backend/:path*",
        destination: `${API_BASE}/:path*`,
      },
    ];
  },
};

export default nextConfig;
