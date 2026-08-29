<script setup lang="ts">
// Les tournees de l'entrepot.
//
// Une tournee dont les arrets ne sont pas ordonnes n'est pas une tournee,
// c'est une liste (D-44). L'ordre est donc la premiere colonne de chaque
// arret, et l'ecran l'affiche meme quand la tournee n'est qu'un brouillon.
import { ChevronDown, MapPin, Route, Truck, User } from '@lucide/vue'
import { computed, onMounted, ref } from 'vue'

import { espaces, type Tournee } from '../../api/espaces'
import Onglets from '../../composants/Onglets.vue'
import Squelette from '../../composants/Squelette.vue'

const tournees = ref<Tournee[]>([])
const enAttente = ref(0)
const chargement = ref(true)
const onglet = ref('a-preparer')
const deplie = ref<number | null>(null)

onMounted(async () => {
  try {
    const donnees = await espaces.entrepot.tournees()
    tournees.value = donnees.tournees
    enAttente.value = donnees.en_attente
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
  <div class="mx-auto max-w-[920px] animate-[apparition_0.2s_ease-out]">
    <Onglets
      v-model="onglet"
      :onglets="[
        { cle: 'a-preparer', libelle: 'A preparer', compteur: aPreparer.length },
        { cle: 'en-cours', libelle: 'En cours', compteur: enCours.length },
        { cle: 'terminees', libelle: 'Terminees', compteur: terminees.length },
      ]"
    />

    <p v-if="enAttente" class="bandeau mb-4">
      <Route :size="15" class="mt-px shrink-0" />
      {{ enAttente }} livraison(s) Standard attendent d etre rattachees a une tournee.
    </p>

    <div v-if="chargement" class="flex flex-col gap-2">
      <Squelette v-for="n in 3" :key="n" hauteur="70px" />
    </div>

    <div v-else-if="!visibles.length" class="carte">
      <div class="vide">
        <Route :size="30" class="text-trait" />
        <b class="vide-titre">
          {{
            onglet === 'en-cours' ? 'Aucune tournee sur la route'
            : onglet === 'terminees' ? 'Aucune tournee terminee'
            : 'Aucune tournee a preparer'
          }}
        </b>
        <p class="vide-texte">
          Une tournee se monte a partir des colis recus, puis s affecte a un livreur
          rattache a cet entrepot.
        </p>
      </div>
    </div>

    <div v-else class="flex flex-col gap-3">
      <section v-for="tournee in visibles" :key="tournee.id" class="carte">
        <button
          type="button"
          class="carte-titre w-full text-left"
          @click="deplie = deplie === tournee.id ? null : tournee.id"
        >
          <span class="flex min-w-0 items-center gap-2.5">
            <Truck :size="15" class="shrink-0" />
            <span class="min-w-0">
              <b class="block">Tournee n° {{ tournee.id }}</b>
              <span class="text-[11px] font-semibold text-encre-douce">
                {{ tournee.zone ?? 'zone non definie' }} ·
                {{ tournee.nombre_arrets }} arrets ·
                {{ tournee.distance_totale_km ?? '—' }} km
              </span>
            </span>
          </span>
          <span class="flex shrink-0 items-center gap-2.5">
            <span v-if="tournee.livreur" class="flex items-center gap-1.5 text-[11.5px]
                                                font-semibold text-encre-douce">
              <User :size="12" /> {{ tournee.livreur.nom }}
            </span>
            <span v-else class="badge badge-attente">a affecter</span>
            <span class="badge" :class="BADGES[tournee.statut] ?? 'badge-neutre'">
              {{ tournee.libelle_statut }}
            </span>
            <ChevronDown
              :size="15"
              class="text-encre-douce transition-transform duration-150"
              :class="deplie === tournee.id ? 'rotate-180' : ''"
            />
          </span>
        </button>

        <!-- Les arrets, dans leur ordre : c'est la tournee elle-meme. -->
        <template v-if="deplie === tournee.id">
          <div v-if="!tournee.arrets.length" class="vide">
            <b class="vide-titre">Aucun arret dans cette tournee</b>
            <p class="vide-texte">Elle est encore a l etat de brouillon.</p>
          </div>
          <div v-for="arret in tournee.arrets" :key="arret.id" class="ligne">
            <span
              class="flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-[11px]
                     font-extrabold text-white"
              :style="{ background: 'var(--accent)' }"
            >
              {{ arret.ordre }}
            </span>
            <span class="min-w-0 flex-1">
              <b class="block truncate">{{ arret.livraison.client }}</b>
              <span class="flex items-center gap-1 text-[11.2px] text-encre-douce">
                <MapPin :size="11" />
                {{ arret.livraison.adresse?.rue }}, {{ arret.livraison.adresse?.code_postal }}
                {{ arret.livraison.adresse?.ville }}
              </span>
            </span>
            <span class="text-[11.5px] text-encre-douce">
              {{ arret.livraison.numero_commande }}
            </span>
            <span class="badge" :class="BADGES_ARRET[arret.statut] ?? 'badge-neutre'">
              {{ arret.libelle_statut }}
            </span>
          </div>
        </template>
      </section>
    </div>
  </div>
</template>
