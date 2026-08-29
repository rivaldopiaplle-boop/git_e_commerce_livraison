<script setup lang="ts">
// La popup de la maquette : 380 px, un titre, une phrase qui explique ce que
// l'action va faire, le formulaire, deux boutons a droite.
//
// « Popups pour les actions courtes » est une regle d'or (n°9), et la
// maquette en decrit quatre. Ajuster un stock dans un formulaire deplie sous
// une ligne de liste, c'est justement ce qu'elle voulait eviter : on ne sait
// plus ce qu'on modifie ni ou finit le formulaire.
import { X } from '@lucide/vue'
import { onMounted, onUnmounted } from 'vue'

defineProps<{ titre: string; explication?: string }>()
const emission = defineEmits<{ fermer: [] }>()

// Echap ferme : une popup qu'on ne peut fermer qu'a la souris est un piege
// au clavier.
function auClavier(evenement: KeyboardEvent) {
  if (evenement.key === 'Escape') emission('fermer')
}
onMounted(() => document.addEventListener('keydown', auClavier))
onUnmounted(() => document.removeEventListener('keydown', auClavier))
</script>

<template>
  <div
    class="fixed inset-0 z-[200] flex animate-[voile_0.15s_ease-out] items-center justify-center
           bg-[rgba(10,12,18,0.45)] px-4"
    role="dialog"
    aria-modal="true"
    @click.self="emission('fermer')"
  >
    <div
      class="w-full max-w-[420px] animate-[apparition_0.2s_ease-out] rounded-[14px] bg-papier
             p-6 shadow-[0_10px_30px_-12px_rgba(15,20,32,0.4)]"
    >
      <div class="flex items-start justify-between gap-4">
        <h4 class="text-[14.5px] font-bold">{{ titre }}</h4>
        <button type="button" class="bouton-icone -mt-1 -mr-1" title="Fermer"
                @click="emission('fermer')">
          <X :size="16" />
          <span class="sr-only">Fermer</span>
        </button>
      </div>

      <p v-if="explication" class="mt-1.5 text-[12.5px] leading-relaxed text-encre-douce">
        {{ explication }}
      </p>

      <div class="mt-4">
        <slot />
      </div>

      <div class="mt-5 flex justify-end gap-2">
        <slot name="actions" />
      </div>
    </div>
  </div>
</template>
