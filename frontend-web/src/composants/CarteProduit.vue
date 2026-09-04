<script setup lang="ts">
// La carte du catalogue, empruntee aux CMS marchands (design-system.md § 9) :
// elevation au survol, image qui grandit un peu, badge d'etat, prix lisible.
// Ce sont ces details qui font la difference entre une grille figee et un
// catalogue vivant.
import { Bike, ImageOff, Package, Plus, Star } from '@lucide/vue'
import { computed } from 'vue'

import { usePanier } from '../stores/panier'

export type Produit = {
  id: number
  nom: string
  prix_centimes: number
  image: string
  disponible: boolean
  distance_km: number | null
  boutique: { id: number; nom: string; type_service: string; ville: string }
  /** La note publique (O-5). `sur` dit si elle porte sur le produit ou sa
   *  boutique : faire passer l'une pour l'autre serait un petit mensonge que
   *  les gens repèrent. */
  note?: { moyenne: number; nombre: number; sur: 'produit' | 'boutique' } | null
}

const props = defineProps<{ produit: Produit }>()
const panier = usePanier()

const prix = computed(() =>
  (props.produit.prix_centimes / 100).toLocaleString('fr-FR', {
    style: 'currency',
    currency: 'EUR',
  }),
)
const estExpress = computed(() => props.produit.boutique.type_service === 'EXPRESS')
</script>

<template>
  <RouterLink
    :to="{ name: 'produit', params: { id: produit.id } }"
    class="group flex flex-col overflow-hidden rounded-2xl border border-trait bg-papier
           transition-all duration-200 hover:-translate-y-1 hover:border-marque/50
           hover:shadow-xl hover:shadow-black/30"
  >
    <div class="relative aspect-4/3 overflow-hidden bg-atelier">
      <img
        v-if="produit.image"
        :src="produit.image"
        :alt="produit.nom"
        loading="lazy"
        class="h-full w-full object-cover transition-transform duration-300
               group-hover:scale-105"
        :class="produit.disponible ? '' : 'opacity-40 grayscale'"
      />
      <span v-else class="flex h-full items-center justify-center text-trait">
        <ImageOff :size="30" />
      </span>

      <span
        class="absolute top-3 left-3 flex items-center gap-1.5 rounded-full px-2.5 py-1
               text-[11px] font-semibold backdrop-blur-sm"
        :class="estExpress ? 'bg-amber-500/85 text-amber-950' : 'bg-slate-900/70 text-slate-100'"
      >
        <component :is="estExpress ? Bike : Package" :size="12" />
        {{ estExpress ? 'Express' : 'Standard' }}
      </span>

      <span
        v-if="!produit.disponible"
        class="absolute top-3 right-3 rounded-full bg-red-900/85 px-2.5 py-1 text-[11px]
               font-semibold text-red-100"
      >
        Rupture
      </span>

      <!-- Ajout rapide : le geste des catalogues marchands, sans quitter la
           grille. `.prevent` empeche le clic d'ouvrir aussi la fiche produit. -->
      <button
        v-else
        type="button"
        class="absolute right-3 bottom-3 flex h-10 w-10 items-center justify-center rounded-xl
               bg-marque text-encre opacity-0 shadow-lg transition-all duration-200
               group-hover:opacity-100 hover:bg-marque-clair focus-visible:opacity-100"
        title="Ajouter au panier"
        :disabled="panier.occupe"
        @click.prevent.stop="panier.ajouter(produit.id)"
      >
        <Plus :size="19" />
      </button>
    </div>

    <div class="flex flex-1 flex-col p-4">
      <b class="text-[14.5px] leading-snug font-semibold text-encre">{{ produit.nom }}</b>
      <span class="mt-1 text-[12.5px] text-encre-douce">
        {{ produit.boutique.nom }}
        <template v-if="produit.distance_km"> · {{ produit.distance_km }} km</template>
      </span>

      <!-- La note se lit AVANT d'ouvrir la fiche : c'est à ce moment-là qu'un
           avis sert à choisir entre deux produits (O-5). Elle était visible
           uniquement dans la fiche, donc trop tard. -->
      <span
        v-if="produit.note"
        class="mt-1.5 inline-flex items-center gap-1 text-[12px]"
        :title="produit.note.sur === 'boutique'
          ? `Note de la boutique, sur ${produit.note.nombre} avis`
          : `Note du produit, sur ${produit.note.nombre} avis`"
      >
        <Star :size="12" class="fill-[#e0a106] text-[#e0a106]" />
        <b class="text-encre">{{ produit.note.moyenne }}</b>
        <span class="text-encre-douce">
          ({{ produit.note.nombre }}{{ produit.note.sur === 'boutique' ? ' · boutique' : '' }})
        </span>
      </span>

      <span class="mt-3 text-[16px] font-bold text-[color:var(--accent)]">{{ prix }}</span>
    </div>
  </RouterLink>
</template>
