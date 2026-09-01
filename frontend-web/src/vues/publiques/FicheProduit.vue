<script setup lang="ts">
// La fiche produit : galerie, prix, boutique, disponibilite, ajout au panier.
//
// En rupture, le bouton est GELE et double d'une alerte de retour en stock
// (D-06) : le produit reste au catalogue, sinon on perd le client au lieu de
// le faire patienter.
import {
  ArrowLeft, Bell, Bike, ChevronLeft, ChevronRight, Clock, MapPin, MessageSquare,
  Package, Play, ShieldCheck, ShoppingCart, Star,
} from '@lucide/vue'
import Rating from 'primevue/rating'
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'

import { api, EchecApi } from '../../api/client'
import { catalogue, type ProduitDetail } from '../../api/catalogue'
import Squelette from '../../composants/Squelette.vue'
import { usePanier } from '../../stores/panier'
import { useAuthentification } from '../../stores/authentification'
import { usePosition } from '../../stores/position'

const route = useRoute()
const position = usePosition()
const panier = usePanier()
const session = useAuthentification()

const alerteInscrite = ref(false)
const alerteMessage = ref('')

async function demanderAlerte() {
  alerteMessage.value = ''
  if (!session.estConnecte) {
    alerteMessage.value = "Creez un compte pour etre prevenu : il nous faut une adresse ou vous ecrire."
    return
  }
  try {
    await api.post(`/produits/${route.params.id}/alerte-dispo`)
    alerteInscrite.value = true
    alerteMessage.value = 'Nous vous previendrons des que ce produit revient.'
  } catch (echec) {
    alerteMessage.value =
      echec instanceof EchecApi ? echec.erreur.message : "L inscription a echoue."
  }
}

const produit = ref<ProduitDetail | null>(null)
const chargement = ref(true)
const introuvable = ref(false)
const photoActive = ref(0)

async function charger() {
  chargement.value = true
  introuvable.value = false
  try {
    produit.value = await catalogue.produit(route.params.id as string, position.parametres)
    photoActive.value = 0
  } catch {
    introuvable.value = true
  } finally {
    chargement.value = false
  }
}

onMounted(charger)
watch(() => route.params.id, charger)

const prix = computed(() =>
  produit.value
    ? (produit.value.prix_centimes / 100).toLocaleString('fr-FR', {
        style: 'currency',
        currency: 'EUR',
      })
    : '',
)
const estExpress = computed(() => produit.value?.boutique?.type_service === 'EXPRESS')
// `photos?.length` et non `photos.length` : si la charge utile change de
// forme, l'ecran doit se degrader, pas planter toute l'application.
type Media = {
  id: number
  url: string
  texte_alternatif: string
  /** `apercu` : l'animation ou la video, toujours en dernier. */
  genre: 'photo' | 'apercu'
  video?: boolean
}

// L'apercu anime ferme la galerie plutot que de l'ouvrir : on regarde d'abord
// le produit, on l'anime ensuite. C'est l'ordre de toutes les fiches produit
// des vraies places de marche.
const medias = computed<Media[]>(() => {
  const produits = produit.value
  if (!produits) return []

  const vues: Media[] = produits.photos?.length
    ? produits.photos.map((photo) => ({ ...photo, genre: 'photo' as const }))
    : produits.image
      ? [{ id: 0, url: produits.image, texte_alternatif: produits.nom, genre: 'photo' as const }]
      : []

  if (produits.apercu) {
    vues.push({
      id: -1,
      url: produits.apercu.url,
      texte_alternatif: `${produits.nom} — apercu anime`,
      genre: 'apercu',
      video: produits.apercu.genre === 'video',
    })
  }
  return vues
})

const mediaCourant = computed(() => medias.value[photoActive.value] ?? null)

/** Fleches du clavier : une galerie qui ne repond qu'a la souris exclut. */
function deplacer(pas: number) {
  if (!medias.value.length) return
  photoActive.value = (photoActive.value + pas + medias.value.length) % medias.value.length
}
</script>

