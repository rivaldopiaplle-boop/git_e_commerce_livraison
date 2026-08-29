<script setup lang="ts">
// Le panneau droit des espaces de travail (D-46).
//
// Le panier n'a aucun sens pour un vendeur ou un admin : ce qu'ils veulent
// garder pres de l'oeil, c'est ce qui bouge. Meme place, meme comportement
// retractable que le panier (D-39), contenu different.
//
// Il affichait « Rien de nouveau » en toutes circonstances, ce qui revient a
// occuper trois cents pixels pour ne rien dire. Il montre desormais les
// derniers changements de statut qui concernent le compte connecte.
import { Activity, Bell, ChevronsRight } from '@lucide/vue'
import { computed, ref, watch } from 'vue'

import { espaces, type Notification } from '../api/espaces'
import { useAuthentification } from '../stores/authentification'
import { usePanier } from '../stores/panier'

// Le magasin du panier porte aussi l'etat « panneau ouvert » : les deux
// panneaux se replient au meme endroit, il n'y a donc qu'un etat a tenir.
const panneau = usePanier()
const session = useAuthentification()

const notifications = ref<Notification[]>([])
const chargement = ref(false)

async function charger() {
  if (!session.estConnecte) {
    notifications.value = []
    return
  }
  chargement.value = true
  try {
    notifications.value = (await espaces.notifications.lire()).notifications.slice(0, 12)
  } finally {
    chargement.value = false
  }
}

watch([() => session.estConnecte, () => panneau.ouvert], ([connecte, ouvert]) => {
  if (connecte && ouvert) charger()
}, { immediate: true })

const quand = (date: string) =>
  new Date(date).toLocaleString('fr-FR', {
    day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit',
  })

const titre = computed(() => (session.role === 'ADMIN' ? 'Activite de la plateforme' : 'Activite'))
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
      <b v-if="panneau.ouvert" class="flex-1 pl-2 text-[13px]">{{ titre }}</b>
    </div>

    <template v-if="panneau.ouvert">
      <div v-if="chargement" class="flex-1 px-4 py-4 text-[12px] text-encre-douce">
        Chargement…
      </div>

      <div
        v-else-if="!notifications.length"
        class="flex flex-1 flex-col items-center justify-center px-6 text-center"
      >
        <span
          class="flex h-12 w-12 items-center justify-center rounded-lg"
          :style="{ background: 'var(--accent-doux)', color: 'var(--accent)' }"
        >
          <Bell :size="20" />
        </span>
        <b class="mt-3 text-[13px]">Rien de nouveau</b>
        <p class="mt-1 text-[12px] text-encre-douce">
          Les changements de statut et les alertes s afficheront ici, du plus recent
          au plus ancien.
        </p>
      </div>

      <div v-else class="flex-1 overflow-auto">
        <article
          v-for="notification in notifications"
          :key="notification.id"
          class="flex gap-2.5 border-b border-trait-doux px-4 py-3 text-[12px] last:border-b-0"
        >
          <span
            class="mt-1.5 h-[7px] w-[7px] shrink-0 rounded-full"
            :style="{
              background: notification.lue ? 'var(--color-trait)' : 'var(--accent)',
            }"
          />
          <span class="min-w-0 flex-1">
            <b class="block truncate">{{ notification.titre }}</b>
            <span class="block leading-relaxed text-encre-douce">
              {{ notification.contenu }}
            </span>
            <span class="mt-1 block text-[10.5px] text-encre-douce">
              {{ quand(notification.date) }}
            </span>
          </span>
        </article>
      </div>
    </template>
  </aside>
</template>
