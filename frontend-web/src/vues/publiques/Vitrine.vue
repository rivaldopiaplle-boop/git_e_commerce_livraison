<script setup lang="ts">
// La page d'accueil, PUBLIQUE (D-03 et D-33).
//
// Sidebar de filtres a gauche, grille au centre, panneau panier a droite :
// c'est la disposition qu'imposent les regles d'or 6 et 8, et celle de tous
// les catalogues marchands.
import { ArrowRight, Bike, MapPin, Package, Search, Store, X } from '@lucide/vue'
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { catalogue } from '../../api/catalogue'
import BarreFiltres, { type BoutiqueFacette, type Univers } from '../../composants/BarreFiltres.vue'
import CarteProduit, { type Produit } from '../../composants/CarteProduit.vue'
import Squelette from '../../composants/Squelette.vue'
import { usePosition } from '../../stores/position'

const position = usePosition()
const route = useRoute()
const routeur = useRouter()

// Chemin construit a l'execution : ecrit en dur dans l'attribut, Vite tente de
// le resoudre comme un module a la compilation et les tests unitaires
// echouent. Le fichier est servi tel quel depuis `public/`.
const MASCOTTE = '/logo-rivdinde-512.webp'

const produits = ref<Produit[]>([])
const univers = ref<Univers[]>([])
const boutiques = ref<BoutiqueFacette[]>([])
const totalAvantFiltres = ref(0)
const chargement = ref(true)

const categorie = ref<string | undefined>()
const boutique = ref<string | undefined>()
const service = ref<string | undefined>()

// La recherche vient de l'URL : elle survit a un rafraichissement et se
// partage par lien. L'en-tete l'ecrit, la vitrine la lit.
const recherche = computed(() => (route.query.recherche as string) || undefined)

async function charger() {
  chargement.value = true
  try {
    const reponse = await catalogue.produits(position.parametres, {
      categorie: categorie.value,
      boutique: boutique.value,
      type_service: service.value,
      recherche: recherche.value,
    })
    produits.value = reponse.data
    univers.value = reponse.meta.facettes.univers
    boutiques.value = reponse.meta.facettes.boutiques
    totalAvantFiltres.value = reponse.meta.total_avant_filtres
  } catch {
    produits.value = []
    univers.value = []
    boutiques.value = []
  } finally {
    chargement.value = false
  }
}

onMounted(charger)
watch([() => position.parametres, categorie, boutique, service, recherche], charger)

function effacerRecherche() {
  const query = { ...route.query }
  delete query.recherche
  routeur.replace({ name: 'vitrine', query })
}
</script>

