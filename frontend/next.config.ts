import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Build a self-contained server for the Docker image.
  output: "standalone",
  images: {
    // YouTube thumbnails (i.ytimg.com, i1–i9.ytimg.com).
    remotePatterns: [{ protocol: "https", hostname: "**.ytimg.com" }],
  },
};

export default nextConfig;
