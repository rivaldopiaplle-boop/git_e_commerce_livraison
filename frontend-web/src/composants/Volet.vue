<script setup lang="ts">
// Ce qu'un écran met dans le panneau de droite.
//
// Usage, dans n'importe quelle vue :
//
//   <Volet titre="Commande RD-260830-A1">
//     …le détail de ce qui est sélectionné…
//   </Volet>
//
// Le panneau reste au même endroit et garde son comportement rétractable
// (D-39) : c'est son contenu qui suit l'écran, pas sa position.
import { onBeforeUnmount, onMounted } from 'vue'

import { useVolet } from '../stores/volet'

const props = defineProps<{ titre: string }>()
const volet = useVolet()

onMounted(() => volet.ouvrir(props.titre))
onBeforeUnmount(() => volet.fermer())
</script>

<template>
  <Teleport to="#volet-cible" defer>
    <div class="animate-[apparition_0.2s_ease-out]">
      <slot />
    </div>
  </Teleport>
</template>
