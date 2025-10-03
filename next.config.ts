import type { NextConfig } from "next";

const isDev = process.env.NODE_ENV === 'development';
const isTauriDev = process.env.TAURI_DEV === 'true' || process.argv.includes('tauri:dev');

const nextConfig: NextConfig = {
  // Только экспорт для production билда, не для Tauri dev режима
  ...(isDev || isTauriDev ? {} : { output: 'export' }),
  trailingSlash: true,
  images: {
    unoptimized: true
  },
  // Убираем assetPrefix - для Tauri не нужен
  experimental: {
    esmExternals: true
  }
};

export default nextConfig;
