import { defineConfig } from 'vite';
import path from 'path';

// https://vitejs.dev/config/
export default defineConfig(({ command }) => ({
  // исходники лежат в admin_app/frontend
  root: '.',

  // для dev — /, для production — FastAPI будет отдавать из /static/admin_dist/
  base: command === 'serve' ? '/' : '/static/admin_dist/',

  /* ──────────────── alias ──────────────── */
  resolve: {
    alias: {
      // @shared → ПРОЕКТ_ROOT/shared
      '@shared': path.resolve(__dirname, '../../shared'),
    },
  },

  /* ──────────────── dev‑server ──────────────── */
  server: {
    origin: 'http://localhost:5173',
    // разрешаем читать файлы на уровни выше frontend/
    fs: { allow: ['..', '../..'] },
  },

  /* ──────────────── deps/optimize ──────────────── */
  optimizeDeps: {
    exclude: [
      '@milkdown/plugin-slash',
      '@milkdown/plugin-block',
    ],
  },

  /* ──────────────── build ──────────────── */
  build: {
    // итог кладём в admin_app/static/admin_dist
    outDir: path.resolve(__dirname, '../static/admin_dist'),
    emptyOutDir: true,
    manifest: true,
    rollupOptions: {
      input: { main: path.resolve(__dirname, 'src/main.ts') },
    },
    sourcemap: command === 'serve' ? 'inline' : true,
    commonjsOptions: { include: [/node_modules/] },
  },
}));
