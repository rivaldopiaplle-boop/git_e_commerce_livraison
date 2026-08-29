<script setup lang="ts">
// Le tableau de bord, par role.
//
// Ce n'est pas une carte d'identite : c'est le travail du jour. Un vendeur
// veut savoir ce qu'il doit preparer et ce qui manque en stock ; un admin, ce
// qui attend une decision ; un magasinier, ce qui est arrive a l'entrepot ;
// un client, ou en sont ses commandes.
//
// « Total depense » a disparu des indicateurs du client. La question etait
// juste : cela ne sert a rien. Personne n'ouvre une application de livraison
// pour se faire rappeler combien il a depense, et le chiffre ne declenche
// aucune action. A la place : ce qui arrive, et quand.
import {
  AlertTriangle, ArrowRight, Bike, Boxes, ClipboardList, MapPin, Package, Receipt,
  Route, ShieldCheck, ShoppingBag, Store, Truck, Users, Warehouse,
} from '@lucide/vue'
import { computed, onMounted, ref } from 'vue'

import { api } from '../api/client'
import Onglets from '../composants/Onglets.vue'
import Squelette from '../composants/Squelette.vue'
import { useAuthentification } from '../stores/authentification'

const session = useAuthentification()

type Indicateurs = Record<string, number | string | unknown[]>
const donnees = ref<Indicateurs>({})
const chargement = ref(true)
const onglet = ref('travail')

/** Quel tableau de bord aller chercher : le sous-role compte (D-05). */
const chemin = computed(() => {
  if (session.role === 'GESTIONNAIRE') {
    return session.estStaffEntrepot
      ? '/entrepots/tableau-de-bord'
      : '/vendeurs/tableau-de-bord'
  }
  const chemins: Record<string, string> = {
    VENDEUR: '/vendeurs/tableau-de-bord',
    ADMIN: '/admin/tableau-de-bord',
    CLIENT: '/moi/tableau-de-bord',
    LIVREUR: '/livreurs/tableau-de-bord',
  }
  return chemins[session.role ?? ''] ?? null
})

onMounted(async () => {
  if (!chemin.value) {
    chargement.value = false
    return
  }
  try {
    donnees.value = await api.get<Indicateurs>(chemin.value)
  } finally {
    chargement.value = false
  }
})

const euros = (centimes: number) =>
  (centimes / 100).toLocaleString('fr-FR', { style: 'currency', currency: 'EUR' })
const nombre = (cle: string) => Number(donnees.value[cle] ?? 0)

type Indicateur = { cle: string; libelle: string; alerte?: boolean; argent?: boolean }

// Chaque role a ses propres indicateurs : afficher les memes pour tout le
// monde reviendrait a n'en afficher pour personne.
const INDICATEURS: Record<string, Indicateur[]> = {
  VENDEUR: [
    { cle: 'a_preparer', libelle: 'Commandes a preparer' },
    { cle: 'produits_en_ligne', libelle: 'Produits en ligne' },
    { cle: 'stock_bas', libelle: 'Sous le seuil d alerte', alerte: true },
    { cle: 'ruptures', libelle: 'En rupture', alerte: true },
    { cle: 'revenu_centimes', libelle: 'Encaisse, commission deduite', argent: true },
  ],
  GESTIONNAIRE: [
    { cle: 'a_preparer', libelle: 'Commandes a preparer' },
    { cle: 'en_preparation', libelle: 'En cours de preparation' },
    { cle: 'stock_bas', libelle: 'Sous le seuil d alerte', alerte: true },
    { cle: 'ruptures', libelle: 'En rupture', alerte: true },
  ],
  GESTIONNAIRE_ENTREPOT: [
    { cle: 'colis_recus', libelle: 'Colis a receptionner' },
    { cle: 'boutiques_deposantes', libelle: 'Boutiques deposantes' },
    { cle: 'tournees_a_preparer', libelle: 'Tournees a preparer', alerte: true },
    { cle: 'tournees_en_cours', libelle: 'Tournees sur la route' },
    { cle: 'livreurs_rattaches', libelle: 'Livreurs rattaches' },
  ],
  LIVREUR: [
    { cle: 'en_cours', libelle: 'Courses en cours' },
    { cle: 'livrees', libelle: 'Livraisons reussies' },
    { cle: 'echouees', libelle: 'Livraisons echouees', alerte: true },
    { cle: 'gains_centimes', libelle: 'Gains cumules', argent: true },
  ],
  ADMIN: [
    { cle: 'a_valider', libelle: 'En attente de validation', alerte: true },
    { cle: 'boutiques_actives', libelle: 'Boutiques actives' },
    { cle: 'commandes_en_cours', libelle: 'Commandes en cours' },
    { cle: 'produits_en_ligne', libelle: 'Produits en ligne' },
    { cle: 'utilisateurs', libelle: 'Comptes' },
  ],
  CLIENT: [
    { cle: 'en_cours', libelle: 'Commandes en cours' },
    { cle: 'livrees', libelle: 'Commandes livrees' },
    { cle: 'commandes', libelle: 'Commandes au total' },
  ],
}

