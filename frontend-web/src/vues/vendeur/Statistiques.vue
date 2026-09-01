<script setup lang="ts">
// Les statistiques du vendeur — et de lui seul (D-04).
//
// **Ta remarque, L-3** : *« il n'y a pas assez de graphe statistique »*.
// Elle était juste, et pour une raison que j'avais écrite noir sur blanc dans
// ce fichier : j'avais dessiné la courbe à la main, en `<div>` de hauteur
// variable, en me justifiant par « un graphe de trente valeurs ne mérite pas
// une dépendance ». C'était faux. Ça marchait pour trente barres et pour rien
// d'autre : ni axe, ni échelle lisible, ni infobulle, ni adaptation à la
// largeur — et c'est exactement ce que ta règle d'or n°5 interdit.
//
// Trois graphiques, sur `Chart` de PrimeVue (D-83) :
//
//   1. **le chiffre d'affaires jour par jour**, avec le nombre de commandes en
//      second axe — un montant qui monte parce qu'on a vendu un article cher
//      ne veut pas dire la même chose qu'un montant qui monte parce qu'on a
//      vendu dix fois plus ;
//   2. **la part de chaque produit** dans le chiffre d'affaires ;
//   3. **la répartition des notes**, qui dit ce qu'une moyenne cache : 4/5 de
//      moyenne avec dix 5 et deux 1, ce n'est pas 4/5 partout.
import { BarChart3, Star, TrendingUp } from '@lucide/vue'
import Chart from 'primevue/chart'
import { computed, onMounted, ref } from 'vue'

import { espaces, type Statistiques } from '../../api/espaces'
import Squelette from '../../composants/Squelette.vue'
import {
  euros,
  jourCourt,
  optionsAnneau,
  optionsTemporelles,
  palette,
  serieAccent,
  serieSecondaire,
} from '../../graphiques'

const donnees = ref<Statistiques | null>(null)
const chargement = ref(true)

onMounted(async () => {
  try {
    donnees.value = await espaces.vendeur.statistiques()
  } finally {
    chargement.value = false
  }
})

// ── Le chiffre d'affaires, jour par jour ─────────────────────────────────
const courbe = computed(() => {
  const jours = donnees.value?.par_jour ?? []
  return {
    labels: jours.map((jour) => jourCourt(jour.jour)),
    datasets: [
      serieAccent('Encaissé', jours.map((jour) => jour.montant_centimes)),
      serieSecondaire('Commandes', jours.map((jour) => jour.commandes)),
    ],
  }
})

const optionsCourbe = computed(() => {
  const base = optionsTemporelles((valeur: number) => euros(valeur))
  return {
    ...base,
    plugins: {
      ...base.plugins,
      tooltip: {
        callbacks: {
          // Les deux séries ne se lisent pas dans la même unité : l'infobulle
          // doit le dire, sinon « 3 » et « 2670 » se ressemblent.
          label: (contexte: { dataset: { label?: string }; parsed: { y: number } }) =>
            contexte.dataset.label === 'Commandes'
              ? `${contexte.parsed.y} commande(s)`
              : `Encaissé : ${euros(contexte.parsed.y)}`,
        },
      },
    },
    scales: {
      ...base.scales,
      y: {
        ...base.scales.y,
        ticks: {
          ...base.scales.y.ticks,
          callback: (valeur: number | string) => euros(Number(valeur)),
        },
      },
      // Le second axe, à droite, pour le nombre de commandes.
      y2: {
        position: 'right' as const,
        beginAtZero: true,
        grid: { display: false },
        border: { display: false },
        ticks: { color: '#5b6478', font: { size: 10 }, precision: 0 },
      },
    },
  }
})

// ── La part de chaque produit ────────────────────────────────────────────
const anneauProduits = computed(() => {
  const produits = donnees.value?.meilleurs_produits ?? []
  // Au-delà de six parts un anneau ne se lit plus : la queue passe sous
  // « Autres » plutôt que d'inventer une septième teinte.
  const tete = produits.slice(0, 6)
  const reste = produits.slice(6)
  const total = reste.reduce((somme, produit) => somme + produit.montant_centimes, 0)

  return {
    labels: [...tete.map((p) => p.nom_produit_capture), ...(total ? ['Autres'] : [])],
    datasets: [{
      data: [...tete.map((p) => p.montant_centimes), ...(total ? [total] : [])],
      backgroundColor: palette(),
      borderWidth: 0,
    }],
  }
})

// ── La répartition des notes ─────────────────────────────────────────────
const NOTES = [5, 4, 3, 2, 1]
const repartitionNotes = computed(() => {
  const avis = donnees.value?.derniers_avis ?? []
  const compte = NOTES.map((note) => avis.filter((element) => element.note === note).length)
  return {
    labels: NOTES.map((note) => `${note} étoile${note > 1 ? 's' : ''}`),
    datasets: [{
      label: 'Avis',
      data: compte,
      backgroundColor: palette(),
      borderWidth: 0,
      borderRadius: 4,
    }],
  }
})

const optionsNotes = computed(() => {
  const base = optionsTemporelles((valeur: number) => `${valeur} avis`)
  return {
    ...base,
    indexAxis: 'y' as const,
    plugins: { ...base.plugins, legend: { display: false } },
  }
})

