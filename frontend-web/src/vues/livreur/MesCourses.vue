<script setup lang="ts">
// L'espace livreur, au web.
//
// Le livreur travaille sur son téléphone (D-40) : accepter une course et
// confirmer une livraison se font une main sur le guidon. L'écran web sert au
// **suivi** et aux **gains**, ce que D-40 lui assigne explicitement — et il
// s'appuie sur les mêmes listes que le reste du projet.
import { Bike, Eye, MapPin, Package, Route, Smartphone, Truck, Wallet } from '@lucide/vue'
import { computed, onMounted, ref } from 'vue'

import { espaces, type Livraison, type Tournee } from '../../api/espaces'
import ActionLigne from '../../composants/ActionLigne.vue'
import Liste from '../../composants/Liste.vue'
import type { Colonne } from '../../composants/liste'
import Onglets from '../../composants/Onglets.vue'
import FicheContextuelle from '../../composants/FicheContextuelle.vue'

type Ligne = Livraison & { [cle: string]: unknown }

const enCours = ref<Ligne[]>([])
const terminees = ref<Ligne[]>([])
const tournee = ref<Tournee | null>(null)
const gains = ref({ courses_terminees: 0, total_centimes: 0, distance_km: 0 })
const mode = ref('')
const chargement = ref(true)
const onglet = ref('en-cours')
const selection = ref<Ligne | null>(null)
// L'oeil ouvre une popup par-dessus la liste (M-1) : le panneau de droite,
// lui, reste le contexte permanent de la ligne active.
const apercu = ref(false)

