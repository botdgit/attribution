import { defineConfig } from "vite";
import react from "@vitejs/plugin-react-swc";
import path from "path";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "src")
    }
  }
  ,
  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (id.includes('node_modules')) {
            // Keep firebase in its own chunk, but bundle all other node_modules
            // (including react and libraries that depend on it) into a single
            // `vendor` chunk to avoid cross-chunk React interop/load-order issues.
            if (id.includes('firebase')) return 'vendor_firebase';
            return 'vendor';
          }
        }
      }
    }
  }
});
