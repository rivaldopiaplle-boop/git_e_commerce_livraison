<script setup lang="ts">
// Le panneau retractable de droite (regle d'or n°6) : ce qui doit rester
// pres de l'oeil sans occuper la page.
import { AlertTriangle, Minus, Plus, ShoppingCart, Trash2, X } from '@lucide/vue'

import { usePanier } from '../stores/panier'

const panier = usePanier()

const euros = (centimes: number) =>
  (centimes / 100).toLocaleString('fr-FR', { style: 'currency', currency: 'EUR' })
</script>

<template>
  <Teleport to="body">
    <!-- Voile : fermer en cliquant a cote est le geste attendu. -->
    <Transition
      enter-active-class="transition-opacity duration-200"
      enter-from-class="opacity-0"
      leave-active-class="transition-opacity duration-150"
      leave-to-class="opacity-0"
    >
      <div
        v-if="panier.ouvert"
        class="fixed inset-0 z-50 bg-black/50"
        @click="panier.ouvert = false"
      />
    </Transition>

    <Transition
      enter-active-class="transition-transform duration-200 ease-out"
      enter-from-class="translate-x-full"
      leave-active-class="transition-transform duration-150 ease-in"
      leave-to-class="translate-x-full"
    >
      <aside
        v-if="panier.ouvert"
        class="fixed top-0 right-0 z-50 flex h-full w-[380px] max-w-[92vw] flex-col
               border-l border-encre-3 bg-encre shadow-2xl"
      >
        <header class="flex items-center justify-between border-b border-encre-3 px-5 py-4">
          <b class="flex items-center gap-2.5 text-[15px] text-white">
            <ShoppingCart :size="18" class="text-marque" />
            Mon panier
            <span
              v-if="panier.nombreArticles"
              class="rounded-full bg-marque px-2 py-0.5 text-[11px] font-bold text-encre"
            >
              {{ panier.nombreArticles }}
            </span>
          </b>
          <button
            type="button"
            class="flex h-8 w-8 items-center justify-center rounded-lg text-[#8a6d5c]
                   transition-colors hover:bg-white/5 hover:text-white"
            @click="panier.ouvert = false"
          >
            <X :size="17" />
          </button>
        </header>

        <p
          v-if="panier.erreur"
          class="mx-5 mt-4 rounded-xl border border-red-900/70 bg-red-950/40 px-3.5 py-2.5
                 text-[12.5px] text-red-200"
        >
          {{ panier.erreur }}
        </p>

        <div v-if="panier.contenu.lignes.length" class="flex-1 overflow-y-auto px-5 py-4">
          <article
            v-for="ligne in panier.contenu.lignes"
            :key="ligne.id"
            class="flex gap-3 border-b border-encre-3 py-4 last:border-0"
          >
            <img
              v-if="ligne.produit.image"
              :src="ligne.produit.image"
              :alt="ligne.produit.nom"
              class="h-16 w-16 shrink-0 rounded-xl object-cover"
            />
            <div class="min-w-0 flex-1">
              <b class="block truncate text-[13.5px] text-white">{{ ligne.produit.nom }}</b>
              <span class="text-[12px] text-[#8a6d5c]">{{ ligne.produit.boutique.nom }}</span>

              <p
                v-if="ligne.prix_a_change"
                class="mt-1 flex items-center gap-1.5 text-[11.5px] text-amber-300"
              >
                <AlertTriangle :size="12" />
                Le prix a change depuis l'ajout
              </p>

              <div class="mt-2 flex items-center justify-between">
                <div class="flex items-center gap-1 rounded-lg border border-encre-3">
                  <button
                    type="button"
                    class="flex h-7 w-7 items-center justify-center text-[#b49a8c]
                           transition-colors hover:text-marque"
                    :disabled="panier.occupe"
                    @click="panier.changerQuantite(ligne.id, ligne.quantite - 1)"
                  >
                    <Minus :size="13" />
                  </button>
                  <span class="w-6 text-center text-[13px] font-semibold">{{ ligne.quantite }}</span>
                  <button
                    type="button"
                    class="flex h-7 w-7 items-center justify-center text-[#b49a8c]
                           transition-colors hover:text-marque disabled:opacity-30"
                    :disabled="panier.occupe || ligne.quantite >= ligne.produit.stock_commandable"
                    @click="panier.changerQuantite(ligne.id, ligne.quantite + 1)"
                  >
                    <Plus :size="13" />
                  </button>
                </div>

                <div class="flex items-center gap-3">
                  <b class="text-[13.5px] text-marque">{{ euros(ligne.sous_total_centimes) }}</b>
                  <button
                    type="button"
                    class="text-[#7c6459] transition-colors hover:text-red-400"
                    title="Retirer"
                    @click="panier.retirer(ligne.id)"
                  >
                    <Trash2 :size="15" />
                  </button>
                </div>
              </div>
            </div>
          </article>
        </div>

        <!-- Etat vide pense : on dit quoi faire, pas seulement que c'est vide -->
        <div v-else class="flex flex-1 flex-col items-center justify-center px-8 text-center">
          <span class="flex h-16 w-16 items-center justify-center rounded-2xl bg-marque/10 text-marque">
            <ShoppingCart :size="26" />
          </span>
          <b class="mt-4 text-[15px] text-white">Votre panier est vide</b>
          <p class="mt-1.5 text-[13px] text-[#b49a8c]">
            Parcourez le catalogue et ajoutez ce qui vous plait. Aucun compte n'est
            necessaire pour commencer.
          </p>
        </div>

        <footer v-if="panier.contenu.lignes.length" class="border-t border-encre-3 p-5">
          <p
            v-if="panier.plusieursBoutiques"
            class="mb-3 rounded-xl border border-encre-3 bg-encre-2/60 px-3.5 py-2.5
                   text-[12px] text-[#b49a8c]"
          >
            Votre panier contient {{ panier.contenu.boutiques.length }} boutiques : il donnera
            plusieurs commandes, livrees separement, mais un seul paiement.
          </p>

          <div class="flex items-center justify-between">
            <span class="text-[13px] text-[#b49a8c]">Total</span>
            <b class="text-[20px] text-marque">{{ panier.total }}</b>
          </div>

          <button type="button" class="bouton-marque mt-4 w-full cursor-not-allowed opacity-60" disabled>
            Passer commande
          </button>
          <p class="mt-2 text-center text-[11.5px] text-[#7c6459]">
            Le tunnel de commande et le paiement arrivent a la tranche 5.
          </p>
        </footer>
      </aside>
    </Transition>
  </Teleport>
</template>
