import vue from '@vitejs/plugin-vue'
import { defineConfig } from 'vite'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    // Ecoute aussi sur l'adresse locale du reseau, pour ouvrir le front depuis
    // le navigateur d'un telephone sans rien reconfigurer.
    host: true,
  },
})
