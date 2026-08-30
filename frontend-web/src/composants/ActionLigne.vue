<script setup lang="ts">
// Le bouton-symbole de fin de ligne, repris de `ActionLigne` du projet banque.
//
// Trois choses qu'il garantit et qu'on oublie une fois sur deux quand on
// écrit un `<button>` à la main :
//   · une **infobulle**, parce qu'une icône seule n'est jamais évidente ;
//   · un **libellé accessible**, sans quoi le bouton n'existe pas pour un
//     lecteur d'écran ;
//   · un état **désactivé** qui reste survolable — un bouton grisé sans
//     infobulle laisse l'utilisateur sans explication.
import type { Component } from 'vue'

withDefaults(
  defineProps<{
    titre: string
    icone: Component
    /** `accent` pour l'action principale, `danger` pour ce qui retire. */
    ton?: 'neutre' | 'accent' | 'danger'
    desactive?: boolean
    /** Une action qui navigue plutôt qu'elle n'agit. */
    vers?: object | string
  }>(),
  { ton: 'neutre' },
)
</script>

<template>
  <RouterLink
    v-if="vers && !desactive"
    :to="vers"
    class="bouton-ligne"
    :class="{ 'bouton-ligne-accent': ton === 'accent', 'bouton-ligne-danger': ton === 'danger' }"
    :title="titre"
  >
    <component :is="icone" :size="14" />
    <span class="sr-only">{{ titre }}</span>
  </RouterLink>

  <button
    v-else
    type="button"
    class="bouton-ligne"
    :class="{ 'bouton-ligne-accent': ton === 'accent', 'bouton-ligne-danger': ton === 'danger' }"
    :title="titre"
    :disabled="desactive"
  >
    <component :is="icone" :size="14" />
    <span class="sr-only">{{ titre }}</span>
  </button>
</template>