const aDesVentes = computed(() => (donnees.value?.par_jour ?? []).length > 0)
const aDesAvis = computed(() => (donnees.value?.derniers_avis ?? []).length > 0)
</script>

<template>
  <div class="mx-auto max-w-[1000px] animate-[apparition_0.2s_ease-out]">
    <div v-if="chargement" class="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
      <Squelette v-for="n in 4" :key="n" hauteur="72px" />
    </div>

    <template v-else-if="donnees">
      <div class="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <div class="kpi">
          <div class="kpi-nombre">{{ euros(donnees.revenu_centimes) }}</div>
          <div class="kpi-libelle">Encaissé, commission déduite</div>
        </div>
        <div class="kpi">
          <div class="kpi-nombre">{{ euros(donnees.commission_centimes) }}</div>
          <div class="kpi-libelle">
            Commission plateforme ({{ Math.round(donnees.taux_commission * 100) }} %)
          </div>
        </div>
        <div class="kpi">
          <div class="kpi-nombre">{{ donnees.commandes }}</div>
          <div class="kpi-libelle">Commandes honorées</div>
        </div>
        <div class="kpi">
          <div class="kpi-nombre">{{ euros(donnees.panier_moyen_centimes) }}</div>
          <div class="kpi-libelle">Panier moyen</div>
        </div>
      </div>

      <!-- Le chiffre d'affaires jour par jour, avec les commandes en second
           axe : un montant qui monte parce qu'on a vendu un article cher ne
           veut pas dire la même chose qu'un montant qui monte parce qu'on a
           vendu dix fois plus. -->
      <section class="carte mt-4">
        <h3 class="carte-titre">
          <span class="flex items-center gap-2">
            <TrendingUp :size="15" /> Les trente derniers jours
          </span>
          <span class="text-[11px] font-semibold text-encre-douce">
            {{ donnees.par_jour.length }} jour(s) d'activité
          </span>
        </h3>

        <div v-if="!aDesVentes" class="vide">
          <BarChart3 :size="30" class="text-trait" />
          <b class="vide-titre">Aucune vente sur la période</b>
          <p class="vide-texte">
            Les ventes apparaîtront ici jour par jour dès la première commande payée.
          </p>
        </div>
        <div v-else class="p-4">
          <Chart type="line" :data="courbe" :options="optionsCourbe" class="h-[240px]" />
        </div>
      </section>

      <div class="mt-4 grid gap-4 lg:grid-cols-2">
        <section class="carte">
          <h3 class="carte-titre">Ce qui fait le chiffre d'affaires</h3>
          <div v-if="!donnees.meilleurs_produits.length" class="vide">
            <b class="vide-titre">Aucune vente enregistrée</b>
          </div>
          <template v-else>
            <div class="p-4">
              <Chart
                type="doughnut"
                :data="anneauProduits"
                :options="optionsAnneau((valeur: number) => euros(valeur))"
                class="h-[200px]"
              />
            </div>
            <!-- Le classement reste : un anneau donne la proportion, il ne
                 donne pas le chiffre exact ni la quantité vendue. -->
            <div
              v-for="(produit, rang) in donnees.meilleurs_produits"
              :key="produit.nom_produit_capture"
              class="ligne"
            >
              <span
                class="flex h-6 w-6 shrink-0 items-center justify-center rounded-md text-[11px]
                       font-bold"
                :style="{ background: 'var(--accent-doux)', color: 'var(--accent)' }"
              >
                {{ rang + 1 }}
              </span>
              <b class="min-w-0 flex-1 truncate">{{ produit.nom_produit_capture }}</b>
              <span class="text-encre-douce">{{ produit.quantite }} vendu(s)</span>
              <b class="w-20 text-right">{{ euros(produit.montant_centimes) }}</b>
            </div>
          </template>
        </section>

        <section class="carte">
          <h3 class="carte-titre">
            <span class="flex items-center gap-2"><Star :size="15" /> Avis reçus</span>
            <span v-if="donnees.nombre_avis" class="text-[11px] font-semibold text-encre-douce">
              {{ donnees.note_moyenne }} / 5 sur {{ donnees.nombre_avis }} avis
            </span>
          </h3>
          <div v-if="!aDesAvis" class="vide">
            <Star :size="30" class="text-trait" />
            <b class="vide-titre">Aucun avis pour l'instant</b>
            <p class="vide-texte">
              Un client peut déposer un avis une fois sa commande livrée, et pas avant.
            </p>
          </div>
          <template v-else>
            <!-- La répartition dit ce qu'une moyenne cache : 4/5 avec dix 5 et
                 deux 1, ce n'est pas 4/5 partout. -->
            <div class="p-4">
              <Chart
                type="bar"
                :data="repartitionNotes"
                :options="optionsNotes"
                class="h-[160px]"
              />
            </div>
            <div v-for="(avis, index) in donnees.derniers_avis" :key="index" class="ligne">
              <span class="w-[52px] shrink-0 font-bold" :style="{ color: 'var(--accent)' }">
                {{ avis.note }} / 5
              </span>
              <span class="min-w-0 flex-1 truncate text-encre-douce">
                {{ avis.commentaire || 'Sans commentaire' }}
              </span>
              <span v-if="avis.statut === 'SIGNALE'" class="badge badge-attente">signalé</span>
            </div>
          </template>
        </section>
      </div>
    </template>
  </div>
</template>
