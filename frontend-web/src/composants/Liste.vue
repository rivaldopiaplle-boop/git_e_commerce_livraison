<script setup lang="ts" generic="T extends Record<string, unknown>">
// LA liste du projet. Toutes les listes de tous les rôles passent par ici.
//
// Elle vient de `banque-app/frontend-web/src/shared/components/Tableau.tsx`,
// qui règle le problème une fois pour toutes : colonnes déclarées, recherche,
// tri, pagination, état vide rédigé, et surtout **des boutons-symboles en fin
// de ligne pour consulter et gérer** — c'est la règle d'or n°9, posée dès le
// bloc A : « dans les listes d'affichage, des boutons en forme de symbole pour
// consulter et gérer les données ».
//
// Avant elle, chaque écran réinventait sa liste : l'un en tableau, l'autre en
// lignes, un troisième avec un dépliant. Trois grammaires pour une seule idée.
import { ChevronDown, ChevronLeft, ChevronRight, Search } from '@lucide/vue'
import { computed, ref, watch } from 'vue'

import type { Colonne } from './liste'

const props = withDefaults(
  defineProps<{
    colonnes: Colonne<T>[]
    lignes: T[]
    cleLigne: (ligne: T) => string | number
    /** Le texte dans lequel la recherche cherche. Absente, pas de recherche. */
    recherche?: (ligne: T) => string
    placeholder?: string
    chargement?: boolean
    parPage?: number
    /** Déplie un détail sous la ligne, sans quitter la liste. */
    depliable?: boolean
  }>(),
  { parPage: 12, placeholder: 'Rechercher…' },
)

const requete = ref('')
const triCle = ref<string | null>(null)
const triSens = ref<1 | -1>(1)
const page = ref(1)
const depliee = ref<string | number | null>(null)

const filtrees = computed(() => {
  let resultat = props.lignes
  const texte = requete.value.trim().toLowerCase()
  if (props.recherche && texte) {
    resultat = resultat.filter((ligne) => props.recherche!(ligne).toLowerCase().includes(texte))
  }
  if (triCle.value) {
    const colonne = props.colonnes.find((c) => c.cle === triCle.value)
    if (colonne?.tri) {
      resultat = [...resultat].sort((a, b) => colonne.tri!(a, b) * triSens.value)
    }
  }
  return resultat
})

const pages = computed(() => Math.max(1, Math.ceil(filtrees.value.length / props.parPage)))
const pageSure = computed(() => Math.min(page.value, pages.value))
const visibles = computed(() =>
  filtrees.value.slice((pageSure.value - 1) * props.parPage, pageSure.value * props.parPage),
)

// Filtrer ou trier remet en première page : rester page 4 d'un résultat qui
// n'en compte plus qu'une donne une liste vide sans explication.
watch([requete, triCle, triSens, () => props.lignes], () => {
  page.value = 1
})

function basculerTri(colonne: Colonne<T>) {
  if (!colonne.tri) return
  if (triCle.value === colonne.cle) triSens.value = triSens.value === 1 ? -1 : 1
  else {
    triCle.value = colonne.cle
    triSens.value = 1
  }
}

const MASQUES: Record<string, string> = {
  sm: 'hidden sm:flex',
  md: 'hidden md:flex',
  lg: 'hidden lg:flex',
  xl: 'hidden xl:flex',
}

function classeColonne(colonne: Colonne<T>) {
  return [
    colonne.masquerSous ? MASQUES[colonne.masquerSous] : 'flex',
    colonne.aligne === 'droite'
      ? 'justify-end text-right'
      : colonne.aligne === 'centre'
        ? 'justify-center text-center'
        : 'justify-start',
  ]
}
function styleColonne(colonne: Colonne<T>) {
  return colonne.largeur
    ? { width: `${colonne.largeur}px`, flex: '0 0 auto' }
    : { flex: '1 1 0%', minWidth: '0' }
}

function basculerDepli(cle: string | number) {
  depliee.value = depliee.value === cle ? null : cle
}
</script>

