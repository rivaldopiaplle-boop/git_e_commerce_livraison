<script setup lang="ts">
// Le catalogue du vendeur : la liste dense de la maquette, avec les
// boutons-icones encadres de ses listes (regle d'or n°9).
//
// Ce que l'ecran ne savait pas faire, et qui lui etait reproche a juste
// titre : les boutons ne faisaient pas leur travail. « Voir » ouvrait la
// fiche PUBLIQUE d'un produit parfois masque — donc une page vide ; « masquer »
// n'avait pas d'inverse, et un produit retire l'etait pour toujours ; rien ne
// permettait de declarer une rupture, alors que c'est le geste le plus
// frequent d'un commercant.
import {
  AlertTriangle, Eye, EyeOff, ImageOff, Package, PackageX, Pencil, Plus, RotateCcw, Search,
} from '@lucide/vue'
import { computed, onMounted, ref } from 'vue'

import { EchecApi } from '../../api/client'
import { vendeur, type ProduitCatalogue } from '../../api/vendeur'
import Onglets from '../../composants/Onglets.vue'
import Popup from '../../composants/Popup.vue'
import Squelette from '../../composants/Squelette.vue'

const produits = ref<ProduitCatalogue[]>([])
const chargement = ref(true)
const filtre = ref('')
const onglet = ref('en-vente')
const erreur = ref('')

// La popup de rupture : declarer un produit epuise est une action courte,
// mais elle laisse une trace au meme titre qu'un ajustement (scenario 4.4).
const enRupture = ref<ProduitCatalogue | null>(null)
const motifRupture = ref('Rupture constatee en boutique')
const occupe = ref(false)

async function charger() {
  chargement.value = true
  try {
    produits.value = await vendeur.mesProduits()
  } finally {
    chargement.value = false
  }
}

onMounted(charger)

const enVente = computed(() => produits.value.filter((p) => p.est_visible))
const retires = computed(() => produits.value.filter((p) => !p.est_visible))
const ruptures = computed(() => enVente.value.filter((p) => p.est_en_rupture))

const visibles = computed(() => {
  const base =
    onglet.value === 'retires' ? retires.value
      : onglet.value === 'ruptures' ? ruptures.value
        : enVente.value
  const recherche = filtre.value.trim().toLowerCase()
  return recherche ? base.filter((p) => p.nom.toLowerCase().includes(recherche)) : base
})

const euros = (centimes: number) =>
  (centimes / 100).toLocaleString('fr-FR', { style: 'currency', currency: 'EUR' })

async function agir(action: Promise<unknown>) {
  erreur.value = ''
  occupe.value = true
  try {
    await action
    await charger()
  } catch (echec) {
    erreur.value = echec instanceof EchecApi ? echec.erreur.message : "L action a echoue."
  } finally {
    occupe.value = false
  }
}

async function declarerRupture() {
  if (!enRupture.value) return
  const produit = enRupture.value
  enRupture.value = null
  await agir(vendeur.stock.definir(produit.id, 0, 'AJUSTEMENT', motifRupture.value))
  motifRupture.value = 'Rupture constatee en boutique'
}
</script>

