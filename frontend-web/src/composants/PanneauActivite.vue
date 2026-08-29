<script setup lang="ts">
// Le panneau droit des espaces de travail.
//
// Le panier n'a aucun sens pour un vendeur ou un admin : ce qu'ils veulent
// garder pres de l'oeil, c'est ce qui bouge sur la plateforme. Meme place,
// meme comportement retractable, contenu different.
import { Bell, ChevronsRight, Activity } from '@lucide/vue'

import { usePanier } from '../stores/panier'

const panneau = usePanier()
</script>

<template>
  <aside
    class="hidden shrink-0 flex-col border-l border-trait bg-panneau transition-[width]
           duration-200 lg:flex"
    :class="panneau.ouvert ? 'w-[300px]' : 'w-[52px]'"
  >
    <div
      class="flex shrink-0 items-center border-b border-trait-doux px-3 py-3"
      :class="panneau.ouvert ? 'justify-between' : 'justify-center'"
    >
      <button
        type="button"
        class="bouton-icone"
        :title="panneau.ouvert ? 'Replier le panneau' : 'Ouvrir le panneau'"
        @click="panneau.ouvert = !panneau.ouvert"
      >
        <component :is="panneau.ouvert ? ChevronsRight : Activity" :size="17" />
      </button>
      <b v-if="panneau.ouvert" class="flex-1 pl-2 text-[13px]">Activite</b>
    </div>

    <template v-if="panneau.ouvert">
      <div class="flex flex-1 flex-col items-center justify-center px-6 text-center">
        <span
          class="flex h-12 w-12 items-center justify-center rounded-lg"
          :style="{ background: 'var(--accent-doux)', color: 'var(--accent)' }"
        >
          <Bell :size="20" />
        </span>
        <b class="mt-3 text-[13px]">Rien de nouveau</b>
        <p class="mt-1 text-[12px] text-encre-douce">
          Les changements de statut et les alertes s afficheront ici.
        </p>
      </div>
    </template>
  </aside>
</template>
