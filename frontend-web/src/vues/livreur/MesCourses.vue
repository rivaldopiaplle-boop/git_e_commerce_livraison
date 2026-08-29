<script setup lang="ts">
// L'espace livreur, au web.
//
// Le livreur travaille sur son telephone (D-40) : accepter une course,
// confirmer une livraison, se laisser guider, cela se fait une main sur le
// guidon. L'ecran web n'essaie donc pas d'imiter l'application — il sert au
// **suivi** et aux **gains**, ce que D-40 lui assigne explicitement.
//
// Ce n'est pas un ecran vide en attendant le mobile : ses courses, sa tournee
// du jour et ce qu'elles lui rapportent sont de vraies donnees.
import {
  Bike, MapPin, Package, Route, Smartphone, Truck, Wallet,
} from '@lucide/vue'
import { computed, onMounted, ref } from 'vue'

import { espaces, type Livraison, type Tournee } from '../../api/espaces'
import Onglets from '../../composants/Onglets.vue'
import Squelette from '../../composants/Squelette.vue'

const enCours = ref<Livraison[]>([])
const terminees = ref<Livraison[]>([])
const tournee = ref<Tournee | null>(null)
const gains = ref({ courses_terminees: 0, total_centimes: 0, distance_km: 0 })
const mode = ref('')
const chargement = ref(true)
const onglet = ref('en-cours')

onMounted(async () => {
  try {
    const donnees = await espaces.livreur.mesCourses()
    enCours.value = donnees.en_cours
    terminees.value = donnees.terminees
    tournee.value = donnees.tournee
    gains.value = donnees.gains
    mode.value = donnees.mode
  } finally {
    chargement.value = false
  }
})

const express = computed(() => mode.value === 'EXPRESS')
const euros = (centimes: number) =>
  (centimes / 100).toLocaleString('fr-FR', { style: 'currency', currency: 'EUR' })

const BADGES: Record<string, string> = {
  A_ATTRIBUER: 'badge-neutre',
  ATTRIBUEE: 'badge-attente',
  RECUPEREE: 'badge-cours',
  EN_ROUTE: 'badge-cours',
  LIVREE: 'badge-ok',
  ECHOUEE: 'badge-erreur',
  ANNULEE: 'badge-neutre',
}

const liste = computed(() => (onglet.value === 'terminees' ? terminees.value : enCours.value))
</script>

<template>
  <div class="mx-auto max-w-[900px] animate-[apparition_0.2s_ease-out]">
    <p class="bandeau bandeau-info mb-4">
      <Smartphone :size="15" class="mt-px shrink-0" />
      <span>
        Accepter une course et confirmer une livraison se font depuis l application mobile —
        c est la que se trouvent la position et l appareil photo. Cet ecran sert au suivi
        et aux gains.
      </span>
    </p>

    <div v-if="chargement" class="grid gap-3 sm:grid-cols-3">
      <Squelette v-for="n in 3" :key="n" hauteur="72px" />
    </div>

    <template v-else>
      <div class="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <div class="kpi">
          <div class="kpi-nombre">{{ enCours.length }}</div>
          <div class="kpi-libelle">{{ express ? 'Courses en cours' : 'Arrets a faire' }}</div>
        </div>
        <div class="kpi">
          <div class="kpi-nombre">{{ gains.courses_terminees }}</div>
          <div class="kpi-libelle">Livraisons terminees</div>
        </div>
        <div class="kpi">
          <div class="kpi-nombre">{{ euros(gains.total_centimes) }}</div>
          <div class="kpi-libelle">Gains cumules</div>
        </div>
        <div class="kpi">
          <div class="kpi-nombre">{{ gains.distance_km.toFixed(1) }} km</div>
          <div class="kpi-libelle">Distance parcourue</div>
        </div>
      </div>

      <!-- La tournee du jour, pour un livreur Standard : ses arrets dans
           l'ordre, exactement comme sur son telephone. -->
      <section v-if="tournee" class="carte mt-4">
        <h3 class="carte-titre">
          <span class="flex items-center gap-2">
            <Route :size="15" /> Ma tournee — {{ tournee.entrepot }}
          </span>
          <span class="text-[11px] font-semibold text-encre-douce">
            {{ tournee.nombre_arrets }} arrets · {{ tournee.distance_totale_km ?? '—' }} km
          </span>
        </h3>
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
              {{ arret.livraison.adresse?.rue }}, {{ arret.livraison.adresse?.ville }}
            </span>
          </span>
          <span class="badge" :class="arret.statut === 'LIVRE' ? 'badge-ok' : 'badge-neutre'">
            {{ arret.libelle_statut }}
          </span>
        </div>
      </section>

      <Onglets
        v-model="onglet"
        class="mt-5"
        :onglets="[
          { cle: 'en-cours', libelle: express ? 'Mes courses' : 'A livrer',
            compteur: enCours.length },
          { cle: 'terminees', libelle: 'Historique', compteur: terminees.length },
        ]"
      />

      <div v-if="!liste.length" class="carte">
        <div class="vide">
          <component :is="express ? Bike : Truck" :size="30" class="text-trait" />
          <b class="vide-titre">
            {{ onglet === 'terminees' ? 'Aucune livraison terminee'
               : express ? 'Aucune course en cours' : 'Aucun arret a faire' }}
          </b>
          <p class="vide-texte">
            {{ express
               ? 'Vous serez notifie sur votre telephone des qu une livraison Express est disponible pres de vous.'
               : 'Votre prochaine tournee apparaitra ici des que l entrepot vous l aura affectee.' }}
          </p>
        </div>
      </div>

      <div v-else class="carte">
        <div v-for="course in liste" :key="course.id" class="ligne">
          <component
            :is="course.type_service === 'EXPRESS' ? Bike : Package"
            :size="16"
            class="shrink-0 text-encre-douce"
          />
          <span class="min-w-0 flex-1">
            <b class="block truncate">
              {{ course.client }} — {{ course.numero_commande }}
            </b>
            <span class="flex items-center gap-1 text-[11.2px] text-encre-douce">
              <MapPin :size="11" />
              {{ course.boutiques.join(', ') }} → {{ course.adresse?.code_postal }}
              {{ course.adresse?.ville }}
              <template v-if="course.nombre_tentatives > 1">
                · {{ course.nombre_tentatives }} tentatives
              </template>
            </span>
          </span>
          <span class="w-16 text-right text-encre-douce">{{ course.distance_km }} km</span>
          <span class="flex w-20 items-center justify-end gap-1 font-bold">
            <Wallet :size="12" />
            {{ euros(course.remuneration_livreur_centimes) }}
          </span>
          <span class="badge w-[96px] justify-center"
                :class="BADGES[course.statut_livraison] ?? 'badge-neutre'">
            {{ course.libelle_statut }}
          </span>
        </div>
      </div>
    </template>
  </div>
</template>
