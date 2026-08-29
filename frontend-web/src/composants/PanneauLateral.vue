<script setup lang="ts">
// Le panneau droit de la maquette : 300 px, fond clair, retractable.
//
// Replie, il laisse une bande ou le compteur du panier reste visible : c'est
// « stable mais retractable », pas une fenetre qui surgit puis disparait.
import { AlertTriangle, Bell, ChevronsRight, ShoppingCart, Trash2 } from '@lucide/vue'
import { computed } from 'vue'

import { usePanier } from '../stores/panier'

const panier = usePanier()

const euros = (centimes: number) =>
  (centimes / 100).toLocaleString('fr-FR', { style: 'currency', currency: 'EUR' })

const vide = computed(() => panier.contenu.lignes.length === 0)
</script>

<template>
  <aside
    class="hidden shrink-0 flex-col border-l border-trait bg-panneau transition-[width]
           duration-200 lg:flex"
    :class="panier.ouvert ? 'w-[300px]' : 'w-[52px]'"
  >
    <div
      class="flex shrink-0 items-center border-b border-trait-doux px-3 py-3"
      :class="panier.ouvert ? 'justify-between' : 'justify-center'"
    >
      <button
        type="button"
        class="bouton-icone relative"
        :title="panier.ouvert ? 'Replier le panier' : 'Ouvrir le panier'"
        @click="panier.ouvert = !panier.ouvert"
      >
        <component :is="panier.ouvert ? ChevronsRight : ShoppingCart" :size="17" />
        <span
          v-if="!panier.ouvert && panier.nombreArticles"
          class="absolute -top-0.5 -right-0.5 flex h-[15px] min-w-[15px] items-center
                 justify-center rounded-full px-1 text-[9.5px] font-bold text-white"
          :style="{ background: 'var(--accent)' }"
        >
          {{ panier.nombreArticles }}
        </span>
      </button>

      <b v-if="panier.ouvert" class="flex-1 pl-2 text-[13px]">Mon panier</b>
      <span
        v-if="panier.ouvert && panier.nombreArticles"
        class="badge text-white"
        :style="{ background: 'var(--accent)' }"
      >
        {{ panier.nombreArticles }}
      </span>
    </div>

    <template v-if="panier.ouvert">
      <p
        v-if="panier.erreur"
        class="mx-4 mt-3 rounded-lg bg-[#fbe4e2] px-3 py-2 text-[12px] text-[#9c2116]"
      >
        {{ panier.erreur }}
      </p>

      <div v-if="!vide" class="flex-1 overflow-y-auto px-4">
        <div
          v-for="ligne in panier.contenu.lignes"
          :key="ligne.id"
          class="flex items-center gap-2.5 border-b border-trait-doux py-2.5"
        >
          <img
            v-if="ligne.produit.image"
            :src="ligne.produit.image"
            :alt="ligne.produit.nom"
            class="h-10 w-10 shrink-0 rounded-lg object-cover"
          />
          <div class="min-w-0 flex-1 text-[12px]">
            <b class="block truncate font-bold">{{ ligne.produit.nom }}</b>
            <span class="text-[11px] text-encre-douce">{{ ligne.produit.boutique.nom }}</span>
            <p
              v-if="ligne.prix_a_change"
              class="flex items-center gap-1 text-[10.5px] text-[#93590a]"
            >
              <AlertTriangle :size="10" /> Prix modifie
            </p>

            <div class="mt-1 flex items-center justify-between">
              <div class="flex items-center gap-1.5 text-[11.5px] text-encre-douce">
                <button
                  type="button"
                  class="h-5 w-5 rounded-[5px] border border-trait bg-papier"
                  :disabled="panier.occupe"
                  @click="panier.changerQuantite(ligne.id, ligne.quantite - 1)"
                >
                  −
                </button>
                {{ ligne.quantite }}
                <button
                  type="button"
                  class="h-5 w-5 rounded-[5px] border border-trait bg-papier disabled:opacity-30"
                  :disabled="panier.occupe || ligne.quantite >= ligne.produit.stock_commandable"
                  @click="panier.changerQuantite(ligne.id, ligne.quantite + 1)"
                >
                  +
                </button>
              </div>
              <div class="flex items-center gap-2">
                <b class="text-[12px]">{{ euros(ligne.sous_total_centimes) }}</b>
                <button
                  type="button"
                  class="text-encre-douce transition-colors hover:text-[#9c2116]"
                  title="Retirer"
                  @click="panier.retirer(ligne.id)"
                >
                  <Trash2 :size="13" />
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div v-else class="flex flex-1 flex-col items-center justify-center px-6 text-center">
        <span
          class="flex h-12 w-12 items-center justify-center rounded-lg"
          :style="{ background: 'var(--accent-doux)', color: 'var(--accent)' }"
        >
          <ShoppingCart :size="20" />
        </span>
        <b class="mt-3 text-[13px]">Panier vide</b>
        <p class="mt-1 text-[12px] text-encre-douce">
          Aucun compte n est necessaire pour commencer.
        </p>
      </div>

      <div v-if="!vide" class="shrink-0 border-t border-trait p-4">
        <p
          v-if="panier.plusieursBoutiques"
          class="mb-2.5 rounded-lg bg-atelier px-3 py-2 text-[11px] text-encre-douce"
        >
          {{ panier.contenu.boutiques.length }} boutiques : plusieurs livraisons, un seul
          paiement.
        </p>
        <div class="mb-2.5 flex justify-between text-[13px] font-extrabold">
          <span>Total</span>
          <span>{{ panier.total }}</span>
        </div>
        <RouterLink :to="{ name: 'commande' }" class="bouton-accent w-full">
          Passer commande
        </RouterLink>
      </div>

      <div class="shrink-0 border-t border-trait-doux px-4 py-2.5">
        <p class="flex items-center gap-2 text-[11px] text-encre-douce">
          <Bell :size="12" /> Les notifications s afficheront ici.
        </p>
      </div>
    </template>
  </aside>
</template>
