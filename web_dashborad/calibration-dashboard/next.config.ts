import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  typescript: {
    ignoreBuildErrors: true,
  },

  serverExternalPackages: ["bcryptjs", "@prisma/client", "@prisma/adapter-pg"],
};

export default nextConfig;
