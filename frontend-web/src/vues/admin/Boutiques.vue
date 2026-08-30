<script setup lang="ts">
// Toutes les boutiques et tous les livreurs, quel que soit leur statut.
//
// L'écran de validation ne montre que ce qui attend une décision : on ne
// savait jamais ce qu'un dossier refusé était devenu, ni combien de boutiques
// tournaient réellement.
import { Bike, Eye, Package, ShieldCheck, Store, Truck } from '@lucide/vue'
import { computed, onMounted, ref } from 'vue'

import { espaces } from '../../api/espaces'
import ActionLigne from '../../composants/ActionLigne.vue'
import Liste from '../../composants/Liste.vue'
import type { Colonne } from '../../composants/liste'
import Onglets from '../../composants/Onglets.vue'
import Volet from '../../composants/Volet.vue'

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
  [cle: string]: unknown
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
  [cle: string]: unknown
}

const boutiques = ref<Boutique[]>([])
const livreurs = ref<LivreurAdmin[]>([])
const chargement = ref(true)
const onglet = ref('boutiques')
const selection = ref<Boutique | null>(null)
const selectionLivreur = ref<LivreurAdmin | null>(null)

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

const colonnesBoutiques: Colonne<Boutique>[] = [
  { cle: 'boutique', titre: 'Boutique', champTri: 'nom_boutique' },
  { cle: 'service', titre: 'Service', largeur: 96, aligne: 'centre' },
  { cle: 'produits', titre: 'Produits', largeur: 90, aligne: 'droite', masquerSous: 'sm',
    champTri: 'produits' },
  { cle: 'commandes', titre: 'Commandes', largeur: 100, aligne: 'droite', masquerSous: 'lg',
    champTri: 'commandes' },
  { cle: 'statut', titre: 'Dossier', largeur: 100, aligne: 'centre' },
]

const colonnesLivreurs: Colonne<LivreurAdmin>[] = [
  { cle: 'livreur', titre: 'Livreur', champTri: 'nom' },
  { cle: 'mode', titre: 'Mode', largeur: 96, aligne: 'centre' },
  { cle: 'entrepot', titre: 'Entrepôt', masquerSous: 'md' },
  { cle: 'livraisons', titre: 'Livraisons', largeur: 100, aligne: 'droite', masquerSous: 'sm',
    champTri: 'livraisons' },
  { cle: 'statut', titre: 'Dossier', largeur: 100, aligne: 'centre' },
]

const enAttente = computed(
  () => boutiques.value.filter((b) => b.statut_validation === 'EN_ATTENTE').length
    + livreurs.value.filter((l) => l.statut_validation === 'EN_ATTENTE').length,
)

const lisible = (statut: string) => statut.toLowerCase().replace(/_/g, ' ')
</script>

