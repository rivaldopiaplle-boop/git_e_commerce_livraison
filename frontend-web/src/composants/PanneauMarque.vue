<script setup lang="ts">
// La colonne de gauche des ecrans de connexion et d'inscription. Elle porte
// la marque et dit en trois lignes ce que fait la plateforme — un ecran de
// connexion nu ne dit rien de ce qu'on s'apprete a rejoindre.
//
// Elle etait ecrite en blanc sur un fond sombre qui n'existait plus : les
// jetons `encre-2` et `encre-3` avaient disparu du theme, et le texte se
// retrouvait blanc sur blanc. Tout est desormais clair, comme la maquette.
import { Bike, PackageCheck, Store } from '@lucide/vue'

import LogoRivDinde from './LogoRivDinde.vue'

const arguments_ = [
  {
    icone: Store,
    titre: 'Des boutiques, deux rythmes',
    texte: 'Express en direct, Standard par entrepot.',
  },
  {
    icone: Bike,
    titre: 'Une livraison suivie',
    texte: 'Du panier a la porte, chaque etape est visible.',
  },
  {
    icone: PackageCheck,
    titre: 'Un seul paiement',
    texte: 'Meme quand la commande vient de plusieurs boutiques.',
  },
]
</script>

<template>
  <aside
    class="relative hidden w-[46%] max-w-[520px] shrink-0 flex-col justify-between
           overflow-hidden border-r border-trait bg-panneau p-12 lg:flex"
  >
    <!-- Un halo de marque, tres pale : il donne de la profondeur sans ajouter
         d'image a telecharger. -->
    <div
      class="pointer-events-none absolute -top-32 -right-24 h-96 w-96 rounded-full
             bg-marque/10 blur-3xl"
      aria-hidden="true"
    />

    <RouterLink to="/" class="relative block" title="Retour au catalogue">
      <LogoRivDinde variante="complet" :taille="132" />
      <h1 class="mt-8 text-4xl font-semibold tracking-tight text-encre">RivDinde</h1>
      <p class="mt-2 text-[12.5px] font-semibold tracking-[0.14em] text-marque-fonce uppercase">
        commander, livrer, suivre
      </p>
    </RouterLink>

    <ul class="relative flex flex-col gap-6">
      <li v-for="argument in arguments_" :key="argument.titre" class="flex gap-4">
        <span
          class="mt-0.5 flex h-10 w-10 shrink-0 items-center justify-center rounded-xl
                 bg-marque-voile text-marque-fonce"
        >
          <component :is="argument.icone" :size="19" />
        </span>
        <span>
          <b class="block text-[15px] font-semibold text-encre">{{ argument.titre }}</b>
          <span class="text-[13.5px] text-encre-douce">{{ argument.texte }}</span>
        </span>
      </li>
    </ul>

    <p class="relative text-[12px] text-encre-douce">
      Environnement de demonstration — aucune commande reelle, aucun paiement reel.
    </p>
  </aside>
</template>
