<script setup lang="ts">
// Les colis reçus à l'entrepôt.
//
// Deux reproches du bloc K-1, tous deux justes :
//
//   « on ne peut même pas consulter les colis » — c'était une liste morte, sans
//   aucun bouton. On voyait des numéros de commande sans jamais savoir ce qu'il
//   y avait dedans ni où ça allait.
//
//   « gérer, je ne pense pas que ce soit une bonne idée » — d'accord, et c'est
//   la bonne intuition : un magasinier ne modifie pas une commande, il la
//   **réceptionne**. Les actions sont donc **consulter** (le détail dans le
//   volet) et **localiser** (la destination), pas « modifier ».
import { Eye, MapPin, Package, Warehouse } from '@lucide/vue'
import { computed, onMounted, ref } from 'vue'

import { espaces, type Colis } from '../../api/espaces'
import ActionLigne from '../../composants/ActionLigne.vue'
import Liste from '../../composants/Liste.vue'
import type { Colonne } from '../../composants/liste'
import Onglets from '../../composants/Onglets.vue'
import Volet from '../../composants/Volet.vue'

type LigneColis = {
  id: number
  numero_commande: string
  destination: string
  articles: number
  date_expedition: string | null
  vendeur: string
  ville: string
  [cle: string]: unknown
}

const donnees = ref<Colis | null>(null)
const chargement = ref(true)
const onglet = ref('tout')
const selection = ref<LigneColis | null>(null)

onMounted(async () => {
  try {
    donnees.value = await espaces.entrepot.colis()
  } finally {
    chargement.value = false
  }
})

/** Les colis à plat : c'est ce qu'une liste triable demande. Le regroupement
 *  par boutique reste accessible par l'onglet et par la colonne. */
const tousLesColis = computed<LigneColis[]>(() =>
  (donnees.value?.groupes ?? []).flatMap((groupe) =>
    groupe.colis.map((colis) => ({
      ...colis,
      vendeur: groupe.vendeur,
      ville: groupe.ville,
    })),
  ),
)

const boutiques = computed(() => (donnees.value?.groupes ?? []).map((g) => g.vendeur))

const visibles = computed(() =>
  onglet.value === 'tout'
    ? tousLesColis.value
    : tousLesColis.value.filter((colis) => colis.vendeur === onglet.value),
)

const colonnes: Colonne<LigneColis>[] = [
  { cle: 'numero', titre: 'Commande', largeur: 170 },
  { cle: 'vendeur', titre: 'Boutique déposante' },
  { cle: 'destination', titre: 'Destination', masquerSous: 'md' },
  { cle: 'articles', titre: 'Articles', largeur: 80, aligne: 'droite',
    tri: (a, b) => a.articles - b.articles },
  { cle: 'recu', titre: 'Reçu le', largeur: 120, aligne: 'droite', masquerSous: 'lg',
    tri: (a, b) => (a.date_expedition ?? '').localeCompare(b.date_expedition ?? '') },
]

const quand = (date: string | null) =>
  date
    ? new Date(date).toLocaleString('fr-FR', {
        day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit',
      })
    : '—'
</script>

<template>
  <div class="mx-auto max-w-[1000px] animate-[apparition_0.2s_ease-out]">
    <p class="bandeau bandeau-info mb-4">
      <Warehouse :size="15" class="mt-px shrink-0" />
      <span>
        <b>{{ donnees?.entrepot?.nom ?? 'Entrepôt' }}</b> — {{ donnees?.total ?? 0 }} colis reçu(s)
        de {{ boutiques.length }} boutique(s). Un entrepôt regroupe plusieurs vendeurs
        Standard : c'est ce qui rend une tournée possible.
      </span>
    </p>

    <Onglets
      v-if="boutiques.length > 1"
      v-model="onglet"
      :onglets="[
        { cle: 'tout', libelle: 'Tous les colis', compteur: tousLesColis.length },
        ...(donnees?.groupes ?? []).map((groupe) => ({
          cle: groupe.vendeur,
          libelle: groupe.vendeur,
          compteur: groupe.colis.length,
        })),
      ]"
    />

    <Liste
      :colonnes="colonnes"
      :lignes="visibles"
      :cle-ligne="(colis) => colis.id"
      :chargement="chargement"
      :recherche="(colis) => `${colis.numero_commande} ${colis.vendeur} ${colis.destination}`"
      placeholder="Numéro de commande, boutique, ville…"
    >
      <template #col-numero="{ ligne }">
        <b class="truncate">{{ ligne.numero_commande }}</b>
      </template>
      <template #col-vendeur="{ ligne }">
        <span class="min-w-0 truncate">
          {{ ligne.vendeur }}
          <span v-if="ligne.ville" class="text-encre-douce">· {{ ligne.ville }}</span>
        </span>
      </template>
      <template #col-destination="{ ligne }">
        <span class="flex min-w-0 items-center gap-1 truncate text-encre-douce">
          <MapPin :size="11" class="shrink-0" /> {{ ligne.destination }}
        </span>
      </template>
      <template #col-articles="{ ligne }">
        <span class="font-bold">{{ ligne.articles }}</span>
      </template>
      <template #col-recu="{ ligne }">
        <span class="text-encre-douce">{{ quand(ligne.date_expedition) }}</span>
      </template>

      <template #actions="{ ligne }">
        <ActionLigne
          titre="Consulter ce colis"
          :icone="Eye"
          :ton="selection?.id === ligne.id ? 'accent' : 'neutre'"
          @click="selection = selection?.id === ligne.id ? null : ligne"
        />
      </template>

      <template #vide>
        <div class="vide">
          <Package :size="30" class="text-trait" />
          <b class="vide-titre">Rien à réceptionner</b>
          <p class="vide-texte">
            Aucun vendeur n'a expédié de colis vers cet entrepôt. Les dépôts apparaîtront ici
            dès qu'une boutique marquera une commande expédiée.
          </p>
        </div>
      </template>
    </Liste>

    <!-- Le détail dans le volet : on consulte sans quitter la liste. -->
    <Volet v-if="selection" :titre="`Colis ${selection.numero_commande}`">
      <dl class="flex flex-col gap-2.5 text-[12px]">
        <div>
          <dt class="font-bold text-encre-douce">Boutique déposante</dt>
          <dd>{{ selection.vendeur }}<template v-if="selection.ville"> · {{ selection.ville }}</template></dd>
        </div>
        <div>
          <dt class="font-bold text-encre-douce">Destination</dt>
          <dd>{{ selection.destination }}</dd>
        </div>
        <div>
          <dt class="font-bold text-encre-douce">Contenu</dt>
          <dd>{{ selection.articles }} article(s)</dd>
        </div>
        <div>
          <dt class="font-bold text-encre-douce">Reçu le</dt>
          <dd>{{ quand(selection.date_expedition) }}</dd>
        </div>
      </dl>

      <p class="bandeau mt-4 !text-[11.5px]">
        Un magasinier réceptionne et charge : il ne modifie ni la commande, ni son contenu,
        ni son prix. Le rattachement à une tournée se fait depuis l'écran des tournées.
      </p>
    </Volet>
  </div>
</template>
