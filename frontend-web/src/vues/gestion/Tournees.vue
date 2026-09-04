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
import {
  AlertTriangle, Eye, MapPin, Play, RefreshCw, Route, Truck, User, UserPlus,
} from '@lucide/vue'
import { computed, defineAsyncComponent, ref } from 'vue'

import { EchecApi } from '../../api/client'
import { espaces, type Tournee } from '../../api/espaces'
import ActionLigne from '../../composants/ActionLigne.vue'
import FicheContextuelle from '../../composants/FicheContextuelle.vue'
import Liste from '../../composants/Liste.vue'
import type { Colonne } from '../../composants/liste'
import Onglets from '../../composants/Onglets.vue'
import Popup from '../../composants/Popup.vue'
import { useNotification } from '../../notifications'
import { useRafraichissement } from '../../rafraichissement'

type LigneTournee = Tournee & { [cle: string]: unknown }

const notifier = useNotification()
const erreur = ref('')
const tournees = ref<LigneTournee[]>([])
const enAttente = ref(0)
const chargement = ref(true)
const onglet = ref('a-preparer')
const selection = ref<LigneTournee | null>(null)

/**
 * Les arrêts de la tournée choisie, prêts pour la carte.
 *
 * L'entrepôt lisait ses tournées comme une liste numérotée. Une liste dit
 * l'ordre, elle ne dit pas si l'ordre est **bon** : deux arrêts voisins
 * séparés de dix rangs ne se voient que sur une carte (N-5).
 */
/**
 * Ce que le gestionnaire FAIT — O-5, D-153.
 *
 * *« Les tournées doivent se calculer seules en fonction des commandes […] le
 * gestionnaire demande le calcul, peut le refaire quand il veut, doit attribuer
 * à un livreur juste et confirmer la réception des colis. »*
 *
 * Il ne pouvait rien faire : les tournées visibles venaient toutes du jeu de
 * démonstration, d'où ta question *« d'où sort la tournée du livreur ? »*.
 */
const occupe = ref(false)
const messageAction = ref('')
const livreurs = ref<{ id: number; nom: string; disponibilite: string
                       de_cet_entrepot: boolean; tournees_en_cours: number }[]>([])
const attribution = ref<LigneTournee | null>(null)

async function agir(action: () => Promise<unknown>, reussite: string) {
  occupe.value = true
  erreur.value = ''
  try {
    await action()
    messageAction.value = reussite
    notifier.succes(reussite)
    await charger()
  } catch (echec) {
    erreur.value = echec instanceof EchecApi ? echec.erreur.message : 'Action refusée.'
    notifier.echec(erreur.value)
  } finally {
    occupe.value = false
  }
}

const calculer = (idTournee?: number) =>
  agir(() => espaces.entrepot.calculerTournee(idTournee),
       idTournee ? 'Tournée recalculée.' : 'Tournée montée avec les colis reçus.')

async function ouvrirAttribution(tournee: LigneTournee) {
  attribution.value = tournee
  livreurs.value = await espaces.entrepot.livreursPourTournee()
}

const attribuer = (idLivreur: number) =>
  agir(async () => {
    await espaces.entrepot.attribuerTournee(attribution.value!.id, idLivreur)
    attribution.value = null
  }, 'Tournée confiée, le livreur est prévenu.')

const fairePartir = (tournee: LigneTournee) =>
  agir(() => espaces.entrepot.fairePartir(tournee.id),
       'La tournée est partie : les clients voient leur commande avancer.')

const pointsTournee = computed(() =>
  (selection.value?.arrets ?? [])
    .map((arret) => ({
      lat: Number(arret.livraison.adresse?.latitude),
      lon: Number(arret.livraison.adresse?.longitude),
      rang: arret.ordre,
      libelle: `${arret.ordre}. ${arret.livraison.client} — ${
        arret.livraison.adresse?.rue ?? ''}`,
    }))
    .filter((point) => Number.isFinite(point.lat) && Number.isFinite(point.lon)),
)
// L'oeil ouvre une popup par-dessus la liste (M-1) : le panneau de droite,
// lui, reste le contexte permanent de la ligne active.
const apercu = ref(false)

/**
 * On n'ouvre la première ligne utile qu'au premier chargement.
 *
 * Depuis que l'écran se rafraîchit en fond (O-5), rouvrir d'office à chaque
 * passage ferait sauter le volet de droite toutes les vingt secondes, sous les
 * yeux de la personne en train de lire.
 */
const premierChargement = ref(true)

/** Nommee : les actions du gestionnaire la rejouent apres avoir agi. */
async function charger() {
  try {
    const donnees = await espaces.entrepot.tournees()
    tournees.value = donnees.tournees as LigneTournee[]
    enAttente.value = donnees.en_attente
    // On arrive ici pour préparer quelque chose : la première tournée à
    // préparer s'ouvre d'elle-même dans le volet.
    if (premierChargement.value) {
      selection.value =
        tournees.value.find((t) => ['BROUILLON', 'PRETE'].includes(t.statut)) ?? null
    }
    // La tournée ouverte suit ce que les actions lui font : sans cela, le
    // volet montrerait encore « brouillon » après une attribution.
    if (selection.value) {
      selection.value = tournees.value.find((t) => t.id === selection.value!.id)
        ?? selection.value
    }
    premierChargement.value = false
  } finally {
    chargement.value = false
  }
}

useRafraichissement(charger, { periodique: true })

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

/**
 * L'oeil : on consulte, on ne selectionne pas seulement.
 *
 * Il ouvre la popup ET marque la ligne active, pour que le panneau de
 * droite montre la meme chose une fois la popup refermee.
 */
function consulter(ligne: LigneTournee) {
  selection.value = ligne
  apercu.value = true
}