<template>
  <div class="mx-auto max-w-[1060px] animate-[apparition_0.2s_ease-out]">
    <Onglets
      v-model="onglet"
      :onglets="[
        { cle: 'boutiques', libelle: 'Boutiques', compteur: boutiques.length },
        { cle: 'livreurs', libelle: 'Livreurs', compteur: livreurs.length },
      ]"
    />

    <p v-if="enAttente" class="bandeau mb-3">
      <ShieldCheck :size="15" class="mt-px shrink-0" />
      {{ enAttente }} dossier(s) attendent une décision.
      <RouterLink :to="{ name: 'admin-validations' }" class="ml-1 font-bold underline">
        Ouvrir les validations
      </RouterLink>
    </p>

    <Liste
      v-if="onglet === 'boutiques'"
      :colonnes="colonnesBoutiques"
      :lignes="boutiques"
      :cle-ligne="(boutique) => boutique.id"
      :chargement="chargement"
      :recherche="(b) => `${b.nom_boutique} ${b.ville} ${b.responsable} ${b.email}`"
      :active="(b) => selection?.id === b.id"
      @ligne-cliquee="(b) => (selection = selection?.id === b.id ? null : b)"
      placeholder="Nom de boutique, ville, responsable…"
    >
      <template #col-boutique="{ ligne }">
        <span class="flex min-w-0 items-center gap-3">
          <span
            class="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg"
            :style="{ background: 'var(--accent-doux)', color: 'var(--accent)' }"
          >
            <component :is="ligne.type_activite === 'EXPRESS' ? Bike : Package" :size="16" />
          </span>
          <span class="min-w-0">
            <b class="block truncate">{{ ligne.nom_boutique }}</b>
            <span class="text-[11.2px] text-encre-douce">
              {{ ligne.responsable }}<template v-if="ligne.ville"> · {{ ligne.ville }}</template>
            </span>
          </span>
        </span>
      </template>
      <template #col-service="{ ligne }">
        <span class="badge badge-neutre">{{ ligne.type_activite.toLowerCase() }}</span>
      </template>
      <template #col-produits="{ ligne }">{{ ligne.produits }}</template>
      <template #col-commandes="{ ligne }">{{ ligne.commandes }}</template>
      <template #col-statut="{ ligne }">
        <span class="badge" :class="STATUTS[ligne.statut_validation] ?? 'badge-neutre'">
          {{ lisible(ligne.statut_validation) }}
        </span>
      </template>

      <template #actions="{ ligne }">
        <ActionLigne
          titre="Consulter cette boutique"
          :icone="Eye"
          :ton="selection?.id === ligne.id ? 'accent' : 'neutre'"
          @click="selection = selection?.id === ligne.id ? null : ligne"
        />
        <ActionLigne
          titre="Traiter le dossier de validation"
          :icone="ShieldCheck"
          :desactive="ligne.statut_validation !== 'EN_ATTENTE'"
          :vers="{ name: 'admin-validations' }"
        />
      </template>

      <template #vide>
        <div class="vide">
          <Store :size="30" class="text-trait" />
          <b class="vide-titre">Aucune boutique ne correspond</b>
        </div>
      </template>
    </Liste>

    <Liste
      v-else
      :colonnes="colonnesLivreurs"
      :lignes="livreurs"
      :cle-ligne="(livreur) => livreur.id"
      :chargement="chargement"
      :recherche="(l) => `${l.nom} ${l.email} ${l.entrepot} ${l.vehicule}`"
      :active="(l) => selectionLivreur?.id === l.id"
      @ligne-cliquee="(l) => (selectionLivreur = selectionLivreur?.id === l.id ? null : l)"
      placeholder="Nom, e-mail, entrepôt…"
    >
      <template #col-livreur="{ ligne }">
        <span class="flex min-w-0 items-center gap-3">
          <span
            class="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg"
            :style="{ background: 'var(--accent-doux)', color: 'var(--accent)' }"
          >
            <component :is="ligne.mode_livraison === 'EXPRESS' ? Bike : Truck" :size="16" />
          </span>
          <span class="min-w-0">
            <b class="block truncate">{{ ligne.nom }}</b>
            <span class="text-[11.2px] text-encre-douce">
              {{ ligne.email }} · {{ ligne.vehicule }}
            </span>
          </span>
        </span>
      </template>
      <template #col-mode="{ ligne }">
        <span class="badge badge-neutre">{{ ligne.mode_livraison.toLowerCase() }}</span>
      </template>
      <template #col-entrepot="{ ligne }">
        <span class="min-w-0 truncate text-encre-douce">{{ ligne.entrepot || '—' }}</span>
      </template>
      <template #col-livraisons="{ ligne }">{{ ligne.livraisons }}</template>
      <template #col-statut="{ ligne }">
        <span class="badge" :class="STATUTS[ligne.statut_validation] ?? 'badge-neutre'">
          {{ lisible(ligne.statut_validation) }}
        </span>
      </template>

      <template #actions="{ ligne }">
        <ActionLigne
          titre="Consulter ce livreur"
          :icone="Eye"
          :ton="selectionLivreur?.id === ligne.id ? 'accent' : 'neutre'"
          @click="selectionLivreur = selectionLivreur?.id === ligne.id ? null : ligne"
        />
        <ActionLigne
          titre="Traiter le dossier de validation"
          :icone="ShieldCheck"
          :desactive="ligne.statut_validation !== 'EN_ATTENTE'"
          :vers="{ name: 'admin-validations' }"
        />
      </template>

      <template #vide>
        <div class="vide">
          <Truck :size="30" class="text-trait" />
          <b class="vide-titre">Aucun livreur inscrit</b>
        </div>
      </template>
    </Liste>

    <Volet v-if="onglet === 'boutiques' && selection" :titre="selection.nom_boutique">
      <dl class="flex flex-col gap-2 text-[12px]">
        <div>
          <dt class="text-encre-douce">Responsable</dt>
          <dd class="font-semibold">{{ selection.responsable }}</dd>
          <dd class="break-all text-encre-douce">{{ selection.email }}</dd>
        </div>
        <div class="flex justify-between gap-2">
          <dt class="text-encre-douce">Service</dt>
          <dd class="font-semibold">{{ selection.type_activite }}</dd>
        </div>
        <div class="flex justify-between gap-2">
          <dt class="text-encre-douce">Ville</dt>
          <dd class="font-semibold">{{ selection.ville || '—' }}</dd>
        </div>
        <div class="flex justify-between gap-2">
          <dt class="text-encre-douce">Produits en ligne</dt>
          <dd class="font-semibold">{{ selection.produits }}</dd>
        </div>
        <div class="flex justify-between gap-2">
          <dt class="text-encre-douce">Commandes reçues</dt>
          <dd class="font-semibold">{{ selection.commandes }}</dd>
        </div>
        <div v-if="selection.description">
          <dt class="text-encre-douce">Description</dt>
          <dd class="leading-relaxed">{{ selection.description }}</dd>
        </div>
      </dl>
    </Volet>

    <Volet v-if="onglet === 'livreurs' && selectionLivreur" :titre="selectionLivreur.nom">
      <dl class="flex flex-col gap-2 text-[12px]">
        <div>
          <dt class="text-encre-douce">Adresse e-mail</dt>
          <dd class="font-semibold break-all">{{ selectionLivreur.email }}</dd>
        </div>
        <div class="flex justify-between gap-2">
          <dt class="text-encre-douce">Mode</dt>
          <dd class="font-semibold">{{ selectionLivreur.mode_livraison }}</dd>
        </div>
        <div class="flex justify-between gap-2">
          <dt class="text-encre-douce">Véhicule</dt>
          <dd class="font-semibold">{{ selectionLivreur.vehicule }}</dd>
        </div>
        <div class="flex justify-between gap-2">
          <dt class="text-encre-douce">Entrepôt</dt>
          <dd class="font-semibold">{{ selectionLivreur.entrepot || '—' }}</dd>
        </div>
        <div class="flex justify-between gap-2">
          <dt class="text-encre-douce">Disponibilité</dt>
          <dd class="font-semibold">
            {{ lisible(selectionLivreur.statut_disponibilite) }}
          </dd>
        </div>
        <div class="flex justify-between gap-2">
          <dt class="text-encre-douce">Livraisons effectuées</dt>
          <dd class="font-semibold">{{ selectionLivreur.livraisons }}</dd>
        </div>
      </dl>
    </Volet>
  </div>
</template>
