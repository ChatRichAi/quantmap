const createNextIntlPlugin = require('next-intl/plugin');

const withNextIntl = createNextIntlPlugin('./i18n.ts');

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  async rewrites() {
    return [
      {
        source: '/api/proxy/:path*',
        destination: 'http://localhost:8891/api/:path*',
      },
      {
        source: '/api/v1/:path*',
        destination: 'http://localhost:8889/api/v1/:path*',
      },
    ];
  },
};

module.exports = withNextIntl(nextConfig);
