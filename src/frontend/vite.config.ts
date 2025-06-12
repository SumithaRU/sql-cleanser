// @ts-ignore
import { defineConfig } from "vite";
// @ts-ignore
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      "/compare": "http://localhost:8000",
      "/progress": "http://localhost:8000",
      "/download": "http://localhost:8000",
    },
  },
});
