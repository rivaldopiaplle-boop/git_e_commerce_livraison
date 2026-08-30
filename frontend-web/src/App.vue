<script setup lang="ts">
// Deux enveloppes seulement :
//
//   pleine page   connexion, inscription, attente de validation
//   coquille      tout le reste — catalogue public compris
//
// Il n'y a qu'une seule structure d'ecran dans ce projet, et c'est celle de
// la maquette. Les filtres ne sont plus passes a la coquille : ils vivent
// dans le contenu, la ou la maquette les place.
import Toast from 'primevue/toast'
import { computed } from 'vue'
import { useRoute } from 'vue-router'

import CoquilleApp from './composants/CoquilleApp.vue'

const route = useRoute()
const pleinePage = computed(() => route.meta.plein === true)
</script>

<template>
  <RouterView v-if="pleinePage" />

  <CoquilleApp v-else>
    <RouterView />
  </CoquilleApp>

  <!-- Les retours d'action, au meme endroit sur tous les ecrans. -->
  <Toast position="bottom-right" />
</template>
