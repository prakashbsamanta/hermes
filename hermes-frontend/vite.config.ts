/// <reference types="vitest" />
import path from "path";
import { fileURLToPath } from "url";
import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  test: {
    globals: true,
    environment: "jsdom",
    setupFiles: "./vitest.setup.ts",
    coverage: {
      provider: "v8",
      reporter: ["text", "json", "html"],
      thresholds: {
        lines: 90,
        functions: 75,
        branches: 80,
        statements: 90,
      },
    },
  },
});