const cleRole = computed(() =>
  session.role === 'GESTIONNAIRE' && session.estStaffEntrepot
    ? 'GESTIONNAIRE_ENTREPOT'
    : (session.role ?? ''),
)
const indicateurs = computed(() => INDICATEURS[cleRole.value] ?? [])

type ProduitBref = { id: number; nom: string; stock_disponible: number; seuil_alerte: number }
const stockBas = computed<ProduitBref[]>(() =>
  Array.isArray(donnees.value.produits_stock_bas)
    ? (donnees.value.produits_stock_bas as ProduitBref[])
    : [],
)

// Ce qui attend une action : la seule chose qu'un tableau de bord doit
// vraiment mettre en avant.
type Action = { libelle: string; route: string; icone: unknown; cle?: string; aide: string }
const ACTIONS: Record<string, Action[]> = {
  VENDEUR: [
    { libelle: 'Traiter les commandes', route: 'vendeur-commandes', icone: ClipboardList,
      cle: 'a_preparer', aide: 'en attente' },
    { libelle: 'Reapprovisionner', route: 'vendeur-stock', icone: Boxes,
      cle: 'stock_bas', aide: 'sous le seuil' },
    { libelle: 'Ajouter un produit', route: 'vendeur-nouveau', icone: Package,
      aide: 'nouveau au catalogue' },
  ],
  GESTIONNAIRE: [
    { libelle: 'Commandes a preparer', route: 'vendeur-commandes', icone: ClipboardList,
      cle: 'a_preparer', aide: 'en attente' },
    { libelle: 'Corriger le stock', route: 'vendeur-stock', icone: Boxes,
      cle: 'stock_bas', aide: 'sous le seuil' },
  ],
  GESTIONNAIRE_ENTREPOT: [
    { libelle: 'Receptionner les colis', route: 'entrepot-colis', icone: Warehouse,
      cle: 'colis_recus', aide: 'colis arrives' },
    { libelle: 'Monter les tournees', route: 'entrepot-tournees', icone: Route,
      cle: 'tournees_a_preparer', aide: 'a preparer' },
  ],
  LIVREUR: [
    { libelle: 'Mes courses et mes gains', route: 'livreur-courses', icone: Bike,
      cle: 'en_cours', aide: 'en cours' },
  ],
  ADMIN: [
    { libelle: 'Valider les comptes', route: 'admin-validations', icone: ShieldCheck,
      cle: 'a_valider', aide: 'dossiers en attente' },
    { libelle: 'Arbitrer les litiges', route: 'admin-litiges', icone: AlertTriangle,
      aide: 'ouverts' },
    { libelle: 'Parcourir les comptes', route: 'admin-utilisateurs', icone: Users,
      cle: 'utilisateurs', aide: 'inscrits' },
  ],
  CLIENT: [
    { libelle: 'Suivre mes commandes', route: 'mes-commandes', icone: Receipt,
      cle: 'en_cours', aide: 'en cours' },
    { libelle: 'Mes adresses de livraison', route: 'mes-adresses', icone: MapPin,
      aide: 'carnet d adresses' },
    { libelle: 'Parcourir le catalogue', route: 'vitrine', icone: ShoppingBag,
      aide: 'ce qui livre chez vous' },
  ],
}
const actions = computed(() => ACTIONS[cleRole.value] ?? [])

const ONGLETS: Record<string, { cle: string; libelle: string }[]> = {
  VENDEUR: [
    { cle: 'travail', libelle: 'Ventes du jour' },
    { cle: 'stock', libelle: 'Alertes stock' },
  ],
  GESTIONNAIRE: [
    { cle: 'travail', libelle: 'A preparer' },
    { cle: 'stock', libelle: 'Alertes stock' },
  ],
}
const onglets = computed(() => ONGLETS[cleRole.value] ?? [])

const ICONES: Record<string, unknown> = {
  VENDEUR: Store,
  GESTIONNAIRE: Boxes,
  GESTIONNAIRE_ENTREPOT: Warehouse,
  ADMIN: Users,
  CLIENT: ShoppingBag,
  LIVREUR: Truck,
}
</script>