onMounted(async () => {
  try {
    const donnees = await espaces.livreur.mesCourses()
    enCours.value = donnees.en_cours as Ligne[]
    terminees.value = donnees.terminees as Ligne[]
    tournee.value = donnees.tournee
    gains.value = donnees.gains
    mode.value = donnees.mode
    selection.value = enCours.value[0] ?? null
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

/**
 * L'oeil : on consulte, on ne selectionne pas seulement.
 *
 * Il ouvre la popup ET marque la ligne active, pour que le panneau de
 * droite montre la meme chose une fois la popup refermee.
 */
function consulter(ligne: Ligne) {
  selection.value = ligne
  apercu.value = true
}

const colonnes: Colonne<Ligne>[] = [
  { cle: 'course', titre: 'Course' },
  { cle: 'trajet', titre: 'Trajet', masquerSous: 'md' },
  { cle: 'distance', titre: 'Distance', largeur: 90, aligne: 'droite', masquerSous: 'sm',
    champTri: 'distance_km' },
  { cle: 'gain', titre: 'Rapporte', largeur: 100, aligne: 'droite',
    champTri: 'remuneration_livreur_centimes' },
  { cle: 'statut', titre: 'État', largeur: 110, aligne: 'centre' },
]
</script>

<template>
  <div class="mx-auto max-w-[1020px] animate-[apparition_0.2s_ease-out]">
    <p class="bandeau bandeau-info mb-4">
      <Smartphone :size="15" class="mt-px shrink-0" />
      <span>
        Accepter une course et confirmer une livraison se font depuis l'application mobile —
        c'est là que se trouvent la position et l'appareil photo. Cet écran sert au suivi et
        aux gains.
      </span>
    </p>

    <div class="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
      <div class="kpi">
        <div class="kpi-nombre">{{ enCours.length }}</div>
        <div class="kpi-libelle">{{ express ? 'Courses en cours' : 'Arrêts à faire' }}</div>
      </div>
      <div class="kpi">
        <div class="kpi-nombre">{{ gains.courses_terminees }}</div>
        <div class="kpi-libelle">Livraisons terminées</div>
      </div>
      <div class="kpi">
        <div class="kpi-nombre">{{ euros(gains.total_centimes) }}</div>
        <div class="kpi-libelle">Gains cumulés</div>
      </div>
      <div class="kpi">
        <div class="kpi-nombre">{{ gains.distance_km.toFixed(1) }} km</div>
        <div class="kpi-libelle">Distance parcourue</div>
      </div>
    </div>

    <Onglets
      v-model="onglet"
      class="mt-5"
      :onglets="[
        { cle: 'en-cours', libelle: express ? 'Mes courses' : 'À livrer',
          compteur: enCours.length },
        { cle: 'terminees', libelle: 'Historique', compteur: terminees.length },
      ]"
    />

    <Liste
      :colonnes="colonnes"
      :lignes="liste"
      :cle-ligne="(course) => course.id"
      :chargement="chargement"
      :recherche="(c) => `${c.numero_commande} ${c.client} ${c.adresse?.ville ?? ''}`"
      :active="(c) => selection?.id === c.id"
      @ligne-cliquee="(c) => (selection = selection?.id === c.id ? null : c)"
      placeholder="Commande, client, ville…"
    >
      <template #col-course="{ ligne }">
        <span class="flex min-w-0 items-center gap-2">
          <component
            :is="ligne.type_service === 'EXPRESS' ? Bike : Package"
            :size="14"
            class="shrink-0 text-encre-douce"
          />
          <span class="min-w-0">
            <b class="block truncate">{{ ligne.client }}</b>
            <span class="text-[11.2px] text-encre-douce">{{ ligne.numero_commande }}</span>
          </span>
        </span>
      </template>
      <template #col-trajet="{ ligne }">
        <span class="flex min-w-0 items-center gap-1 truncate text-encre-douce">
          <MapPin :size="11" class="shrink-0" />
          {{ ligne.boutiques.join(', ') }} → {{ ligne.adresse?.ville }}
        </span>
      </template>
      <template #col-distance="{ ligne }">
        <span class="text-encre-douce">{{ ligne.distance_km }} km</span>
      </template>
      <template #col-gain="{ ligne }">
        <b>{{ euros(ligne.remuneration_livreur_centimes) }}</b>
      </template>
      <template #col-statut="{ ligne }">
        <span class="badge" :class="BADGES[ligne.statut_livraison] ?? 'badge-neutre'">
          {{ ligne.libelle_statut }}
        </span>
      </template>

      <template #actions="{ ligne }">
        <ActionLigne
          titre="Consulter cette course"
          :icone="Eye"
          :ton="selection?.id === ligne.id ? 'accent' : 'neutre'"
          @click="consulter(ligne)"
        />
      </template>

      <template #vide>
        <div class="vide">
          <component :is="express ? Bike : Truck" :size="30" class="text-trait" />
          <b class="vide-titre">
            {{ onglet === 'terminees' ? 'Aucune livraison terminée'
               : express ? 'Aucune course en cours' : 'Aucun arrêt à faire' }}
          </b>
          <p class="vide-texte">
            {{ express
               ? "Vous serez notifié sur votre téléphone dès qu'une livraison Express est disponible près de vous."
               : "Votre prochaine tournée apparaîtra ici dès que l'entrepôt vous l'aura affectée." }}
          </p>
        </div>
      </template>
    </Liste>

    <!-- La tournée du jour, pour un livreur Standard -->
    <section v-if="tournee" class="carte mt-4">
      <h3 class="carte-titre">
        <span class="flex items-center gap-2">
          <Route :size="15" /> Ma tournée — {{ tournee.entrepot }}
        </span>
        <span class="text-[11px] font-semibold text-encre-douce">
          {{ tournee.nombre_arrets }} arrêts · {{ tournee.distance_totale_km ?? '—' }} km
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

    <FicheContextuelle
      v-if="selection"
      :titre="selection.client"
      :apercu-ouvert="apercu"
      @fermer-apercu="apercu = false"
    >
      <dl class="flex flex-col gap-2 text-[12px]">
        <div class="flex justify-between gap-2">
          <dt class="text-encre-douce">Commande</dt>
          <dd class="font-semibold">{{ selection.numero_commande }}</dd>
        </div>
        <div>
          <dt class="text-encre-douce">À récupérer chez</dt>
          <dd class="font-semibold">{{ selection.boutiques.join(', ') }}</dd>
        </div>
        <div>
          <dt class="text-encre-douce">À livrer</dt>
          <dd class="font-semibold">
            {{ selection.adresse?.rue }}<br />
            {{ selection.adresse?.code_postal }} {{ selection.adresse?.ville }}
          </dd>
          <dd v-if="selection.adresse?.instructions" class="mt-1 text-encre-douce">
            « {{ selection.adresse.instructions }} »
          </dd>
        </div>
        <div class="flex justify-between gap-2">
          <dt class="text-encre-douce">Distance</dt>
          <dd class="font-semibold">{{ selection.distance_km }} km</dd>
        </div>
        <div class="flex justify-between gap-2">
          <dt class="flex items-center gap-1 text-encre-douce"><Wallet :size="12" /> Rapporte</dt>
          <dd class="font-semibold">{{ euros(selection.remuneration_livreur_centimes) }}</dd>
        </div>
        <div v-if="selection.code_confirmation" class="flex justify-between gap-2">
          <dt class="text-encre-douce">Code de remise</dt>
          <dd class="font-mono font-bold">{{ selection.code_confirmation }}</dd>
        </div>
        <div v-if="selection.nombre_tentatives > 1" class="flex justify-between gap-2">
          <dt class="text-encre-douce">Tentatives</dt>
          <dd class="font-semibold">{{ selection.nombre_tentatives }}</dd>
        </div>
      </dl>

      <p class="bandeau mt-4 !text-[11.5px]">
        Confirmer la remise se fait sur le téléphone : c'est là que le code du client se
        saisit, et là que la position prouve que vous y étiez.
      </p>
    </FicheContextuelle>
  </div>
</template>
