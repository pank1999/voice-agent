import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5173,
    proxy: {
      "/command": "http://localhost:8000",
      "/confirm": "http://localhost:8000",
      "/cancel": "http://localhost:8000",
    },
  },
});
