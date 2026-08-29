<script setup lang="ts">
// Le tableau de bord, par role.
//
// Ce n'est pas une carte d'identite : c'est le travail du jour. Un vendeur
// veut savoir ce qu'il doit preparer et ce qui manque en stock ; un admin, ce
// qui attend une decision ; un client, ou en sont ses commandes.
import {
  AlertTriangle, ArrowRight, Boxes, ClipboardList, Package, Receipt, ShieldCheck,
  ShoppingBag, Store, TrendingUp, Truck, Users,
} from '@lucide/vue'
import { computed, onMounted, ref } from 'vue'

import { api } from '../api/client'
import Squelette from '../composants/Squelette.vue'
import { descriptionDuRole } from '../roles'
import { useAuthentification } from '../stores/authentification'

const session = useAuthentification()
const role = computed(() => descriptionDuRole(session.role))

type Indicateurs = Record<string, number | unknown[]>
const donnees = ref<Indicateurs>({})
const chargement = ref(true)

const CHEMINS: Record<string, string> = {
  VENDEUR: '/vendeurs/tableau-de-bord',
  GESTIONNAIRE: '/vendeurs/tableau-de-bord',
  ADMIN: '/admin/tableau-de-bord',
  CLIENT: '/moi/tableau-de-bord',
}

onMounted(async () => {
  const chemin = CHEMINS[session.role ?? '']
  if (!chemin) {
    chargement.value = false
    return
  }
  try {
    donnees.value = await api.get<Indicateurs>(chemin)
  } finally {
    chargement.value = false
  }
})

const euros = (centimes: number) =>
  (centimes / 100).toLocaleString('fr-FR', { style: 'currency', currency: 'EUR' })

const nombre = (cle: string) => Number(donnees.value[cle] ?? 0)

// Chaque role a ses propres indicateurs : afficher les memes pour tout le
// monde reviendrait a n'en afficher pour personne.
const INDICATEURS: Record<string, { cle: string; libelle: string; alerte?: boolean }[]> = {
  VENDEUR: [
    { cle: 'a_preparer', libelle: 'Commandes a preparer' },
    { cle: 'produits_en_ligne', libelle: 'Produits en ligne' },
    { cle: 'stock_bas', libelle: 'Sous le seuil d alerte', alerte: true },
    { cle: 'ruptures', libelle: 'En rupture', alerte: true },
  ],
  GESTIONNAIRE: [
    { cle: 'a_preparer', libelle: 'Commandes a preparer' },
    { cle: 'stock_bas', libelle: 'Sous le seuil d alerte', alerte: true },
    { cle: 'ruptures', libelle: 'En rupture', alerte: true },
  ],
  ADMIN: [
    { cle: 'a_valider', libelle: 'En attente de validation', alerte: true },
    { cle: 'boutiques_actives', libelle: 'Boutiques actives' },
    { cle: 'commandes_en_cours', libelle: 'Commandes en cours' },
    { cle: 'utilisateurs', libelle: 'Comptes' },
  ],
  CLIENT: [
    { cle: 'en_cours', libelle: 'Commandes en cours' },
    { cle: 'livrees', libelle: 'Commandes livrees' },
    { cle: 'commandes', libelle: 'Commandes au total' },
  ],
}

const indicateurs = computed(() => INDICATEURS[session.role ?? ''] ?? [])

type ProduitBref = { id: number; nom: string }
const stockBas = computed<ProduitBref[]>(() =>
  Array.isArray(donnees.value.produits_stock_bas)
    ? (donnees.value.produits_stock_bas as ProduitBref[])
    : [],
)

// Ce qui attend une action : la seule chose qu'un tableau de bord doit
// vraiment mettre en avant.
const ACTIONS: Record<string, { libelle: string; route: string; icone: unknown; cle?: string }[]> = {
  VENDEUR: [
    { libelle: 'Traiter les commandes', route: 'vendeur-commandes', icone: ClipboardList,
      cle: 'a_preparer' },
    { libelle: 'Reapprovisionner', route: 'vendeur-stock', icone: Boxes, cle: 'stock_bas' },
    { libelle: 'Ajouter un produit', route: 'vendeur-nouveau', icone: Package },
  ],
  GESTIONNAIRE: [
    { libelle: 'Commandes a preparer', route: 'vendeur-commandes', icone: ClipboardList,
      cle: 'a_preparer' },
    { libelle: 'Ajuster le stock', route: 'vendeur-stock', icone: Boxes, cle: 'stock_bas' },
  ],
  ADMIN: [
    { libelle: 'Valider les comptes', route: 'admin-validations', icone: ShieldCheck,
      cle: 'a_valider' },
  ],
  CLIENT: [
    { libelle: 'Suivre mes commandes', route: 'mes-commandes', icone: Receipt, cle: 'en_cours' },
    { libelle: 'Parcourir le catalogue', route: 'vitrine', icone: ShoppingBag },
  ],
  LIVREUR: [],
}
const actions = computed(() => ACTIONS[session.role ?? ''] ?? [])

