import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "export",
  distDir: "build",
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: "https://biohue.onrender.com/api/:path*",
      },
    ];
  },
};

export default nextConfig;
