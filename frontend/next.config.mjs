/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    const flaskApiUrl = process.env.FLASK_API_URL || "http://localhost:8122";
    return [
      {
        source: "/api/:path*",
        destination: `${flaskApiUrl}/api/:path*`,
      },
    ];
  },

  async redirects() {
    // Pricing used to live at /plans; keep old links and any indexed URL working.
    return [{ source: "/plans", destination: "/pricing", permanent: true }];
  },

  async headers() {
    // /_next/static (JS, CSS, self-hosted fonts) is content-hashed and Next already serves it as
    // `immutable` for a year. Files in /public keep their names between deploys, so they get a
    // long cache plus stale-while-revalidate: repeat visits paint from the browser cache at once
    // and a changed file is picked up in the background.
    const publicAssetCache = "public, max-age=2592000, stale-while-revalidate=604800";
    return [
      // Skips /_next/* (already immutable) and the generated /icon.svg route (already immutable).
      { source: "/:file((?!_next/|icon\\.svg).*\\.(?:png|jpg|jpeg|webp|avif|gif|svg|ico|woff2?))", headers: [{ key: "Cache-Control", value: publicAssetCache }] },
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
