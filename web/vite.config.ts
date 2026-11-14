import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5173,
    // WSL: file events from Windows-side editors are unreliable
    watch: { usePolling: true, interval: 300 },
  },
});