<template>
  <div class="mx-auto max-w-[1240px] px-5 py-10">
    <RouterLink
      to="/"
      class="inline-flex items-center gap-2 text-[13.5px] text-encre-douce transition-colors
             hover:text-[color:var(--accent)]"
    >
      <ArrowLeft :size="15" />
      Retour au catalogue
    </RouterLink>

    <div v-if="chargement" class="mt-6 grid gap-10 lg:grid-cols-2">
      <Squelette hauteur="420px" />
      <div class="flex flex-col gap-4">
        <Squelette hauteur="2rem" largeur="70%" />
        <Squelette hauteur="1rem" largeur="40%" />
        <Squelette hauteur="6rem" />
      </div>
    </div>

    <div
      v-else-if="introuvable"
      class="mt-10 rounded-2xl border border-trait bg-papier px-6 py-16 text-center"
    >
      <b class="text-[16px] text-encre">Ce produit n'est plus au catalogue</b>
      <p class="mt-2 text-[13.5px] text-encre-douce">
        Il a peut-etre ete retire par sa boutique, ou celle-ci ne livre pas votre ville.
      </p>
    </div>

    <article v-else-if="produit" class="mt-6 grid gap-10 lg:grid-cols-2">
      <!-- Galerie : grande image, vignettes dessous — le premier reflexe d'un
           acheteur (design-system.md § 9). -->
      <div>
        <div
          class="group relative overflow-hidden rounded-2xl border border-trait bg-atelier"
          tabindex="0"
          @keydown.left.prevent="deplacer(-1)"
          @keydown.right.prevent="deplacer(1)"
        >
          <!-- Une vraie video se joue ; un apercu anime est une image. Le
               serveur dit lequel, l'ecran ne le devine pas. -->
          <video
            v-if="mediaCourant?.genre === 'apercu' && mediaCourant.video"
            :src="mediaCourant.url"
            class="aspect-4/3 w-full object-cover"
            controls
            playsinline
            muted
            loop
          />
          <img
            v-else-if="mediaCourant"
            :src="mediaCourant.url"
            :alt="mediaCourant.texte_alternatif"
            class="aspect-4/3 w-full object-cover"
          />

          <!-- Les fleches n'apparaissent qu'au survol, mais elles existent
               toujours pour le clavier et les lecteurs d'ecran. -->
          <template v-if="medias.length > 1">
            <button
              type="button"
              class="fleche-galerie left-3"
              title="Vue precedente"
              @click="deplacer(-1)"
            >
              <ChevronLeft :size="18" />
              <span class="sr-only">Vue precedente</span>
            </button>
            <button
              type="button"
              class="fleche-galerie right-3"
              title="Vue suivante"
              @click="deplacer(1)"
            >
              <ChevronRight :size="18" />
              <span class="sr-only">Vue suivante</span>
            </button>
            <span
              class="pointer-events-none absolute bottom-3 right-3 rounded-full bg-encre/70
                     px-2.5 py-1 text-[11px] font-semibold text-papier"
            >
              {{ photoActive + 1 }} / {{ medias.length }}
            </span>
          </template>
        </div>

        <div v-if="medias.length > 1" class="mt-3 flex flex-wrap gap-3">
          <button
            v-for="(media, index) in medias"
            :key="media.id"
            type="button"
            class="relative h-20 w-24 overflow-hidden rounded-xl border transition-colors
                   duration-150"
            :class="index === photoActive
              ? 'border-[color:var(--accent)]'
              : 'border-trait hover:border-encre-douce'"
            :title="media.genre === 'apercu' ? 'Apercu anime' : media.texte_alternatif"
            @click="photoActive = index"
          >
            <img :src="media.url" :alt="media.texte_alternatif"
                 class="h-full w-full object-cover" />
            <!-- Le symbole de lecture dit ce qui se cache derriere la
                 vignette : sans lui, la derniere image ressemble aux autres. -->
            <span
              v-if="media.genre === 'apercu'"
              class="absolute inset-0 flex items-center justify-center bg-encre/35 text-papier"
            >
              <Play :size="18" />
            </span>
          </button>
        </div>
      </div>

      <div>
        <div class="flex items-center gap-2">
          <span
            class="badge"
            :class="estExpress ? 'badge-attente' : 'badge-neutre'"
          >
            <component :is="estExpress ? Bike : Package" :size="12" />
            {{ estExpress ? 'Livraison Express' : 'Livraison Standard' }}
          </span>
          <span v-if="produit.categorie" class="text-[12.5px] text-encre-douce">
            {{ produit.categorie.nom }}
          </span>
        </div>

        <h1 class="mt-4 text-[30px] leading-tight font-semibold tracking-tight text-encre">
          {{ produit.nom }}
        </h1>

        <p class="mt-2 flex items-center gap-2 text-[13.5px] text-encre-douce">
          <MapPin :size="14" />
          {{ produit.boutique?.nom }} · {{ produit.boutique?.ville }}
          <template v-if="produit.distance_km"> · {{ produit.distance_km }} km</template>
        </p>

        <p class="mt-6 text-[32px] font-bold text-[color:var(--accent)]">{{ prix }}</p>

        <p class="mt-5 text-[14.5px] leading-relaxed text-encre-douce">
          {{ produit.description }}
        </p>

        <!-- Disponibilite : bouton gele plutot que masque, avec l'alerte de
             retour en stock (D-06). -->
        <div class="mt-7 flex flex-col gap-3">
          <button
            v-if="produit.disponible"
            type="button"
            class="bouton-accent w-full"
            :disabled="panier.occupe"
            @click="panier.ajouter(produit.id)"
          >
            <ShoppingCart :size="17" />
            {{ panier.occupe ? 'Ajout…' : 'Ajouter au panier' }}
          </button>
          <template v-else>
            <button type="button" class="bouton-accent w-full cursor-not-allowed opacity-40" disabled>
              <ShoppingCart :size="17" />
              Indisponible
            </button>
            <button
              type="button"
              class="bouton-neutre w-full"
              :disabled="alerteInscrite"
              @click="demanderAlerte"
            >
              <Bell :size="15" />
              {{ alerteInscrite ? 'Vous serez prevenu' : 'Etre alerte quand ce produit revient' }}
            </button>
            <p v-if="alerteMessage" class="text-center text-[12px] text-encre-douce">
              {{ alerteMessage }}
            </p>
          </template>

          <p class="text-center text-[12px] text-encre-douce">
            Le paiement arrive a la tranche 5. Le panier, lui, fonctionne — et il vous suit
            si vous creez un compte ensuite.
          </p>
        </div>

        <!-- La note, la ou on la cherche : sous le titre du produit -->
        <RouterLink
          v-if="produit.avis?.nombre"
          to="#avis"
          class="mt-3 inline-flex items-center gap-2 text-[13px] text-encre-douce
                 transition-colors hover:text-encre"
        >
          <Rating :model-value="Math.round(produit.avis?.note_moyenne ?? 0)" readonly />
          <b class="text-encre">{{ produit.avis?.note_moyenne }}</b>
          <span>· {{ produit.avis?.nombre }} avis</span>
        </RouterLink>

        <ul class="mt-8 flex flex-col gap-3 border-t border-trait pt-6">
          <li class="flex items-center gap-3 text-[13.5px] text-encre-douce">
            <Clock :size="16" class="text-[color:var(--accent)]" />
            <template v-if="estExpress">Prepare et livre directement, en minutes.</template>
            <template v-else>Regroupe en entrepot, livre en tournee sous 48 a 72 heures.</template>
          </li>
          <li class="flex items-center gap-3 text-[13.5px] text-encre-douce">
            <ShieldCheck :size="16" class="text-[color:var(--accent)]" />
            Boutique verifiee par la plateforme avant publication.
          </li>
        </ul>
      </div>
    </article>

    <!-- ── Ce que les clients en disent (D-71) ────────────────────────── -->
    <section v-if="produit" id="avis" class="carte mt-8">
      <h3 class="carte-titre">
        <span class="flex items-center gap-2">
          <MessageSquare :size="15" /> Avis des clients
        </span>
        <span v-if="produit.avis?.nombre" class="text-[11px] font-semibold text-encre-douce">
          {{ produit.avis?.nombre }} avis, sur le produit et sur la boutique
        </span>
      </h3>

      <div v-if="!produit.avis?.nombre" class="vide">
        <Star :size="30" class="text-trait" />
        <b class="vide-titre">Aucun avis pour l'instant</b>
        <p class="vide-texte">
          Seuls les clients ayant reçu leur commande peuvent en déposer un : c'est ce qui
          rend ceux d'en dessous crédibles.
        </p>
      </div>

      <template v-else>
        <!-- La répartition : une note moyenne seule ne dit pas si l'avis est
             partagé ou si deux extrêmes s'annulent. -->
        <div class="flex flex-col gap-4 border-b border-trait-doux p-4 sm:flex-row sm:items-center">
          <div class="shrink-0 text-center">
            <b class="block text-[34px] leading-none">{{ produit.avis?.note_moyenne }}</b>
            <Rating
              :model-value="Math.round(produit.avis?.note_moyenne ?? 0)"
              readonly
              class="mt-1"
            />
            <span class="mt-1 block text-[11.5px] text-encre-douce">
              {{ produit.avis?.nombre }} avis
            </span>
          </div>

          <div class="flex flex-1 flex-col gap-1">
            <div
              v-for="valeur in [5, 4, 3, 2, 1]"
              :key="valeur"
              class="flex items-center gap-2 text-[11.5px]"
            >
              <span class="w-8 shrink-0 text-encre-douce">{{ valeur }} ★</span>
              <span class="h-1.5 flex-1 overflow-hidden rounded-full bg-trait-doux">
                <span
                  class="block h-full rounded-full transition-[width] duration-300"
                  :style="{
                    width: `${((produit.avis?.repartition?.[String(valeur)] ?? 0)
                      / Math.max(1, produit.avis?.nombre ?? 1)) * 100}%`,
                    background: 'var(--accent)',
                  }"
                />
              </span>
              <span class="w-6 shrink-0 text-right text-encre-douce">
                {{ produit.avis?.repartition?.[String(valeur)] ?? 0 }}
              </span>
            </div>
          </div>
        </div>

        <article v-for="avis in produit.avis?.avis ?? []" :key="avis.id" class="ligne !items-start">
          <span
            class="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-atelier
                   text-[11.5px] font-bold text-encre-douce"
          >
            {{ avis.auteur.charAt(0) }}
          </span>
          <span class="min-w-0 flex-1">
            <span class="flex flex-wrap items-center gap-2">
              <b>{{ avis.auteur }}</b>
              <Rating :model-value="avis.note" readonly />
              <span class="text-[11px] text-encre-douce">
                sur {{ avis.porte_sur }} · {{ new Date(avis.date).toLocaleDateString('fr-FR') }}
              </span>
            </span>
            <p v-if="avis.commentaire" class="mt-1 leading-relaxed text-encre-douce">
              {{ avis.commentaire }}
            </p>
          </span>
        </article>
      </template>
    </section>

    <!-- ── Dans la même catégorie ─────────────────────────────────────── -->
    <section v-if="produit?.produits_similaires?.length" class="mt-8">
      <h3 class="mb-3 text-[15px] font-semibold">Dans la même catégorie</h3>
      <!-- Carrousel horizontal : découverte passive, pas recherche active
           (D-69). On n'en retient que deux ou trois en passant. -->
      <div class="flex gap-3 overflow-x-auto pb-2">
        <RouterLink
          v-for="autre in produit.produits_similaires"
          :key="autre.id"
          :to="{ name: 'produit', params: { id: autre.id } }"
          class="carte w-[168px] shrink-0 transition-shadow hover:shadow-md"
        >
          <img
            v-if="autre.image"
            :src="autre.image"
            :alt="autre.nom"
            class="aspect-4/3 w-full object-cover"
            :class="autre.disponible ? '' : 'opacity-40 grayscale'"
          />
          <span class="block p-3">
            <b class="block truncate text-[12.5px]">{{ autre.nom }}</b>
            <span class="text-[12px] font-bold" :style="{ color: 'var(--accent)' }">
              {{ (autre.prix_centimes / 100).toLocaleString('fr-FR', {
                style: 'currency', currency: 'EUR' }) }}
            </span>
          </span>
        </RouterLink>
      </div>
    </section>
  </div>
</template>
