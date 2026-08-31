import { fileURLToPath, URL } from 'node:url'

import tailwindcss from '@tailwindcss/vite'
import vue from '@vitejs/plugin-vue'
// defineConfig vient de vitest/config et non de vite : c'est lui qui connait
// la cle `test`. Sans cela, vue-tsc refuse le fichier de configuration.
import { defineConfig } from 'vitest/config'

export default defineConfig({
  plugins: [vue(), tailwindcss()],
  resolve: {
    alias: {
      // Ce que les deux fronts partagent : types, client d'API, regles
      // d'affichage. Voir partager/LISEZ-MOI.md.
      '@partage': fileURLToPath(new URL('../partager/src', import.meta.url)),
    },
  },
  server: {
    port: 5173,
    // Ecoute aussi sur l'adresse locale du reseau, pour ouvrir le front depuis
    // le navigateur d'un telephone sans rien reconfigurer.
    host: true,
  },
  test: {
    environment: 'jsdom',
    setupFiles: ['./src/tests-preparation.ts'],
    include: ['src/**/*.test.ts'],
    // Fils d'execution plutot que processus separes : sous Windows, le pool
    // par processus expire une fois sur trois au demarrage des ouvriers, et
    // une suite qui echoue au hasard ne sert plus a rien.
    pool: 'threads',
  },
})
