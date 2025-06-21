import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://backend:5000',
        changeOrigin: true,
        rewrite: path => path.replace(/^\/api/, '/api'),
      },
      '/ollama': {
        target: 'http://ollama:11434',
        changeOrigin: true,
        rewrite: path => path.replace(/^\/ollama/, '/ollama'),
      },
    },
  },
});