<template>
  <div class="mx-auto max-w-[1100px] animate-[apparition_0.2s_ease-out]">
    <Onglets v-if="onglets.length" v-model="onglet" :onglets="onglets" />

    <!-- Les indicateurs, dans la rangee de KPI de la maquette -->
    <div v-if="chargement" class="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
      <Squelette v-for="n in 4" :key="n" hauteur="72px" />
    </div>

    <template v-else-if="onglet === 'travail'">
      <div v-if="indicateurs.length" class="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
        <div
          v-for="indicateur in indicateurs"
          :key="indicateur.cle"
          class="kpi"
          :class="indicateur.alerte && nombre(indicateur.cle) ? 'kpi-alerte' : ''"
        >
          <div class="kpi-nombre">
            {{ indicateur.argent ? euros(nombre(indicateur.cle)) : nombre(indicateur.cle) }}
          </div>
          <div class="kpi-libelle">{{ indicateur.libelle }}</div>
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
            <span class="text-[12px] text-encre-douce">
              <template v-if="action.cle">{{ nombre(action.cle) }} </template>{{ action.aide }}
            </span>
          </span>
          <ArrowRight :size="16" class="text-encre-douce" />
        </RouterLink>
      </div>

      <!-- Le livreur travaille sur son telephone (D-40) : on le dit, et on lui
           montre quand meme ses chiffres plutot qu'un ecran vide. -->
      <section v-if="session.role === 'LIVREUR'" class="carte mt-4 p-8 text-center">
        <span
          class="mx-auto flex h-14 w-14 items-center justify-center rounded-lg"
          :style="{ background: 'var(--accent-doux)', color: 'var(--accent)' }"
        >
          <component :is="ICONES.LIVREUR" :size="24" />
        </span>
        <b class="mt-4 block text-[15px]">Accepter et confirmer se font sur le telephone</b>
        <p class="mx-auto mt-1.5 max-w-[52ch] text-[13px] text-encre-douce">
          Prendre une course, se laisser guider, confirmer une livraison : tout cela se fait
          une main sur le guidon. Cet ecran-ci sert au suivi et aux gains.
        </p>
        <RouterLink :to="{ name: 'livreur-courses' }" class="bouton-accent mt-5">
          <Bike :size="15" /> Voir mes courses et mes gains
        </RouterLink>
      </section>

      <section v-if="session.role === 'CLIENT'" class="carte mt-4">
        <h3 class="carte-titre">Mon compte</h3>
        <div class="ligne">
          <span class="flex-1 text-encre-douce">Nom</span>
          <b>{{ session.utilisateur?.prenom }} {{ session.utilisateur?.nom }}</b>
        </div>
        <div class="ligne">
          <span class="flex-1 text-encre-douce">Adresse e-mail</span>
          <b>{{ session.utilisateur?.email }}</b>
        </div>
      </section>
    </template>

    <!-- L'onglet « Alertes stock » de la maquette -->
    <template v-else-if="onglet === 'stock'">
      <p v-if="nombre('stock_bas')" class="bandeau mb-3">
        <AlertTriangle :size="15" class="mt-px shrink-0" />
        {{ nombre('stock_bas') }} produit(s) sous le seuil d alerte — pensez a
        reapprovisionner ou a corriger le stock systeme.
      </p>

      <section class="carte">
        <h3 class="carte-titre">
          <span>Produits a reapprovisionner</span>
          <RouterLink
            :to="{ name: 'vendeur-stock' }"
            class="text-[11px] font-semibold text-encre-douce hover:text-encre"
          >
            Ouvrir l ecran de stock
          </RouterLink>
        </h3>

        <div v-if="!stockBas.length" class="vide">
          <Boxes :size="30" class="text-trait" />
          <b class="vide-titre">Rien a reapprovisionner</b>
          <p class="vide-texte">Tous les produits sont au-dessus du seuil que vous avez fixe.</p>
        </div>

        <div v-for="produit in stockBas" :key="produit.id" class="ligne">
          <span class="flex-1 font-bold">{{ produit.nom }}</span>
          <span class="text-encre-douce">
            {{ produit.stock_disponible }} en stock, seuil a {{ produit.seuil_alerte }}
          </span>
          <span class="badge" :class="produit.stock_disponible ? 'badge-attente' : 'badge-erreur'">
            {{ produit.stock_disponible ? 'a reapprovisionner' : 'rupture' }}
          </span>
        </div>
      </section>
    </template>
  </div>
</template>
