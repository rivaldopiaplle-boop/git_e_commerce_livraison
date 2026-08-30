<script setup lang="ts">
// La popup du projet, posée sur le **Dialog de PrimeVue**.
//
// « Popups pour les actions courtes » est une règle d'or (n°9), et D-26
// impose PrimeVue précisément pour ne pas redessiner à la main les fenêtres.
// Ce que je gagne à ne plus la dessiner : le piège de focus, la fermeture par
// Échap, le voile, le retour du focus au bouton d'origine, les rôles ARIA.
// Autant de choses qu'on oublie toujours dans une modale maison.
//
// L'interface publique ne change pas : `titre`, `explication`, le contenu par
// défaut et l'emplacement `actions`.
import Dialog from 'primevue/dialog'
import { ref, watch } from 'vue'

defineProps<{ titre: string; explication?: string }>()
const emission = defineEmits<{ fermer: [] }>()

// PrimeVue pilote sa visibilité par `v-model` ; l'écran, lui, monte et démonte
// la popup avec un `v-if`. On ouvre donc au montage et on prévient l'écran
// quand PrimeVue se referme.
const ouverte = ref(true)
watch(ouverte, (valeur) => {
  if (!valeur) emission('fermer')
})
</script>

<template>
  <Dialog
    v-model:visible="ouverte"
    modal
    :draggable="false"
    :header="titre"
    :style="{ width: '440px' }"
    :breakpoints="{ '520px': '94vw' }"
    :pt="{ root: { class: 'carte-popup' } }"
  >
    <p v-if="explication" class="-mt-1 mb-4 text-[12.5px] leading-relaxed text-encre-douce">
      {{ explication }}
    </p>

    <slot />

    <template #footer>
      <div class="flex w-full justify-end gap-2">
        <slot name="actions" />
      </div>
    </template>
  </Dialog>
</template>

<style>
/* Le Dialog est téléporté hors du composant : son style ne peut pas être
   `scoped`, sinon il ne l'atteint jamais. */
.carte-popup .p-dialog-header {
  padding: 1.25rem 1.375rem 0.5rem;
  font-size: 14.5px;
  font-weight: 700;
}
.carte-popup .p-dialog-content {
  padding: 0 1.375rem 0.5rem;
}
.carte-popup .p-dialog-footer {
  padding: 0.75rem 1.375rem 1.25rem;
}
</style>
