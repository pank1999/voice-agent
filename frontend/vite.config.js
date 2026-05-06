import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

const API_ROUTES = [
  "/command",
  "/confirm",
  "/cancel",
  "/todos",
  "/reminders",
  "/transcribe",
];

export default defineConfig({
  plugins: [react(), tailwindcss()],
  base: "./",
  build: {
    outDir: "dist",
    emptyOutDir: true,
  },
  server: {
    port: 5173,
    proxy: Object.fromEntries(
      API_ROUTES.map((r) => [r, "http://localhost:8000"]),
    ),
  },
});
