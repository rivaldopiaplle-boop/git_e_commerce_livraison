<script setup lang="ts">
// Les tournées de l'entrepôt.
//
// « Tu dis qu'il y a des tournées mais je ne sais pas où regarder » (K-2). Le
// reproche portait : elles n'étaient visibles que dans un dépliant qu'il
// fallait deviner. Elles sont maintenant une liste avec ses boutons-symboles,
// et le détail — les arrêts, dans leur ordre — part dans le volet de droite.
//
// Une tournée dont les arrêts ne sont pas ordonnés n'est pas une tournée,
// c'est une liste (D-44) : l'ordre est donc la première chose affichée.
import { MapPin, Eye, Route, Truck, User } from '@lucide/vue'
import { computed, onMounted, ref } from 'vue'

import { espaces, type Tournee } from '../../api/espaces'
import ActionLigne from '../../composants/ActionLigne.vue'
import Liste from '../../composants/Liste.vue'
import type { Colonne } from '../../composants/liste'
import Onglets from '../../composants/Onglets.vue'
import Volet from '../../composants/Volet.vue'

type LigneTournee = Tournee & { [cle: string]: unknown }

const tournees = ref<LigneTournee[]>([])
const enAttente = ref(0)
const chargement = ref(true)
const onglet = ref('a-preparer')
const selection = ref<LigneTournee | null>(null)

onMounted(async () => {
  try {
    const donnees = await espaces.entrepot.tournees()
    tournees.value = donnees.tournees as LigneTournee[]
    enAttente.value = donnees.en_attente
    // On arrive ici pour préparer quelque chose : la première tournée à
    // préparer s'ouvre d'elle-même dans le volet.
    selection.value =
      tournees.value.find((t) => ['BROUILLON', 'PRETE'].includes(t.statut)) ?? null
  } finally {
    chargement.value = false
  }
})

const aPreparer = computed(() =>
  tournees.value.filter((t) => ['BROUILLON', 'PRETE'].includes(t.statut)),
)
const enCours = computed(() => tournees.value.filter((t) => t.statut === 'EN_COURS'))
const terminees = computed(() => tournees.value.filter((t) => t.statut === 'TERMINEE'))

const visibles = computed(() =>
  onglet.value === 'en-cours' ? enCours.value
    : onglet.value === 'terminees' ? terminees.value
      : aPreparer.value,
)

const colonnes: Colonne<LigneTournee>[] = [
  { cle: 'numero', titre: 'Tournée', largeur: 120 },
  { cle: 'zone', titre: 'Zone' },
  { cle: 'livreur', titre: 'Livreur', masquerSous: 'md' },
  { cle: 'arrets', titre: 'Arrêts', largeur: 74, aligne: 'droite',
    tri: (a, b) => a.nombre_arrets - b.nombre_arrets },
  { cle: 'distance', titre: 'Distance', largeur: 90, aligne: 'droite', masquerSous: 'lg' },
  { cle: 'statut', titre: 'État', largeur: 104, aligne: 'centre' },
]

const BADGES: Record<string, string> = {
  BROUILLON: 'badge-neutre',
  PRETE: 'badge-attente',
  AFFECTEE: 'badge-cours',
  EN_COURS: 'badge-cours',
  TERMINEE: 'badge-ok',
}
const BADGES_ARRET: Record<string, string> = {
  A_FAIRE: 'badge-neutre',
  LIVRE: 'badge-ok',
  ECHOUE: 'badge-erreur',
  REPORTE: 'badge-attente',
}
</script>

