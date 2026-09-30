/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    const flaskApiUrl = process.env.FLASK_API_URL || "http://localhost:8122";
    return [
      {
        source: "/api/:path*",
        destination: `${flaskApiUrl}/api/:path*`,
      },
      {
        source: "/roadmap/:path*",
        destination: `${flaskApiUrl}/roadmap/:path*`,
      },
    ];
  },

  output: "standalone",

  images: {
    // Serve AVIF first (best compression), then WebP, then original
    formats: ["image/avif", "image/webp"],
    // Cache optimized images for 1 week (604800 seconds)
    minimumCacheTTL: 604800,
    // Only generate sizes that are actually needed
    deviceSizes: [640, 750, 828, 1080, 1200, 1536],
    imageSizes: [16, 32, 48, 64, 96, 128, 256, 384],
  },
};

export default nextConfig;
