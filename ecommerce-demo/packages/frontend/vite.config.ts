import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/api/catalog": { target: "http://localhost:4001", changeOrigin: true },
      "/api/cart": { target: "http://localhost:4002", changeOrigin: true },
      "/api/order": { target: "http://localhost:4003", changeOrigin: true }
    }
  }
});
