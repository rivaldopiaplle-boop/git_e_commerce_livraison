<script setup lang="ts">
// L'enveloppe des ecrans publics : en-tete, contenu, pied de page.
// La coquille a sidebar, elle, est reservee aux espaces de travail.
import EntetePublic from './EntetePublic.vue'
import PanneauPanier from './PanneauPanier.vue'
import PiedPublic from './PiedPublic.vue'
</script>

<template>
  <div class="flex min-h-screen w-full flex-col">
    <EntetePublic />
    <main class="flex-1">
      <slot />
    </main>
    <PiedPublic />
    <PanneauPanier />
  </div>
</template>
