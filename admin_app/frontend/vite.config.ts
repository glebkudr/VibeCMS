import { defineConfig } from 'vite';
import path from 'path';

// https://vitejs.dev/config/
export default defineConfig(({ command }) => ({
  root: '.', // Source files are in admin_app/frontend
  base: command === 'serve' ? '/' : '/static/admin_dist/', // Dynamic base for dev/prod
  optimizeDeps: {
    // Исключаем проблемные Milkdown плагины из предобработки (pre-bundling)
    exclude: [
      '@milkdown/plugin-slash',
      '@milkdown/plugin-block',
      // Добавьте другие плагины, если потребуется
    ],
    // include: [], // Можно убрать или оставить пустым, если не требуется
  },
  build: {
    // Output directory relative to the project root (where manage.py is)
    // We want it inside admin_app/static for FastAPI to serve it
    outDir: path.resolve(__dirname, '../static/admin_dist'),
    emptyOutDir: true, // Clear output directory before building
    manifest: true, // Generate manifest.json
    rollupOptions: {
      // Define the entry point for the application
      input: {
        main: path.resolve(__dirname, 'src/main.ts'),
      },
    },
    // Sourcemaps are useful for debugging production issues
    sourcemap: command === 'serve' ? 'inline' : true,
    commonjsOptions: {
        // Help Vite/Rollup process CJS dependencies smoothly
        include: [/node_modules/],
        // Sometimes needed for specific CJS packages:
        // transformMixedEsModules: true,
    },
  },
  server: {
    // Configure how Vite serves files during development
    origin: 'http://localhost:5173', // Origin for HMR and asset requests
    // If you need HMR (Hot Module Replacement) with Docker, further
    // configuration might be needed (e.g., host, port forwarding)
  },
})); 