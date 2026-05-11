import type { NextConfig } from "next";

const config: NextConfig = {
  reactStrictMode: true,
  async rewrites() {
    const api = (process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8787").trim().replace(/\/+$/, "");
    return [{ source: "/api/:path*", destination: `${api}/:path*` }];
  },
};

export default config;
