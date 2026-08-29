<script setup lang="ts">
// Les filtres, DANS le contenu et au-dessus de la grille.
//
// Ils ont ete essayes dans la sidebar : mauvaise idee. La sidebar sert a
// naviguer entre les ecrans, pas a trier ce qu'on regarde — et la maquette
// les place au-dessus du contenu, comme tous les catalogues.
import { Bike, Package, Store, X } from '@lucide/vue'

import { useCatalogue } from '../stores/catalogue'

const catalogue = useCatalogue()

const SERVICES = [
  { cle: undefined, libelle: 'Tout', icone: Store },
  { cle: 'EXPRESS', libelle: 'Express', icone: Bike },
  { cle: 'STANDARD', libelle: 'Standard', icone: Package },
]
</script>

<template>
  <div class="flex flex-col gap-2.5">
    <!-- Service -->
    <div class="flex flex-wrap items-center gap-2">
      <button
        v-for="option in SERVICES"
        :key="option.libelle"
        type="button"
        class="puce-filtre"
        :class="{ 'puce-filtre-active': catalogue.service === option.cle }"
        @click="catalogue.service = option.cle; catalogue.charger()"
      >
        <component :is="option.icone" :size="13" />
        {{ option.libelle }}
      </button>

      <span class="mx-1 h-5 w-px bg-trait" />

      <!-- Categories, groupees par univers : sept categories a plat ne se
           lisent pas, deux univers oui. -->
      <template v-for="groupe in catalogue.univers" :key="groupe.nom">
        <button
          v-for="element in groupe.categories"
          :key="element.slug"
          type="button"
          class="puce-filtre"
          :class="{ 'puce-filtre-active': catalogue.categorie === element.slug }"
          :title="groupe.nom"
          @click="catalogue.basculer('categorie', element.slug)"
        >
          {{ element.nom }}
          <span class="opacity-60">{{ element.nombre }}</span>
        </button>
      </template>
    </div>

    <!-- Boutiques -->
    <div v-if="catalogue.boutiques.length > 1" class="flex flex-wrap items-center gap-2">
      <span class="text-[11px] font-bold tracking-wider text-encre-douce uppercase">
        Boutiques
      </span>
      <button
        v-for="element in catalogue.boutiques"
        :key="element.id"
        type="button"
        class="puce-filtre"
        :class="{ 'puce-filtre-active': catalogue.boutique === String(element.id) }"
        @click="catalogue.basculer('boutique', String(element.id))"
      >
        <component :is="element.type_service === 'EXPRESS' ? Bike : Package" :size="12" />
        {{ element.nom }}
        <span class="opacity-60">{{ element.nombre }}</span>
      </button>

      <button
        v-if="catalogue.filtreActif"
        type="button"
        class="puce-filtre"
        @click="catalogue.toutEffacer()"
      >
        <X :size="12" />
        Tout effacer
      </button>
    </div>
  </div>
</template>