const ICONES: Record<string, unknown> = {
  VENDEUR: Store, GESTIONNAIRE: Boxes, ADMIN: Users, CLIENT: ShoppingBag, LIVREUR: Truck,
}
</script>

<template>
  <div class="mx-auto max-w-[1100px] animate-[apparition_0.2s_ease-out]">
    <!-- Les indicateurs, dans la rangee de KPI de la maquette -->
    <div v-if="chargement" class="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
      <Squelette v-for="n in 4" :key="n" hauteur="72px" />
    </div>

    <div
      v-else-if="indicateurs.length"
      class="grid gap-3 sm:grid-cols-2 lg:grid-cols-4"
    >
      <div
        v-for="indicateur in indicateurs"
        :key="indicateur.cle"
        class="kpi"
        :class="indicateur.alerte && nombre(indicateur.cle) ? 'border-[#ffe2b3] bg-[#fff6ea]' : ''"
      >
        <div class="kpi-nombre" :class="indicateur.alerte && nombre(indicateur.cle) ? 'text-[#b5610a]' : ''">
          {{ nombre(indicateur.cle) }}
        </div>
        <div class="kpi-libelle">{{ indicateur.libelle }}</div>
      </div>

      <div v-if="session.role === 'VENDEUR'" class="kpi">
        <div class="kpi-nombre">{{ euros(nombre('revenu_centimes')) }}</div>
        <div class="kpi-libelle">Encaisse, commission deduite</div>
      </div>
      <div v-if="session.role === 'CLIENT'" class="kpi">
        <div class="kpi-nombre">{{ euros(nombre('total_depense_centimes')) }}</div>
        <div class="kpi-libelle">Total depense</div>
      </div>
    </div>

    <!-- Ce qui attend une action -->
    <div v-if="actions.length" class="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
      <RouterLink
        v-for="action in actions"
        :key="action.libelle"
        :to="{ name: action.route }"
        class="carte flex items-center gap-3 p-4 transition-shadow hover:shadow-md"
      >
        <span
          class="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg"
          :style="{ background: 'var(--accent-doux)', color: 'var(--accent)' }"
        >
          <component :is="action.icone" :size="19" />
        </span>
        <span class="min-w-0 flex-1">
          <b class="block text-[13.5px]">{{ action.libelle }}</b>
          <span v-if="action.cle" class="text-[12px] text-encre-douce">
            {{ nombre(action.cle) }} en attente
          </span>
        </span>
        <ArrowRight :size="16" class="text-encre-douce" />
      </RouterLink>
    </div>

    <!-- Le stock bas, en toutes lettres : c'est ce qui coute une vente -->
    <section
      v-if="stockBas.length"
      class="carte mt-4"
    >
      <h3 class="carte-titre">
        <span class="flex items-center gap-2">
          <AlertTriangle :size="15" class="text-[#b5610a]" />
          Produits a reapprovisionner
        </span>
        <RouterLink :to="{ name: 'vendeur-stock' }" class="mini text-[11px] font-semibold
                                                            text-encre-douce hover:text-encre">
          Tout voir
        </RouterLink>
      </h3>
      <div
        v-for="produit in stockBas"
        :key="produit.id"
        class="ligne"
      >
        <span class="flex-1 font-bold">{{ produit.nom }}</span>
        <span class="badge badge-attente">a reapprovisionner</span>
      </div>
    </section>

    <!-- Le livreur n'a pas d'espace web : on le dit, on ne bricole pas -->
    <section v-if="session.role === 'LIVREUR'" class="carte mt-4 p-8 text-center">
      <span
        class="mx-auto flex h-14 w-14 items-center justify-center rounded-lg"
        :style="{ background: 'var(--accent-doux)', color: 'var(--accent)' }"
      >
        <component :is="ICONES.LIVREUR" :size="24" />
      </span>
      <b class="mt-4 block text-[15px]">Vos courses sont sur l application mobile</b>
      <p class="mx-auto mt-1.5 max-w-[52ch] text-[13px] text-encre-douce">
        Accepter une course, suivre une tournee, confirmer une livraison : tout cela se
        fait une main sur le guidon, pas devant un ecran d ordinateur. Cet espace web
        servira au suivi et aux gains.
      </p>
    </section>

    <section v-if="session.role === 'CLIENT'" class="carte mt-4">
      <h3 class="carte-titre">
        <span class="flex items-center gap-2"><TrendingUp :size="15" /> Mon compte</span>
      </h3>
      <div class="ligne">
        <span class="flex-1 text-encre-douce">Nom</span>
        <b>{{ session.utilisateur?.prenom }} {{ session.utilisateur?.nom }}</b>
      </div>
      <div class="ligne">
        <span class="flex-1 text-encre-douce">Adresse e-mail</span>
        <b>{{ session.utilisateur?.email }}</b>
      </div>
    </section>
  </div>
</template>
