import { fileURLToPath, URL } from 'node:url'

import vue from '@vitejs/plugin-vue'
import { defineConfig } from 'vitest/config'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      // Le meme paquet partage que le front web : types, client d'API,
      // regles d'affichage. Voir partager/LISEZ-MOI.md.
      '@partage': fileURLToPath(new URL('../partager/src', import.meta.url)),
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server: {
    // 5174 et non 5173 : le front web occupe deja ce port, et les deux
    // doivent pouvoir tourner en meme temps pendant une demonstration.
    port: 5174,
    // Ecoute sur le reseau local : c'est ainsi qu'on ouvre l'application
    // depuis le navigateur d'un vrai telephone, sans rien reconfigurer.
    host: true,
  },
  test: {
    environment: 'jsdom',
    include: ['src/**/*.test.ts'],
    pool: 'threads',
  },
})
