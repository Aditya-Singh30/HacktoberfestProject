import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5173,
    proxy: {
      "/extract": "http://127.0.0.1:8000",
      "/ask": "http://127.0.0.1:8000",
      "/health": "http://127.0.0.1:8000",
      "/buildings": "http://127.0.0.1:8000",
    },
  },
});