<template>
  <div>
    <!-- ── Banniere ────────────────────────────────────────────────── -->
    <section class="relative overflow-hidden border-b border-encre-3">
      <div
        class="pointer-events-none absolute -top-40 -right-20 h-[420px] w-[420px]
               rounded-full bg-marque/12 blur-3xl"
      />
      <div
        class="relative mx-auto flex max-w-[1240px] flex-col items-center gap-10 px-5 py-14
               lg:flex-row lg:justify-between lg:py-16"
      >
        <div>
          <p class="text-[12px] tracking-[0.16em] text-marque uppercase">
            Commander, livrer, suivre
          </p>
          <h1
            class="mt-4 max-w-[16ch] text-4xl leading-[1.1] font-semibold tracking-tight
                   text-white lg:text-[52px]"
          >
            Deux rythmes, une seule plateforme.
          </h1>
          <p class="mt-5 max-w-[58ch] text-[15.5px] leading-relaxed text-[#b49a8c]">
            <b class="text-white">Express</b> : les boutiques proches de chez vous, livrees
            directement, en minutes. <b class="text-white">Standard</b> : tout le catalogue,
            regroupe en entrepot et livre en tournee.
          </p>

          <div class="mt-8 flex flex-wrap items-center gap-3">
            <a href="#catalogue" class="bouton-marque">
              Voir le catalogue
              <ArrowRight :size="17" />
            </a>
            <RouterLink to="/rejoindre" class="bouton-discret">
              <Store :size="15" />
              Vendre ou livrer avec nous
            </RouterLink>
          </div>
        </div>

        <!-- La mascotte, qui se balance doucement a cote du titre (G-8).
             L'animation est suspendue si le systeme demande moins de
             mouvement — certaines personnes en ont mal au coeur. -->
        <div class="shrink-0">
          <img
            :src="MASCOTTE"
            alt=""
            width="300"
            height="300"
            class="mascotte w-[210px] rounded-3xl lg:w-[300px]"
          />
        </div>
      </div>
    </section>

    <div class="mx-auto max-w-[1240px] px-5">
      <p
        v-if="!position.connue"
        class="mt-6 flex items-center gap-2 rounded-xl border border-amber-900/60
               bg-amber-950/25 px-4 py-3 text-[13px] text-amber-200"
      >
        <MapPin :size="15" class="shrink-0" />
        Indiquez votre ville en haut de page pour voir aussi les boutiques Express
        proches de vous — au-dela de leur rayon, elles ne peuvent pas vous livrer.
      </p>

      <section id="catalogue" class="scroll-mt-24 py-10">
        <div class="flex items-start gap-8">
          <BarreFiltres
            v-model:categorie="categorie"
            v-model:boutique="boutique"
            v-model:service="service"
            :univers="univers"
            :boutiques="boutiques"
            :total="totalAvantFiltres"
            class="hidden lg:block"
          />

          <div class="min-w-0 flex-1">
            <div class="flex flex-wrap items-end justify-between gap-3">
              <div>
                <h2 class="text-[19px] font-semibold tracking-tight text-white">
                  <template v-if="recherche">Resultats pour « {{ recherche }} »</template>
                  <template v-else>Le catalogue</template>
                </h2>
                <p class="mt-1 text-[13px] text-[#b49a8c]">
                  {{ produits.length }} produit{{ produits.length > 1 ? 's' : '' }}
                  <template v-if="position.connue"> · livrable a {{ position.libelle }}</template>
                </p>
              </div>

              <button
                v-if="recherche"
                type="button"
                class="bouton-discret !py-2 text-[12.5px]"
                @click="effacerRecherche"
              >
                <X :size="14" />
                Effacer la recherche
              </button>
            </div>

            <div v-if="chargement" class="mt-6 grid gap-5 sm:grid-cols-2 xl:grid-cols-3">
              <div
                v-for="n in 6"
                :key="n"
                class="overflow-hidden rounded-2xl border border-encre-3 bg-encre-2/40"
              >
                <Squelette hauteur="170px" />
                <div class="flex flex-col gap-2 p-4">
                  <Squelette hauteur="0.9rem" largeur="80%" />
                  <Squelette hauteur="0.8rem" largeur="50%" />
                  <Squelette hauteur="1rem" largeur="35%" />
                </div>
              </div>
            </div>

            <div v-else-if="produits.length" class="mt-6 grid gap-5 sm:grid-cols-2 xl:grid-cols-3">
              <CarteProduit v-for="produit in produits" :key="produit.id" :produit="produit" />
            </div>

            <div
              v-else
              class="mt-6 flex flex-col items-center rounded-2xl border border-encre-3
                     bg-encre-2/30 px-6 py-16 text-center"
            >
              <span
                class="flex h-14 w-14 items-center justify-center rounded-2xl bg-marque/10 text-marque"
              >
                <Search :size="24" />
              </span>
              <b class="mt-4 text-[15px] text-white">Aucun produit ne correspond</b>
              <p class="mt-1.5 max-w-[46ch] text-[13.5px] text-[#b49a8c]">
                <template v-if="!position.connue && service === 'EXPRESS'">
                  Les boutiques Express n'apparaissent qu'une fois votre ville indiquee, en
                  haut de page.
                </template>
                <template v-else-if="recherche">
                  Aucun resultat pour « {{ recherche }} ». Essayez un autre mot, ou effacez
                  la recherche.
                </template>
                <template v-else>Retirez un filtre pour elargir le resultat.</template>
              </p>
              <button
                v-if="categorie || boutique || service || recherche"
                type="button"
                class="bouton-discret mt-5"
                @click="categorie = undefined; boutique = undefined; service = undefined; effacerRecherche()"
              >
                Tout effacer
              </button>
            </div>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<style scoped>
/* La dinde se balance doucement, comme posee sur le R. Deux mouvements
   combines — vertical et rotation — pour que ce ne soit pas mecanique. */
.mascotte {
  animation: flotter 5.5s ease-in-out infinite;
  filter: drop-shadow(0 24px 32px rgb(0 0 0 / 0.45));
  transform-origin: 50% 85%;
}

@keyframes flotter {
  0%,
  100% {
    transform: translateY(0) rotate(-1.2deg);
  }
  50% {
    transform: translateY(-14px) rotate(1.4deg);
  }
}

/* Certaines personnes ont mal au coeur devant une animation continue. Le
   systeme le signale, on l'ecoute. */
@media (prefers-reduced-motion: reduce) {
  .mascotte {
    animation: none;
  }
}
</style>
