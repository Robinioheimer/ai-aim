/** @type {import('next').NextConfig} */
const nextConfig = {
  typescript: {
    // CI runs `pnpm typecheck` separately; keep build strict about everything else.
    ignoreBuildErrors: false,
  },
  images: {
    unoptimized: true,
  },
}

export default nextConfig
