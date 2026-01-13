import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";
import type { ProxyOptions } from "vite";

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");
  const apiBase = (env.VITE_API_BASE_URL ?? "").replace(/\/+$/, "");
  const proxy: Record<string, string | ProxyOptions> = apiBase
    ? { "/api": { target: apiBase, changeOrigin: true } }
    : {
        "/api/catalog": { target: "http://localhost:4001", changeOrigin: true },
        "/api/cart": { target: "http://localhost:4002", changeOrigin: true },
        "/api/order": { target: "http://localhost:4003", changeOrigin: true }
      };

  return {
    plugins: [react()],
    server: {
      proxy
    }
  };
});