<template>
  <div class="mx-auto max-w-[1100px] animate-[apparition_0.2s_ease-out]">
    <Onglets
      v-model="onglet"
      :onglets="[
        { cle: 'en-vente', libelle: 'En vente', compteur: enVente.length },
        { cle: 'ruptures', libelle: 'En rupture', compteur: ruptures.length },
        { cle: 'retires', libelle: 'Retires de la vente', compteur: retires.length },
      ]"
    />

    <div class="mb-4 flex flex-wrap items-center justify-between gap-3">
      <div class="flex items-center gap-2 rounded-full bg-papier px-3.5 py-2 ring-1 ring-trait">
        <Search :size="14" class="text-encre-douce" />
        <input
          v-model="filtre"
          type="search"
          placeholder="Filtrer mes produits…"
          class="w-56 bg-transparent text-[12.5px] focus:outline-none"
        />
      </div>

      <RouterLink :to="{ name: 'vendeur-nouveau' }" class="bouton-accent">
        <Plus :size="16" />
        Nouveau produit
      </RouterLink>
    </div>

    <p v-if="erreur" class="bandeau bandeau-erreur mb-3">
      <AlertTriangle :size="15" class="mt-px shrink-0" />
      {{ erreur }}
    </p>

    <div v-if="chargement" class="flex flex-col gap-2">
      <Squelette v-for="n in 5" :key="n" hauteur="58px" />
    </div>

    <!-- Etat vide pense : un vendeur qui arrive sur une page blanche croit que
         l'application est cassee (regle d'or n°2). -->
    <div v-else-if="!produits.length" class="carte">
      <div class="vide">
        <span
          class="flex h-14 w-14 items-center justify-center rounded-lg"
          :style="{ background: 'var(--accent-doux)', color: 'var(--accent)' }"
        >
          <Package :size="24" />
        </span>
        <b class="vide-titre">Votre catalogue est vide</b>
        <p class="vide-texte">
          Ajoutez votre premier produit : un nom, un prix, une photo. Il apparaitra
          aussitot au catalogue de vos clients.
        </p>
        <RouterLink :to="{ name: 'vendeur-nouveau' }" class="bouton-accent mt-4">
          <Plus :size="16" />
          Ajouter un produit
        </RouterLink>
      </div>
    </div>

    <div v-else-if="!visibles.length" class="carte">
      <div class="vide">
        <Package :size="30" class="text-trait" />
        <b class="vide-titre">
          {{
            onglet === 'ruptures' ? 'Aucune rupture — tout est disponible'
            : onglet === 'retires' ? 'Aucun produit retire de la vente'
            : 'Aucun produit ne correspond a ce filtre'
          }}
        </b>
      </div>
    </div>

    <div v-else class="carte">
      <h3 class="carte-titre">
        <span>{{ visibles.length }} produit{{ visibles.length > 1 ? 's' : '' }}</span>
        <span class="text-[11px] font-semibold text-encre-douce">
          prix · stock · etat
        </span>
      </h3>

      <div v-for="produit in visibles" :key="produit.id" class="ligne">
        <img
          v-if="produit.image"
          :src="produit.image"
          :alt="produit.nom"
          class="h-10 w-10 shrink-0 rounded-lg object-cover"
          :class="produit.est_visible ? '' : 'opacity-40 grayscale'"
        />
        <span
          v-else
          class="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-atelier
                 text-encre-douce"
        >
          <ImageOff :size="15" />
        </span>

        <span class="min-w-0 flex-1">
          <b class="block truncate">{{ produit.nom }}</b>
          <span class="text-[11.2px] text-encre-douce">
            {{ produit.categorie?.nom ?? 'Sans categorie' }}
            <template v-if="produit.nombre_photos < 1"> · aucune photo</template>
          </span>
        </span>

        <span class="w-24 shrink-0 text-right font-bold">{{ euros(produit.prix_centimes) }}</span>

        <span class="w-20 shrink-0 text-right text-encre-douce">
          {{ produit.stock_disponible }} en stock
        </span>

        <span
          class="badge w-[104px] shrink-0 justify-center"
          :class="
            !produit.est_visible ? 'badge-neutre'
            : produit.est_en_rupture ? 'badge-erreur'
            : produit.stock_disponible <= produit.seuil_alerte ? 'badge-attente'
            : 'badge-ok'
          "
        >
          {{
            !produit.est_visible ? 'retire'
            : produit.est_en_rupture ? 'rupture'
            : produit.stock_disponible <= produit.seuil_alerte ? 'stock bas'
            : 'en vente'
          }}
        </span>

        <span class="flex shrink-0 gap-1.5">
          <!-- « Voir » n'ouvre la fiche publique que si le produit y est
               reellement : sinon le bouton menait a une page vide. -->
          <RouterLink
            v-if="produit.est_visible"
            :to="{ name: 'produit', params: { id: produit.id } }"
            class="bouton-ligne"
            title="Voir la fiche publique"
          >
            <Eye :size="14" />
            <span class="sr-only">Voir la fiche publique</span>
          </RouterLink>
          <span v-else class="bouton-ligne opacity-40" title="Retire de la vente : pas de fiche publique">
            <Eye :size="14" />
          </span>

          <RouterLink
            :to="{ name: 'vendeur-produit', params: { id: produit.id } }"
            class="bouton-ligne"
            title="Modifier ce produit"
          >
            <Pencil :size="14" />
            <span class="sr-only">Modifier</span>
          </RouterLink>

          <button
            v-if="produit.est_visible && !produit.est_en_rupture"
            type="button"
            class="bouton-ligne"
            title="Declarer une rupture de stock"
            :disabled="occupe"
            @click="enRupture = produit"
          >
            <PackageX :size="14" />
            <span class="sr-only">Declarer une rupture</span>
          </button>

          <button
            v-if="produit.est_visible"
            type="button"
            class="bouton-ligne bouton-ligne-danger"
            title="Retirer de la vente"
            :disabled="occupe"
            @click="agir(vendeur.masquer(produit.id))"
          >
            <EyeOff :size="14" />
            <span class="sr-only">Retirer de la vente</span>
          </button>
          <button
            v-else
            type="button"
            class="bouton-ligne bouton-ligne-accent"
            title="Remettre en vente"
            :disabled="occupe"
            @click="agir(vendeur.remettreEnVente(produit.id))"
          >
            <RotateCcw :size="14" />
            <span class="sr-only">Remettre en vente</span>
          </button>
        </span>
      </div>
    </div>

    <!-- La popup de la maquette : une action courte, un motif obligatoire,
         une phrase qui dit ce qui va se passer cote client. -->
    <Popup
      v-if="enRupture"
      titre="Declarer une rupture de stock"
      :explication="`Le stock de « ${enRupture.nom} » passe a zero. Le produit reste au catalogue,
                     son bouton d'achat est gele et vos clients peuvent demander a etre prevenus
                     de son retour. Le mouvement est trace dans l'historique.`"
      @fermer="enRupture = null"
    >
      <label class="flex flex-col gap-1.5">
        <span class="etiquette">Motif</span>
        <input v-model="motifRupture" class="champ-clair" required />
      </label>

      <template #actions>
        <button type="button" class="bouton-neutre !py-2" @click="enRupture = null">
          Annuler
        </button>
        <button
          type="button"
          class="bouton-accent !py-2"
          :disabled="occupe || !motifRupture.trim()"
          @click="declarerRupture"
        >
          <PackageX :size="15" />
          Declarer la rupture
        </button>
      </template>
    </Popup>
  </div>
</template>