const colonnes: Colonne<LigneTournee>[] = [
  { cle: 'numero', titre: 'Tournée', largeur: 120 },
  { cle: 'zone', titre: 'Zone' },
  { cle: 'livreur', titre: 'Livreur', masquerSous: 'md' },
  { cle: 'arrets', titre: 'Arrêts', largeur: 74, aligne: 'droite',
    champTri: 'nombre_arrets' },
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

// MapLibre pese pres d'un mega-octet. Charge paresseusement, il n'arrive
// qu'au moment ou une carte s'affiche vraiment : personne ne telecharge un
// moteur de cartographie pour lire une liste de tournees.
const Carte = defineAsyncComponent(() => import('../../composants/Carte.vue'))
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

    <!-- Monter une tournée : le geste qui n'existait nulle part (O-5, D-153).
         Les tournées visibles venaient toutes du jeu de démonstration, d'où
         ta question « d'où sort la tournée du livreur ? ». -->
    <div class="carte mb-3 flex flex-wrap items-center justify-between gap-3 p-4">
      <div>
        <b class="text-[13.5px]">Monter une tournée</b>
        <p class="mt-0.5 text-[12px] text-encre-douce">
          <template v-if="enAttente">
            {{ enAttente }} colis reçu{{ enAttente > 1 ? 's' : '' }} attend{{
              enAttente > 1 ? 'ent' : '' }} d'être chargé{{ enAttente > 1 ? 's' : '' }}.
            L'ordre part de l'entrepôt et suit le plus proche voisin.
          </template>
          <template v-else>
            Rien à charger : confirmez d'abord la réception des colis dans
            « Colis reçus ».
          </template>
        </p>
      </div>
      <button type="button" class="bouton-accent" :disabled="occupe" @click="calculer()">
        <Route :size="15" /> Calculer une tournée
      </button>
    </div>

    <p v-if="erreur" class="bandeau bandeau-erreur mb-3">
      <AlertTriangle :size="15" class="mt-px shrink-0" />
      {{ erreur }}
    </p>

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
      :active="(t) => selection?.id === t.id"
      @ligne-cliquee="(t) => (selection = selection?.id === t.id ? null : t)"
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
          @click="consulter(ligne)"
        />
        <!-- Recalculer : « il peut le refaire quand il veut, et le résultat
             peut différer ». Une tournée partie, elle, ne bouge plus. -->
        <ActionLigne
          v-if="['BROUILLON', 'PRETE'].includes(ligne.statut)"
          titre="Recalculer l'ordre des arrêts"
          :icone="RefreshCw"
          :desactive="occupe"
          @click="calculer(ligne.id)"
        />
        <ActionLigne
          v-if="['BROUILLON', 'PRETE'].includes(ligne.statut)"
          :titre="ligne.livreur ? 'Changer de livreur' : 'Confier à un livreur'"
          :icone="UserPlus"
          :desactive="occupe"
          @click="ouvrirAttribution(ligne)"
        />
        <ActionLigne
          v-if="ligne.livreur && ligne.statut !== 'EN_COURS' && ligne.statut !== 'TERMINEE'"
          titre="Faire partir la tournée"
          :icone="Play"
          ton="accent"
          :desactive="occupe"
          @click="fairePartir(ligne)"
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
    <FicheContextuelle
      v-if="selection"
      :titre="`Tournée n° ${selection.id}`"
      :apercu-ouvert="apercu"
      @fermer-apercu="apercu = false"
    >
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

      <!-- La carte AVANT la liste : on regarde la forme de la tournée, puis
           on lit le détail. L'inverse oblige à tout lire pour comprendre. -->
      <Carte
        v-if="pointsTournee.length > 1"
        :points="pointsTournee"
        profil="voiture"
        hauteur="220px"
        class="mb-3"
      />

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
    </FicheContextuelle>

    <!-- À qui confier la tournée. La liste ne contient QUE des livreurs
         Standard validés : proposer un choix qu'on refusera ensuite est une
         erreur qu'on laisse faire (D-153). -->
    <Popup
      v-if="attribution"
      :titre="`Confier la tournée n° ${attribution.id}`"
      explication="Le livreur est prévenu immédiatement, et ses arrêts apparaissent
                   sur son téléphone."
      @fermer="attribution = null"
    >
      <div v-if="!livreurs.length" class="vide !py-6">
        <b class="vide-titre">Aucun livreur Standard disponible</b>
        <p class="vide-texte">
          Les livreurs Express prennent des courses à la volée : ils ne peuvent pas
          prendre de tournée.
        </p>
      </div>

      <button
        v-for="livreur in livreurs"
        :key="livreur.id"
        type="button"
        class="flex w-full items-center gap-3 rounded-lg border border-trait p-2.5
               text-left text-[13px] transition-colors hover:bg-atelier"
        :disabled="occupe"
        @click="attribuer(livreur.id)"
      >
        <User :size="15" class="shrink-0 text-encre-douce" />
        <span class="flex-1">
          <b>{{ livreur.nom }}</b>
          <span class="ml-2 text-[11.5px] text-encre-douce">
            {{ livreur.de_cet_entrepot ? 'de cet entrepôt' : 'autre entrepôt' }}
          </span>
        </span>
        <span
          class="badge"
          :class="livreur.tournees_en_cours ? 'badge-attente' : 'badge-ok'"
        >
          {{ livreur.tournees_en_cours
            ? `${livreur.tournees_en_cours} tournée(s) en cours` : 'libre' }}
        </span>
      </button>

      <template #actions>
        <button type="button" class="bouton-neutre !py-2" @click="attribution = null">
          Fermer
        </button>
      </template>
    </Popup>
  </div>
</template>
