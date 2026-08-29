<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'

import CoquilleApp from './composants/CoquilleApp.vue'
import DispositionPublique from './composants/DispositionPublique.vue'

const route = useRoute()

// Trois enveloppes possibles :
//   pleine page   connexion, inscription, attente de validation
//   publique      en-tete + pied de page : le magasin
//   coquille      sidebar + navbar : les espaces de travail
const disposition = computed(() => {
  if (route.meta.plein) return 'pleine'
  return route.meta.acces === 'public' ? 'publique' : 'coquille'
})
</script>

<template>
  <RouterView v-if="disposition === 'pleine'" />

  <DispositionPublique v-else-if="disposition === 'publique'">
    <RouterView />
  </DispositionPublique>

  <CoquilleApp v-else>
    <RouterView />
  </CoquilleApp>
</template>