<template>
  <div class="mx-auto max-w-[1000px] animate-[apparition_0.2s_ease-out]">
    <Onglets
      v-model="onglet"
      :onglets="[
        { cle: 'a-preparer', libelle: 'À préparer', compteur: aPreparer.length },
        { cle: 'en-cours', libelle: 'En cours', compteur: enCours.length },
        { cle: 'terminees', libelle: 'Terminées', compteur: terminees.length },
      ]"
    />

    <p v-if="enAttente" class="bandeau mb-4">
      <Route :size="15" class="mt-px shrink-0" />
      {{ enAttente }} livraison(s) Standard attendent d'être rattachées à une tournée.
    </p>

    <Liste
      :colonnes="colonnes"
      :lignes="visibles"
      :cle-ligne="(tournee) => tournee.id"
      :chargement="chargement"
      :recherche="(t) => `tournée ${t.id} ${t.zone ?? ''} ${t.livreur?.nom ?? ''}`"
      placeholder="Numéro, zone, livreur…"
    >
      <template #col-numero="{ ligne }">
        <b class="flex items-center gap-2"><Truck :size="14" /> n° {{ ligne.id }}</b>
      </template>
      <template #col-zone="{ ligne }">
        <span class="min-w-0 truncate">{{ ligne.zone ?? 'zone non définie' }}</span>
      </template>
      <template #col-livreur="{ ligne }">
        <span v-if="ligne.livreur" class="flex min-w-0 items-center gap-1.5 truncate">
          <User :size="12" class="shrink-0 text-encre-douce" /> {{ ligne.livreur.nom }}
        </span>
        <span v-else class="badge badge-attente">à affecter</span>
      </template>
      <template #col-arrets="{ ligne }">
        <span class="font-bold">{{ ligne.nombre_arrets }}</span>
      </template>
      <template #col-distance="{ ligne }">
        <span class="text-encre-douce">{{ ligne.distance_totale_km ?? '—' }} km</span>
      </template>
      <template #col-statut="{ ligne }">
        <span class="badge" :class="BADGES[ligne.statut] ?? 'badge-neutre'">
          {{ ligne.libelle_statut }}
        </span>
      </template>

      <template #actions="{ ligne }">
        <ActionLigne
          titre="Consulter les arrêts de cette tournée"
          :icone="Eye"
          :ton="selection?.id === ligne.id ? 'accent' : 'neutre'"
          @click="selection = selection?.id === ligne.id ? null : ligne"
        />
      </template>

      <template #vide>
        <div class="vide">
          <Route :size="30" class="text-trait" />
          <b class="vide-titre">
            {{
              onglet === 'en-cours' ? 'Aucune tournée sur la route'
              : onglet === 'terminees' ? 'Aucune tournée terminée'
              : 'Aucune tournée à préparer'
            }}
          </b>
          <p class="vide-texte">
            Une tournée se monte à partir des colis reçus, puis s'affecte à un livreur
            rattaché à cet entrepôt.
          </p>
        </div>
      </template>
    </Liste>

    <!-- Les arrêts, dans leur ordre : c'est la tournée elle-même. -->
    <Volet v-if="selection" :titre="`Tournée n° ${selection.id}`">
      <dl class="mb-3 flex flex-col gap-2 text-[12px]">
        <div class="flex justify-between gap-2">
          <dt class="text-encre-douce">Entrepôt</dt>
          <dd class="font-semibold">{{ selection.entrepot }}</dd>
        </div>
        <div class="flex justify-between gap-2">
          <dt class="text-encre-douce">Zone</dt>
          <dd class="font-semibold">{{ selection.zone ?? '—' }}</dd>
        </div>
        <div class="flex justify-between gap-2">
          <dt class="text-encre-douce">Livreur</dt>
          <dd class="font-semibold">{{ selection.livreur?.nom ?? 'à affecter' }}</dd>
        </div>
        <div class="flex justify-between gap-2">
          <dt class="text-encre-douce">Distance</dt>
          <dd class="font-semibold">{{ selection.distance_totale_km ?? '—' }} km</dd>
        </div>
      </dl>

      <b class="text-[11px] font-bold tracking-wider text-encre-douce uppercase">
        {{ selection.arrets.length }} arrêt(s), dans l'ordre
      </b>

      <div v-if="!selection.arrets.length" class="vide !py-6">
        <b class="vide-titre">Aucun arrêt</b>
        <p class="vide-texte">Cette tournée est encore à l'état de brouillon.</p>
      </div>

      <ol v-else class="mt-2 flex flex-col gap-2">
        <li
          v-for="arret in selection.arrets"
          :key="arret.id"
          class="flex gap-2.5 rounded-lg border border-trait bg-papier p-2.5 text-[12px]"
        >
          <span
            class="flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-[11px]
                   font-extrabold text-white"
            :style="{ background: 'var(--accent)' }"
          >
            {{ arret.ordre }}
          </span>
          <span class="min-w-0 flex-1">
            <b class="block truncate">{{ arret.livraison.client }}</b>
            <span class="flex items-center gap-1 text-[11px] text-encre-douce">
              <MapPin :size="10" class="shrink-0" />
              {{ arret.livraison.adresse?.rue }}, {{ arret.livraison.adresse?.ville }}
            </span>
            <span class="mt-1 block">
              <span class="badge" :class="BADGES_ARRET[arret.statut] ?? 'badge-neutre'">
                {{ arret.libelle_statut }}
              </span>
            </span>
          </span>
        </li>
      </ol>
    </Volet>
  </div>
</template>
