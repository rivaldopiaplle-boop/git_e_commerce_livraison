<script setup lang="ts">
// Les litiges, dans le depliant de la maquette : l'en-tete resume, le corps
// donne la commande, l'historique et l'echange.
//
// Les litiges ouverts d'abord — c'est ce qui attend un arbitrage. Les resolus
// restent consultables : un dossier clos qui disparait, c'est une decision
// qu'on ne peut plus expliquer.
import { AlertTriangle, ChevronDown, Scale, Store, User } from '@lucide/vue'
import { computed, onMounted, ref } from 'vue'

import { espaces, type Litige } from '../../api/espaces'
import Onglets from '../../composants/Onglets.vue'
import Squelette from '../../composants/Squelette.vue'

const litiges = ref<Litige[]>([])
const chargement = ref(true)
const onglet = ref('ouverts')
const deplie = ref<number | null>(null)

onMounted(async () => {
  try {
    const donnees = await espaces.admin.litiges()
    litiges.value = donnees.litiges
    // Le premier dossier ouvert est deplie : on arrive sur cet ecran pour
    // traiter quelque chose, pas pour contempler une liste.
    deplie.value = donnees.litiges.find((dossier) => dossier.statut === 'OUVERT')?.id ?? null
  } finally {
    chargement.value = false
  }
})

const ouverts = computed(() =>
  litiges.value.filter((dossier) => ['OUVERT', 'EN_COURS'].includes(dossier.statut)),
)
const clos = computed(() =>
  litiges.value.filter((dossier) => ['RESOLU', 'REJETE'].includes(dossier.statut)),
)
const visibles = computed(() => (onglet.value === 'clos' ? clos.value : ouverts.value))

const euros = (centimes: number) =>
  (centimes / 100).toLocaleString('fr-FR', { style: 'currency', currency: 'EUR' })
const quand = (date: string | null) =>
  date ? new Date(date).toLocaleDateString('fr-FR') : '—'

const BADGES: Record<string, string> = {
  OUVERT: 'badge-erreur',
  EN_COURS: 'badge-attente',
  RESOLU: 'badge-ok',
  REJETE: 'badge-neutre',
}
</script>

<template>
  <div class="mx-auto max-w-[880px] animate-[apparition_0.2s_ease-out]">
    <Onglets
      v-model="onglet"
      :onglets="[
        { cle: 'ouverts', libelle: 'A arbitrer', compteur: ouverts.length },
        { cle: 'clos', libelle: 'Dossiers clos', compteur: clos.length },
      ]"
    />

    <div v-if="chargement" class="flex flex-col gap-2">
      <Squelette v-for="n in 3" :key="n" hauteur="64px" />
    </div>

    <div v-else-if="!visibles.length" class="carte">
      <div class="vide">
        <Scale :size="30" class="text-trait" />
        <b class="vide-titre">
          {{ onglet === 'clos' ? 'Aucun dossier clos' : 'Aucun litige a arbitrer' }}
        </b>
        <p class="vide-texte">
          Un client ouvre un litige apres livraison. Tant qu il n y en a pas, c est que
          les commandes arrivent comme prevu.
        </p>
      </div>
    </div>

    <div v-else class="flex flex-col gap-3">
      <section v-for="dossier in visibles" :key="dossier.id" class="carte">
        <button
          type="button"
          class="carte-titre w-full text-left"
          @click="deplie = deplie === dossier.id ? null : dossier.id"
        >
          <span class="flex min-w-0 items-center gap-2.5">
            <AlertTriangle
              :size="15"
              class="shrink-0"
              :class="dossier.statut === 'OUVERT' ? 'text-alerte' : 'text-encre-douce'"
            />
            <span class="min-w-0">
              <b class="block truncate">
                Litige n° {{ dossier.id }} — {{ dossier.libelle_motif }}
              </b>
              <span class="text-[11px] font-semibold text-encre-douce">
                {{ dossier.client }} · commande {{ dossier.commande }} ·
                ouvert le {{ quand(dossier.date_ouverture) }}
              </span>
            </span>
          </span>
          <span class="flex shrink-0 items-center gap-2.5">
            <span class="badge" :class="BADGES[dossier.statut] ?? 'badge-neutre'">
              {{ dossier.libelle_statut }}
            </span>
            <ChevronDown
              :size="15"
              class="text-encre-douce transition-transform duration-150"
              :class="deplie === dossier.id ? 'rotate-180' : ''"
            />
          </span>
        </button>

        <div v-if="deplie === dossier.id" class="px-4 py-4 text-[12.5px]">
          <div class="grid gap-3 sm:grid-cols-3">
            <div class="kpi">
              <div class="kpi-nombre">{{ euros(dossier.montant_commande_centimes) }}</div>
              <div class="kpi-libelle">Montant de la commande</div>
            </div>
            <div class="kpi" :class="dossier.montant_rembourse_centimes ? 'kpi-alerte' : ''">
              <div class="kpi-nombre">{{ euros(dossier.montant_rembourse_centimes) }}</div>
              <div class="kpi-libelle">Deja rembourse</div>
            </div>
            <div class="kpi">
              <div class="kpi-nombre">{{ quand(dossier.date_resolution) }}</div>
              <div class="kpi-libelle">Date de resolution</div>
            </div>
          </div>

          <dl class="mt-4 flex flex-col gap-2.5">
            <div class="flex gap-2">
              <dt class="flex w-28 shrink-0 items-center gap-1.5 font-bold text-encre-douce">
                <User :size="12" /> Client
              </dt>
              <dd>{{ dossier.client }}</dd>
            </div>
            <div class="flex gap-2">
              <dt class="flex w-28 shrink-0 items-center gap-1.5 font-bold text-encre-douce">
                <Store :size="12" /> Boutique(s)
              </dt>
              <dd>{{ dossier.boutiques.join(', ') || '—' }}</dd>
            </div>
            <div class="flex gap-2">
              <dt class="w-28 shrink-0 font-bold text-encre-douce">Ce qu il dit</dt>
              <dd class="leading-relaxed">« {{ dossier.description }} »</dd>
            </div>
            <div v-if="dossier.resolution" class="flex gap-2">
              <dt class="w-28 shrink-0 font-bold text-encre-douce">Decision</dt>
              <dd class="leading-relaxed">{{ dossier.resolution }}</dd>
            </div>
          </dl>

          <p v-if="dossier.statut === 'OUVERT'" class="bandeau mt-4">
            <AlertTriangle :size="15" class="mt-px shrink-0" />
            L arbitrage — rembourser, refuser, contacter les deux parties — arrive avec la
            tranche paiement : un remboursement suppose un paiement a rembourser.
          </p>
        </div>
      </section>
    </div>
  </div>
</template>
