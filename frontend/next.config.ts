import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: 'via.placeholder.com',
        port: '',
        pathname: '/**',
      },
      {
        protocol: 'https',
        hostname: 'www.martel.ch',
        port: '',
        pathname: '/thumbnail/**',
      },
    ],
  },
};

export default nextConfig;
