<script setup lang="ts">
// Les statistiques du vendeur — et de lui seul (D-04).
//
// Trois choses, pas trente : ce que la boutique a encaisse, ce qui se vend, et
// ce qu'on pense d'elle. La commission de la plateforme est affichee a cote du
// revenu plutot que retranchee en silence : chaque role doit voir l'argent qui
// le concerne, y compris ce qu'il ne touche pas (D-29).
import { BarChart3, Star, TrendingUp } from '@lucide/vue'
import { computed, onMounted, ref } from 'vue'

import { espaces, type Statistiques } from '../../api/espaces'
import Squelette from '../../composants/Squelette.vue'

const donnees = ref<Statistiques | null>(null)
const chargement = ref(true)

onMounted(async () => {
  try {
    donnees.value = await espaces.vendeur.statistiques()
  } finally {
    chargement.value = false
  }
})

const euros = (centimes: number) =>
  (centimes / 100).toLocaleString('fr-FR', { style: 'currency', currency: 'EUR' })

/** L'echelle de la courbe : le plus haut jour vaut 100 % de la hauteur. */
const maximum = computed(() =>
  Math.max(1, ...(donnees.value?.par_jour ?? []).map((jour) => jour.montant_centimes)),
)
const jourCourt = (jour: string) =>
  new Date(jour).toLocaleDateString('fr-FR', { day: '2-digit', month: '2-digit' })
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
          <div class="kpi-libelle">Encaisse, commission deduite</div>
        </div>
        <div class="kpi">
          <div class="kpi-nombre">{{ euros(donnees.commission_centimes) }}</div>
          <div class="kpi-libelle">
            Commission plateforme ({{ Math.round(donnees.taux_commission * 100) }} %)
          </div>
        </div>
        <div class="kpi">
          <div class="kpi-nombre">{{ donnees.commandes }}</div>
          <div class="kpi-libelle">Commandes honorees</div>
        </div>
        <div class="kpi">
          <div class="kpi-nombre">{{ euros(donnees.panier_moyen_centimes) }}</div>
          <div class="kpi-libelle">Panier moyen</div>
        </div>
      </div>

      <!-- La courbe, en barres : trente jours, une barre par jour ou il s'est
           passe quelque chose. Sans bibliotheque — un graphe de trente valeurs
           ne justifie pas deux cents kilo-octets de dependance. -->
      <section class="carte mt-4">
        <h3 class="carte-titre">
          <span class="flex items-center gap-2">
            <TrendingUp :size="15" /> Les trente derniers jours
          </span>
          <span class="text-[11px] font-semibold text-encre-douce">
            {{ donnees.par_jour.length }} jour(s) d activite
          </span>
        </h3>

        <div v-if="!donnees.par_jour.length" class="vide">
          <BarChart3 :size="30" class="text-trait" />
          <b class="vide-titre">Aucune vente sur la periode</b>
          <p class="vide-texte">
            Les ventes apparaitront ici jour par jour des la premiere commande payee.
          </p>
        </div>

        <div v-else class="flex items-end gap-1.5 overflow-x-auto px-4 py-5" style="height: 190px">
          <div
            v-for="jour in donnees.par_jour"
            :key="jour.jour"
            class="flex min-w-[26px] flex-1 flex-col items-center justify-end gap-1.5"
            :title="`${jourCourt(jour.jour)} — ${euros(jour.montant_centimes)} · ${jour.commandes} commande(s)`"
          >
            <span class="text-[10px] font-bold text-encre-douce">
              {{ Math.round(jour.montant_centimes / 100) }}
            </span>
            <span
              class="w-full rounded-t-[4px] transition-all duration-200"
              :style="{
                height: `${Math.max(4, (jour.montant_centimes / maximum) * 110)}px`,
                background: 'var(--accent)',
              }"
            />
            <span class="text-[9.5px] whitespace-nowrap text-encre-douce">
              {{ jourCourt(jour.jour) }}
            </span>
          </div>
        </div>
      </section>

      <div class="mt-4 grid gap-4 lg:grid-cols-2">
        <section class="carte">
          <h3 class="carte-titre">Ce qui se vend le mieux</h3>
          <div v-if="!donnees.meilleurs_produits.length" class="vide">
            <b class="vide-titre">Aucune vente enregistree</b>
          </div>
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
        </section>

        <section class="carte">
          <h3 class="carte-titre">
            <span class="flex items-center gap-2"><Star :size="15" /> Avis recus</span>
            <span v-if="donnees.nombre_avis" class="text-[11px] font-semibold text-encre-douce">
              {{ donnees.note_moyenne }} / 5 sur {{ donnees.nombre_avis }} avis
            </span>
          </h3>
          <div v-if="!donnees.derniers_avis.length" class="vide">
            <Star :size="30" class="text-trait" />
            <b class="vide-titre">Aucun avis pour l instant</b>
            <p class="vide-texte">
              Un client peut deposer un avis une fois sa commande livree, et pas avant.
            </p>
          </div>
          <div v-for="(avis, index) in donnees.derniers_avis" :key="index" class="ligne">
            <span class="w-[52px] shrink-0 font-bold" :style="{ color: 'var(--accent)' }">
              {{ avis.note }} / 5
            </span>
            <span class="min-w-0 flex-1 truncate text-encre-douce">
              {{ avis.commentaire || 'Sans commentaire' }}
            </span>
            <span v-if="avis.statut === 'SIGNALE'" class="badge badge-attente">signale</span>
          </div>
        </section>
      </div>
    </template>
  </div>
</template>
