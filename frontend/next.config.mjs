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
};

export default nextConfig;