<template>
  <div class="carte">
    <!-- Barre d'outils : recherche à gauche, actions de l'écran à droite -->
    <div
      v-if="recherche || $slots.outils"
      class="flex flex-wrap items-center justify-between gap-3 border-b border-trait-doux px-4 py-3"
    >
      <div
        v-if="recherche"
        class="flex items-center gap-2 rounded-full bg-atelier px-3.5 py-2"
      >
        <Search :size="14" class="text-encre-douce" />
        <input
          v-model="requete"
          type="search"
          :placeholder="placeholder"
          class="w-56 bg-transparent text-[12.5px] focus:outline-none"
        />
      </div>
      <div v-else />
      <div class="flex items-center gap-2">
        <slot name="outils" />
      </div>
    </div>

    <!-- En-têtes -->
    <div
      class="flex items-center gap-3 border-b border-trait-doux px-4 py-2.5 text-[10.5px]
             font-bold tracking-wider text-encre-douce uppercase"
    >
      <span
        v-for="colonne in colonnes"
        :key="colonne.cle"
        class="items-center gap-1"
        :class="[classeColonne(colonne), colonne.tri ? 'cursor-pointer hover:text-encre' : '']"
        :style="styleColonne(colonne)"
        @click="basculerTri(colonne)"
      >
        {{ colonne.titre }}
        <ChevronDown
          v-if="colonne.tri && triCle === colonne.cle"
          :size="11"
          class="transition-transform"
          :class="triSens === -1 ? 'rotate-180' : ''"
        />
      </span>
      <span v-if="$slots.actions" class="w-[104px] shrink-0 text-right">Actions</span>
      <span v-if="depliable" class="w-6 shrink-0" />
    </div>

    <!-- Chargement -->
    <div v-if="chargement" class="flex flex-col">
      <span
        v-for="n in 5"
        :key="n"
        class="mx-4 my-2.5 h-5 animate-pulse rounded bg-trait-doux"
      />
    </div>

    <!-- État vide : rédigé, jamais un tableau muet (règle d'or n°2) -->
    <div v-else-if="!visibles.length">
      <slot name="vide">
        <div class="vide">
          <b class="vide-titre">Aucun résultat</b>
          <p v-if="requete" class="vide-texte">
            Rien ne correspond à « {{ requete }} ».
          </p>
        </div>
      </slot>
    </div>

    <!-- Les lignes -->
    <template v-else>
      <template v-for="ligne in visibles" :key="cleLigne(ligne)">
        <div
          class="flex items-center gap-3 border-b border-trait-doux px-4 py-3 text-[12.5px]
                 transition-colors last:border-b-0 hover:bg-atelier"
        >
          <span
            v-for="colonne in colonnes"
            :key="colonne.cle"
            class="min-w-0 items-center"
            :class="classeColonne(colonne)"
            :style="styleColonne(colonne)"
          >
            <slot :name="`col-${colonne.cle}`" :ligne="ligne" />
          </span>

          <!-- Les boutons-symboles : consulter et gérer, sans quitter la liste -->
          <span v-if="$slots.actions" class="flex w-[104px] shrink-0 justify-end gap-1.5">
            <slot name="actions" :ligne="ligne" />
          </span>

          <button
            v-if="depliable"
            type="button"
            class="bouton-icone !h-6 !w-6 shrink-0"
            :title="depliee === cleLigne(ligne) ? 'Replier' : 'Déplier le détail'"
            @click="basculerDepli(cleLigne(ligne))"
          >
            <ChevronDown
              :size="14"
              class="transition-transform duration-150"
              :class="depliee === cleLigne(ligne) ? 'rotate-180' : ''"
            />
          </button>
        </div>

        <div
          v-if="depliable && depliee === cleLigne(ligne)"
          class="border-b border-trait-doux bg-atelier px-4 py-4"
        >
          <slot name="detail" :ligne="ligne" />
        </div>
      </template>
    </template>

    <!-- Pagination : seulement quand elle sert -->
    <div
      v-if="pages > 1"
      class="flex items-center justify-between border-t border-trait-doux px-4 py-2.5
             text-[11.5px] text-encre-douce"
    >
      <span>
        {{ (pageSure - 1) * parPage + 1 }}–{{ Math.min(pageSure * parPage, filtrees.length) }}
        sur {{ filtrees.length }}
      </span>
      <span class="flex items-center gap-1">
        <button
          type="button"
          class="bouton-ligne"
          title="Page précédente"
          :disabled="pageSure <= 1"
          @click="page = pageSure - 1"
        >
          <ChevronLeft :size="14" />
        </button>
        <span class="px-2 font-semibold">{{ pageSure }} / {{ pages }}</span>
        <button
          type="button"
          class="bouton-ligne"
          title="Page suivante"
          :disabled="pageSure >= pages"
          @click="page = pageSure + 1"
        >
          <ChevronRight :size="14" />
        </button>
      </span>
    </div>
  </div>
</template>
