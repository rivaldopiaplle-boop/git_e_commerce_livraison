<script setup lang="ts">
// « Livrer a … » : le premier geste que fait un visiteur sur une plateforme
// de livraison. Tant qu'il n'a pas repondu, aucune boutique Express ne peut
// s'afficher — et le dire vaut mieux que d'afficher une page a moitie vide.
import { Crosshair, MapPin } from '@lucide/vue'
import { ref } from 'vue'

import { usePosition, VILLES, type Ville } from '../stores/position'

// `clair` : le bandeau vit desormais dans une navbar claire. La prop reste
// pour que l'appelant puisse dire explicitement dans quel contexte il est.
defineProps<{ clair?: boolean }>()

const position = usePosition()
const ouvert = ref(false)

function choisir(ville: Ville) {
  position.choisir(ville)
  ouvert.value = false
}
</script>

<template>
  <div class="relative">
    <button
      type="button"
      class="flex items-center gap-2 rounded-full bg-atelier px-3.5 py-[7px] text-[12.5px]
             transition-colors duration-150 hover:bg-trait-doux"
      @click="ouvert = !ouvert"
    >
      <MapPin :size="14" class="text-[color:var(--accent)]" />
      <span class="text-encre-douce">Livrer a</span>
      <b class="text-encre">{{ position.libelle }}</b>
    </button>

    <Transition
      enter-active-class="transition duration-150"
      enter-from-class="opacity-0 -translate-y-1"
      leave-active-class="transition duration-100"
      leave-to-class="opacity-0"
    >
      <div
        v-if="ouvert"
        class="absolute top-full left-0 z-50 mt-2 w-64 rounded-lg border border-trait
               bg-papier p-2 shadow-lg"
      >
        <button
          type="button"
          class="flex w-full items-center gap-2.5 rounded-xl px-3 py-2.5 text-left text-[13px]
                 text-[color:var(--accent)] transition-colors hover:bg-atelier"
          @click="position.localiser()"
        >
          <Crosshair :size="15" />
          {{ position.localisationEnCours ? 'Localisation…' : 'Utiliser ma position' }}
        </button>

        <div class="my-1.5 border-t border-trait-doux" />

        <button
          v-for="ville in VILLES"
          :key="ville.nom"
          type="button"
          class="flex w-full items-center justify-between rounded-xl px-3 py-2 text-left
                 text-[13.5px] transition-colors hover:bg-atelier"
          :class="position.ville?.nom === ville.nom ? 'text-[color:var(--accent)]' : 'text-encre-douce'"
          @click="choisir(ville)"
        >
          {{ ville.nom }}
          <span v-if="position.ville?.nom === ville.nom" class="text-[11px]">choisie</span>
        </button>
      </div>
    </Transition>
  </div>
</template>
