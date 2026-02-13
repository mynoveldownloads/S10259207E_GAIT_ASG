import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
    plugins: [react()],
    server: {
        port: 3000,
        host: '0.0.0.0',
        strictPort: true,
        allowedHosts: true,
        cors: true,
        hmr: {
            host: 'home3.localhost.rodeo',
            protocol: 'ws'
        },
        proxy: {
            '/api': {
                target: 'http://localhost:5000',
                changeOrigin: true,
                secure: false
            }
        }
    }
})
