<script setup lang="ts">
// L'en-tete du site public. Elle doit repondre a trois questions en un coup
// d'oeil : ou suis-je, ou est-ce que je me fais livrer, et comment j'entre.
import { LogIn, Search, ShoppingCart, Store, UserRound } from '@lucide/vue'
import { ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { useAuthentification } from '../stores/authentification'
import { usePanier } from '../stores/panier'
import BandeauLivrerA from './BandeauLivrerA.vue'
import LogoRivDinde from './LogoRivDinde.vue'

const session = useAuthentification()
const panier = usePanier()
const routeur = useRouter()
const route = useRoute()

const recherche = ref((route.query.recherche as string) ?? '')
watch(
  () => route.query.recherche,
  (valeur) => {
    recherche.value = (valeur as string) ?? ''
  },
)

// Recherche instantanee, avec un delai de 250 ms : filtrer a chaque frappe
// enverrait une requete par lettre, attendre la touche Entree oblige a un
// geste que plus personne ne fait. `replace` plutot que `push` pour ne pas
// remplir l'historique du navigateur d'une entree par lettre tapee.
let minuteur: ReturnType<typeof setTimeout> | undefined

function appliquer(remplacer = true) {
  const query = { ...route.query }
  const valeur = recherche.value.trim()
  if (valeur) query.recherche = valeur
  else delete query.recherche
  const cible = { name: 'vitrine', query }
  return remplacer ? routeur.replace(cible) : routeur.push(cible)
}

watch(recherche, () => {
  clearTimeout(minuteur)
  minuteur = setTimeout(() => appliquer(), 250)
})

function lancerRecherche() {
  clearTimeout(minuteur)
  appliquer(false)
}
</script>

<template>
  <header class="sticky top-0 z-40 border-b border-encre-3 bg-encre/90 backdrop-blur-md">
    <div class="mx-auto flex h-[68px] max-w-[1240px] items-center gap-4 px-5">
      <RouterLink to="/" class="flex shrink-0 items-center gap-2.5">
        <LogoRivDinde :taille="34" />
        <span class="hidden text-[17px] font-semibold tracking-tight text-white sm:block">
          RivDinde
        </span>
      </RouterLink>

      <div class="hidden lg:block">
        <BandeauLivrerA />
      </div>

      <form class="relative mx-auto hidden max-w-md flex-1 md:block" @submit.prevent="lancerRecherche">
        <Search :size="16" class="absolute top-1/2 left-3.5 -translate-y-1/2 text-[#8a6d5c]" />
        <input
          v-model="recherche"
          type="search"
          placeholder="Rechercher un plat, un produit, une boutique…"
          class="w-full rounded-xl border border-encre-3 bg-encre-2/60 py-2.5 pr-3 pl-10
                 text-[13.5px] text-[#f3e7dd] transition-colors duration-150
                 placeholder:text-[#7c6459] focus:border-marque focus:outline-none"
        />
      </form>

      <nav class="ml-auto flex items-center gap-2">
        <button
          type="button"
          class="relative flex items-center gap-2 rounded-xl border border-encre-3 px-3 py-2
                 text-[13px] text-[#c9b4a6] transition-colors duration-150 hover:border-marque"
          title="Mon panier"
          @click="panier.ouvert = true"
        >
          <ShoppingCart :size="16" />
          <span
            v-if="panier.nombreArticles"
            class="absolute -top-1.5 -right-1.5 flex h-[18px] min-w-[18px] items-center
                   justify-center rounded-full bg-marque px-1 text-[10px] font-bold text-encre"
          >
            {{ panier.nombreArticles }}
          </span>
        </button>

        <RouterLink
          to="/rejoindre"
          class="hidden items-center gap-2 rounded-xl px-3 py-2 text-[13px] text-[#c9b4a6]
                 transition-colors duration-150 hover:text-marque-clair lg:flex"
        >
          <Store :size="15" />
          Vendre ou livrer
        </RouterLink>

        <template v-if="session.estConnecte">
          <RouterLink
            v-if="session.role !== 'CLIENT'"
            to="/espace"
            class="bouton-discret"
          >
            Mon espace
          </RouterLink>
          <RouterLink
            to="/espace"
            class="flex items-center gap-2 rounded-xl border border-encre-3 px-3 py-2
                   text-[13px] text-[#c9b4a6] transition-colors hover:border-marque"
          >
            <UserRound :size="15" />
            <span class="hidden sm:block">{{ session.utilisateur?.prenom }}</span>
          </RouterLink>
        </template>

        <template v-else>
          <RouterLink to="/connexion" class="bouton-discret">
            <LogIn :size="15" />
            <span class="hidden sm:block">Se connecter</span>
          </RouterLink>
          <RouterLink to="/inscription" class="bouton-marque px-4! py-2! text-[13px]!">
            <span class="hidden sm:block">Creer un compte</span>
            <span class="sm:hidden">Compte</span>
          </RouterLink>
        </template>
      </nav>
    </div>

    <!-- Sur mobile, le choix de la ville passe sous l'en-tete plutot que de
         disparaitre : c'est l'information qui commande tout le catalogue. -->
    <div class="border-t border-encre-3 px-5 py-2 lg:hidden">
      <BandeauLivrerA />
    </div>
  </header>
</template>
