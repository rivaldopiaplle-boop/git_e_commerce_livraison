<script setup lang="ts">
// Toutes les boutiques, quel que soit leur statut.
//
// L'ecran de validation ne montrait que ce qui attend une decision : on ne
// savait jamais ce qu'un dossier refuse etait devenu, ni combien de boutiques
// tournaient reellement. Les livreurs sont dans le second onglet, pour la
// meme raison.
import { Bike, Package, Search, Store, Truck } from '@lucide/vue'
import { computed, onMounted, ref } from 'vue'

import { espaces } from '../../api/espaces'
import Onglets from '../../composants/Onglets.vue'
import Squelette from '../../composants/Squelette.vue'

type Boutique = {
  id: number
  nom_boutique: string
  type_activite: string
  statut_validation: string
  ville: string
  responsable: string
  email: string
  produits: number
  commandes: number
  description: string
}
type LivreurAdmin = {
  id: number
  nom: string
  email: string
  mode_livraison: string
  vehicule: string
  entrepot: string
  statut_validation: string
  statut_disponibilite: string
  livraisons: number
}

const boutiques = ref<Boutique[]>([])
const livreurs = ref<LivreurAdmin[]>([])
const chargement = ref(true)
const onglet = ref('boutiques')
const recherche = ref('')

onMounted(async () => {
  try {
    const [b, l] = await Promise.all([espaces.admin.boutiques(), espaces.admin.livreurs()])
    boutiques.value = b as unknown as Boutique[]
    livreurs.value = l as unknown as LivreurAdmin[]
  } finally {
    chargement.value = false
  }
})

const STATUTS: Record<string, string> = {
  VALIDE: 'badge-ok',
  EN_ATTENTE: 'badge-attente',
  REJETE: 'badge-erreur',
  SUSPENDU: 'badge-neutre',
}

const boutiquesVisibles = computed(() => {
  const texte = recherche.value.trim().toLowerCase()
  if (!texte) return boutiques.value
  return boutiques.value.filter((boutique) =>
    `${boutique.nom_boutique} ${boutique.ville} ${boutique.responsable} ${boutique.email}`
      .toLowerCase()
      .includes(texte),
  )
})
</script>

<template>
  <div class="mx-auto max-w-[1020px] animate-[apparition_0.2s_ease-out]">
    <Onglets
      v-model="onglet"
      :onglets="[
        { cle: 'boutiques', libelle: 'Boutiques', compteur: boutiques.length },
        { cle: 'livreurs', libelle: 'Livreurs', compteur: livreurs.length },
      ]"
    />

    <div
      v-if="onglet === 'boutiques'"
      class="mb-4 flex items-center gap-2 rounded-full bg-papier px-3.5 py-2 ring-1 ring-trait"
    >
      <Search :size="14" class="text-encre-douce" />
      <input
        v-model="recherche"
        type="search"
        placeholder="Nom de boutique, ville, responsable…"
        class="w-full bg-transparent text-[12.5px] focus:outline-none"
      />
    </div>

    <div v-if="chargement" class="flex flex-col gap-2">
      <Squelette v-for="n in 5" :key="n" hauteur="56px" />
    </div>

    <div v-else-if="onglet === 'boutiques'" class="carte">
      <div v-if="!boutiquesVisibles.length" class="vide">
        <Store :size="30" class="text-trait" />
        <b class="vide-titre">Aucune boutique ne correspond</b>
      </div>

      <div v-for="boutique in boutiquesVisibles" :key="boutique.id" class="ligne">
        <span
          class="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg"
          :style="{ background: 'var(--accent-doux)', color: 'var(--accent)' }"
        >
          <component :is="boutique.type_activite === 'EXPRESS' ? Bike : Package" :size="16" />
        </span>
        <span class="min-w-0 flex-1">
          <b class="block truncate">{{ boutique.nom_boutique }}</b>
          <span class="text-[11.2px] text-encre-douce">
            {{ boutique.responsable }} · {{ boutique.email }}
            <template v-if="boutique.ville"> · {{ boutique.ville }}</template>
          </span>
        </span>
        <span class="badge badge-neutre w-[86px] justify-center">
          {{ boutique.type_activite.toLowerCase() }}
        </span>
        <span class="hidden w-24 text-right text-encre-douce sm:block">
          {{ boutique.produits }} produit(s)
        </span>
        <span class="hidden w-24 text-right text-encre-douce lg:block">
          {{ boutique.commandes }} commande(s)
        </span>
        <span class="badge w-[92px] justify-center"
              :class="STATUTS[boutique.statut_validation] ?? 'badge-neutre'">
          {{ boutique.statut_validation.toLowerCase().replace(/_/g, ' ') }}
        </span>
      </div>
    </div>

    <div v-else class="carte">
      <div v-if="!livreurs.length" class="vide">
        <Truck :size="30" class="text-trait" />
        <b class="vide-titre">Aucun livreur inscrit</b>
      </div>

      <div v-for="livreur in livreurs" :key="livreur.id" class="ligne">
        <span
          class="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg"
          :style="{ background: 'var(--accent-doux)', color: 'var(--accent)' }"
        >
          <component :is="livreur.mode_livraison === 'EXPRESS' ? Bike : Truck" :size="16" />
        </span>
        <span class="min-w-0 flex-1">
          <b class="block truncate">{{ livreur.nom }}</b>
          <span class="text-[11.2px] text-encre-douce">
            {{ livreur.email }} · {{ livreur.vehicule }}
            <template v-if="livreur.entrepot"> · {{ livreur.entrepot }}</template>
          </span>
        </span>
        <span class="badge badge-neutre w-[86px] justify-center">
          {{ livreur.mode_livraison.toLowerCase() }}
        </span>
        <span class="hidden w-28 text-right text-encre-douce sm:block">
          {{ livreur.livraisons }} livraison(s)
        </span>
        <span class="badge w-[92px] justify-center"
              :class="STATUTS[livreur.statut_validation] ?? 'badge-neutre'">
          {{ livreur.statut_validation.toLowerCase().replace(/_/g, ' ') }}
        </span>
      </div>
    </div>
  </div>
</template>
