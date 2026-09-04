<script setup lang="ts">
// La file du vendeur : ce qu'il doit préparer.
//
// C'est l'écran que la maquette décrit le plus précisément : une liste avec
// ses boutons-symboles, et le **détail de la commande sélectionnée dans le
// volet de droite**, avec un seul bouton — « passer au statut suivant,
// jamais de menu libre ».
//
// Les suites possibles viennent du SERVEUR (`suites_possibles`) : le front
// n'a pas à connaître la machine à états, il affiche ce qu'on lui donne.
// C'est ce qui garantit qu'un vendeur ne saute jamais une étape.
import {
  AlertTriangle, Bike, Check, ClipboardList, Clock, Eye, MapPin, Package, UserRound, X,
} from '@lucide/vue'
import { useForm } from 'vee-validate'
import { computed, ref } from 'vue'

import { useRafraichissement } from '../../rafraichissement'
import { EchecApi } from '../../api/client'
import { commandes, type SousCommande } from '../../api/commandes'
import ActionLigne from '../../composants/ActionLigne.vue'
import ChampTexte from '../../composants/ChampTexte.vue'
import FicheContextuelle from '../../composants/FicheContextuelle.vue'
import Liste from '../../composants/Liste.vue'
import type { Colonne } from '../../composants/liste'
import Onglets from '../../composants/Onglets.vue'
import Popup from '../../composants/Popup.vue'
import { useNotification } from '../../notifications'
import { schemaAnnulationVendeur } from '../../validation'

type Ligne = SousCommande & { [cle: string]: unknown }

const liste = ref<Ligne[]>([])
const chargement = ref(true)
const erreur = ref('')
const onglet = ref('a_faire')
const selection = ref<Ligne | null>(null)
// L'oeil ouvre une popup par-dessus la liste (M-1) : le panneau de droite,
// lui, reste le contexte permanent de la ligne active.
const apercu = ref(false)
const occupe = ref(false)
/**
 * On n'ouvre la première ligne utile qu'au premier chargement.
 *
 * Depuis que l'écran se rafraîchit en fond (O-5), rouvrir d'office à chaque
 * passage ferait sauter le volet de droite toutes les vingt secondes, sous les
 * yeux de la personne en train de lire.
 */
const premierChargement = ref(true)

// On ne traite pas tout d'un bloc : la file se range par étape, comme dans
// n'importe quelle cuisine ou n'importe quel atelier.
const ETAPES: Record<string, string[]> = {
  a_faire: ['A_PREPARER'],
  en_cours: ['EN_PREPARATION'],
  pretes: ['PRETE'],
  terminees: ['EXPEDIEE', 'ANNULEE'],
}

const parEtape = (cle: string) =>
  liste.value.filter((sous) => ETAPES[cle].includes(sous.statut_preparation))

const visibles = computed(() => parEtape(onglet.value))

/**
 * Les mots du bouton viennent du SERVEUR — D-81.
 *
 * Ta remarque : *« la chaîne n'est pas comme dans la réalité »*. Un restaurant
 * « met en préparation » puis « signale prête » ; un expéditeur de colis
 * « prépare le colis » puis « l'expédie vers l'entrepôt ». Même statut
 * technique, deux gestes différents, deux mots différents.
 *
 * Cette table n'est plus qu'un **repli** : si le serveur ne donne pas de
 * libellé, on retombe sur le vocabulaire générique plutôt que sur un bouton
 * muet.
 */
const LIBELLES: Record<string, string> = {
  EN_PREPARATION: 'Commencer la préparation',
  PRETE: 'Marquer prête',
  EXPEDIEE: 'Expédier',
  ANNULEE: 'Annuler cette part',
}

const mot = (ligne: Ligne, statut: string) =>
  ligne.libelles_suites?.[statut] ?? LIBELLES[statut] ?? 'Étape suivante'

/** « 3 h 20 » plutôt que « 200 min » : personne ne compte en minutes au-delà d'une heure. */
function duree(minutes: number) {
  if (minutes < 60) return `${minutes} min`
  const heures = Math.floor(minutes / 60)
  if (heures < 24) return minutes % 60 ? `${heures} h ${minutes % 60}` : `${heures} h`
  return `${Math.floor(heures / 24)} j`
}

const BADGES: Record<string, string> = {
  A_PREPARER: 'badge-attente',
  EN_PREPARATION: 'badge-cours',
  PRETE: 'badge-ok',
  EXPEDIEE: 'badge-ok',
  ANNULEE: 'badge-erreur',
}

async function charger() {
  chargement.value = true
  try {
    liste.value = (await commandes.recues()) as Ligne[]
    // Ce qui attend en tête de file s'ouvre tout seul : on arrive ici pour
    // préparer quelque chose, pas pour contempler une liste.
    if (premierChargement.value) selection.value = parEtape(onglet.value)[0] ?? null
    premierChargement.value = false
  } finally {
    chargement.value = false
  }
}

useRafraichissement(charger, { periodique: true })

async function avancer(sous: Ligne, statut: string) {
  erreur.value = ''
  occupe.value = true
  try {
    const miseAJour = await commandes.avancer(sous.id, statut)
    Object.assign(sous, miseAJour)
  } catch (echec) {
    erreur.value = echec instanceof Error ? echec.message : 'Changement refusé.'
  } finally {
    occupe.value = false
  }
}

/** La suite normale, celle du bouton principal. L'annulation reste à part :
 *  elle ne se déclenche pas par le même geste que « avancer ». */
const suiteNormale = (sous: Ligne) =>
  (sous.suites_possibles ?? []).find((statut) => statut !== 'ANNULEE') ?? null

// ── L'annulation, qui n'était pas une annulation ─────────────────────────
//
// Le bouton posait le statut `ANNULEE` et s'arrêtait là : pas de motif, pas de
// remboursement, pas de stock rendu, et **le client n'était prévenu de rien**.
// D-07 exige un motif obligatoire et une notification forte depuis le début du
// projet ; ni l'un ni l'autre n'existaient (D-144).
const MOTIFS = [
  { cle: 'RUPTURE', libelle: 'Produit finalement indisponible' },
  { cle: 'FERMETURE', libelle: 'Boutique fermée ou service interrompu' },
  { cle: 'ERREUR_PRIX', libelle: 'Erreur de prix ou de description' },
  { cle: 'CLIENT', libelle: 'À la demande du client' },
  { cle: 'AUTRE', libelle: 'Autre raison' },
]

const notifier = useNotification()
const annulation = ref<Ligne | null>(null)

const { handleSubmit, resetForm, values, setFieldValue } = useForm({
  validationSchema: schemaAnnulationVendeur,
  initialValues: { motif: 'RUPTURE', explication: '' },
})

function ouvrirAnnulation(ligne: Ligne) {
  annulation.value = ligne
  resetForm({ values: { motif: 'RUPTURE', explication: '' } })
  erreur.value = ''
}

/** Ce que l'annulation va réellement déclencher, écrit avant de la confirmer. */
const consequences = computed(() => {
  const ligne = annulation.value
  if (!ligne) return []
  return [
    `${euros(ligne.montant_vendeur_centimes + ligne.montant_commission_centimes)} `
      + 'seront remboursés au client.',
    'Les articles retournent en stock, avec un mouvement à votre nom.',
    'Le client reçoit votre explication, mot pour mot.',
    'Vous ne serez pas payé pour cette part.',
  ]
})

const confirmerAnnulation = handleSubmit(async (saisie) => {
  const ligne = annulation.value
  if (!ligne) return
  erreur.value = ''
  occupe.value = true
  try {
    const miseAJour = await commandes.avancer(ligne.id, 'ANNULEE', saisie)
    Object.assign(ligne, miseAJour)
    annulation.value = null
    notifier.succes('Le client a été prévenu et remboursé.')
  } catch (echec) {
    erreur.value = echec instanceof EchecApi ? echec.erreur.message : 'Annulation refusée.'
    notifier.echec(erreur.value)
  } finally {
    occupe.value = false
  }
})

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
  { cle: 'numero', titre: 'Commande', largeur: 180 },
  { cle: 'articles', titre: 'Contenu' },
  // Ou part le colis (D-74) : le vendeur ne le savait meme pas. Ville et code
  // postal, pas la rue — il prepare, il ne livre pas.
  { cle: 'destination', titre: 'Destination', largeur: 150, masquerSous: 'lg' },
  { cle: 'montant', titre: 'Votre part', largeur: 110, aligne: 'droite', masquerSous: 'md',
    champTri: 'montant_vendeur_centimes' },
  { cle: 'statut', titre: 'État', largeur: 120, aligne: 'centre' },
]

const euros = (centimes: number) =>
  (centimes / 100).toLocaleString('fr-FR', { style: 'currency', currency: 'EUR' })

/** « il y a deux heures » plutot qu'une date : c'est la fraicheur qui compte. */
function depuis(quand: string) {
  const minutes = Math.round((Date.now() - new Date(quand).getTime()) / 60_000)
  if (minutes < 1) return 'a l\'instant'
  if (minutes < 60) return `il y a ${minutes} min`
  const heures = Math.round(minutes / 60)
  if (heures < 24) return `il y a ${heures} h`
  return new Date(quand).toLocaleDateString('fr-FR')
}
</script>

<template>
  <div class="mx-auto max-w-[1040px] animate-[apparition_0.2s_ease-out]">
    <Onglets
      v-model="onglet"
      :onglets="[
        { cle: 'a_faire', libelle: 'À préparer', compteur: parEtape('a_faire').length },
        { cle: 'en_cours', libelle: 'En préparation', compteur: parEtape('en_cours').length },
        { cle: 'pretes', libelle: 'Prêtes', compteur: parEtape('pretes').length },
        { cle: 'terminees', libelle: 'Terminées', compteur: parEtape('terminees').length },
      ]"
    />

    <p v-if="erreur" class="bandeau bandeau-erreur mb-3">
      <AlertTriangle :size="15" class="mt-px shrink-0" />
      {{ erreur }}
    </p>

    <Liste
      :colonnes="colonnes"
      :lignes="visibles"
      :cle-ligne="(sous) => sous.id"
      :chargement="chargement"
      :recherche="(sous) => `${sous.numero_commande ?? ''} ${sous.lignes.map((l) => l.nom_produit_capture).join(' ')}`"
      :active="(sous) => selection?.id === sous.id"
      @ligne-cliquee="(sous) => (selection = selection?.id === sous.id ? null : sous)"
      placeholder="Numéro de commande, produit…"
    >
      <template #col-numero="{ ligne }">
        <b class="flex min-w-0 items-center gap-2">
          <component
            :is="ligne.type_service === 'EXPRESS' ? Bike : Package"
            :size="14"
            class="shrink-0 text-encre-douce"
          />
          <span class="truncate">{{ ligne.numero_commande ?? `n° ${ligne.id}` }}</span>
        </b>
      </template>
      <template #col-articles="{ ligne }">
        <span class="block min-w-0 truncate text-encre-douce">
          {{ ligne.lignes.reduce((total, l) => total + l.quantite, 0) }} article(s) —
          {{ ligne.lignes.map((l) => l.nom_produit_capture).join(', ') }}
        </span>
        <!-- Qui a deja agi (D-80). Le vendeur et son personnel travaillaient
             sur la meme file sans savoir lequel des deux l'avait prise. -->
        <span class="mt-0.5 flex flex-wrap items-center gap-x-3 gap-y-0.5 text-[11px]">
          <span v-if="ligne.dernier_acte" class="flex items-center gap-1 text-encre-douce">
            <UserRound :size="10" class="shrink-0" />
            {{ ligne.dernier_acte.qui }}, {{ depuis(ligne.dernier_acte.quand) }}
          </span>
          <!-- Le temps compte (D-81) : une file où tout se ressemble se traite
               dans le désordre. Au-delà du délai annoncé au client, la ligne
               passe en alerte. -->
          <span
            v-if="ligne.attente?.minutes !== null && ligne.attente"
            class="flex items-center gap-1"
            :class="ligne.attente.en_retard ? 'font-bold text-[#9c2116]' : 'text-encre-douce'"
            :title="ligne.attente.en_retard
              ? `Au-delà du délai annoncé au client (${duree(ligne.attente.delai_minutes!)})`
              : 'Temps d’attente à cette étape'"
          >
            <Clock :size="10" class="shrink-0" />
            {{ duree(ligne.attente.minutes!) }}
            <span v-if="ligne.attente.en_retard">— en retard</span>
          </span>
        </span>
      </template>
      <template #col-destination="{ ligne }">
        <span v-if="ligne.destination" class="flex min-w-0 items-center gap-1.5">
          <MapPin :size="13" class="shrink-0 text-encre-douce" />
          <span class="truncate">
            {{ ligne.destination.ville }}
            <span class="text-encre-douce">{{ ligne.destination.code_postal }}</span>
          </span>
        </span>
        <span v-else class="text-trait">&mdash;</span>
      </template>
      <template #col-montant="{ ligne }">
        <b>{{ euros(ligne.montant_vendeur_centimes) }}</b>
      </template>
      <template #col-statut="{ ligne }">
        <span class="badge" :class="BADGES[ligne.statut_preparation] ?? 'badge-neutre'">
          {{ ligne.libelle_statut }}
        </span>
      </template>

      <template #actions="{ ligne }">
        <ActionLigne
          titre="Consulter cette commande"
          :icone="Eye"
          :ton="selection?.id === ligne.id ? 'accent' : 'neutre'"
          @click="consulter(ligne)"
        />
        <ActionLigne
          v-if="suiteNormale(ligne)"
          :titre="mot(ligne, suiteNormale(ligne)!)"
          :icone="Check"
          ton="accent"
          :desactive="occupe"
          @click="avancer(ligne, suiteNormale(ligne)!)"
        />
        <ActionLigne
          v-if="(ligne.suites_possibles ?? []).includes('ANNULEE')"
          :titre="mot(ligne, 'ANNULEE')"
          :icone="X"
          ton="danger"
          :desactive="occupe"
          @click="ouvrirAnnulation(ligne)"
        />
      </template>

      <template #vide>
        <div class="vide">
          <ClipboardList :size="30" class="text-trait" />
          <b class="vide-titre">
            {{
              onglet === 'a_faire' ? 'Rien à préparer pour l\'instant'
              : onglet === 'terminees' ? 'Aucune commande terminée'
              : 'Rien à cette étape'
            }}
          </b>
          <p class="vide-texte">
            Les commandes payées arrivent ici automatiquement, dans l'ordre où elles
            tombent.
          </p>
        </div>
      </template>
    </Liste>

    <!-- Le volet de la maquette : le détail, et UN seul bouton d'avancement. -->
    <FicheContextuelle
      v-if="selection"
      :titre="selection.numero_commande ?? `Commande n° ${selection.id}`"
      :apercu-ouvert="apercu"
      @fermer-apercu="apercu = false"
    >
      <dl class="flex flex-col gap-2 text-[12px]">
        <div class="flex justify-between gap-2">
          <dt class="text-encre-douce">Service</dt>
          <dd class="font-semibold">
            {{ selection.type_service === 'EXPRESS' ? 'Express' : 'Standard' }}
          </dd>
        </div>
        <div class="flex justify-between gap-2">
          <dt class="text-encre-douce">Statut</dt>
          <dd>
            <span class="badge" :class="BADGES[selection.statut_preparation] ?? 'badge-neutre'">
              {{ selection.libelle_statut }}
            </span>
          </dd>
        </div>
        <div class="flex justify-between gap-2">
          <dt class="text-encre-douce">Vous touchez</dt>
          <dd class="font-semibold">{{ euros(selection.montant_vendeur_centimes) }}</dd>
        </div>
        <div class="flex justify-between gap-2">
          <dt class="text-encre-douce">Commission</dt>
          <dd class="font-semibold">{{ euros(selection.montant_commission_centimes) }}</dd>
        </div>
      </dl>

      <b class="mt-4 block text-[11px] font-bold tracking-wider text-encre-douce uppercase">
        À préparer
      </b>
      <ul class="mt-2 flex flex-col gap-1.5">
        <li
          v-for="produit in selection.lignes"
          :key="produit.id"
          class="flex items-center gap-2 rounded-lg border border-trait bg-papier px-2.5 py-2
                 text-[12px]"
        >
          <span
            class="flex h-5 w-5 shrink-0 items-center justify-center rounded-md bg-atelier
                   text-[10.5px] font-bold"
          >
            {{ produit.quantite }}
          </span>
          <span class="min-w-0 flex-1 truncate">{{ produit.nom_produit_capture }}</span>
          <b>{{ euros(produit.sous_total_centimes) }}</b>
        </li>
      </ul>

      <div v-if="suiteNormale(selection)" class="mt-4">
        <button
          type="button"
          class="bouton-accent w-full"
          :disabled="occupe"
          @click="avancer(selection, suiteNormale(selection)!)"
        >
          <Check :size="15" />
          {{ mot(selection, suiteNormale(selection)!) }}
        </button>
        <button
          v-if="(selection.suites_possibles ?? []).includes('ANNULEE')"
          type="button"
          class="bouton-neutre mt-2 w-full !text-[#9c2116]"
          :disabled="occupe"
          @click="ouvrirAnnulation(selection)"
        >
          <X :size="15" />
          {{ mot(selection, 'ANNULEE') }}
        </button>
        <p class="mt-2 text-[11px] leading-relaxed text-encre-douce">
          On passe au statut suivant, jamais à un statut choisi librement : c'est le
          serveur qui dit ce qui est possible.
        </p>
      </div>
    </FicheContextuelle>

    <!-- Annuler n'est pas « avancer d'un cran » : le client est remboursé, le
         stock revient, et il lit l'explication. On le dit AVANT (D-07, D-144). -->
    <Popup
      v-if="annulation"
      :titre="`Annuler ${annulation.numero_commande ?? `la commande n° ${annulation.id}`}`"
      explication="Cette annulation est définitive et le client en est prévenu
                   immédiatement, avec votre explication."
      @fermer="annulation = null"
    >
      <form class="flex flex-col gap-3" @submit.prevent="confirmerAnnulation">
        <div class="flex flex-col gap-2">
          <span class="etiquette">Pourquoi ?</span>
          <label
            v-for="choix in MOTIFS"
            :key="choix.cle"
            class="flex cursor-pointer items-center gap-3 rounded-lg border p-2.5 text-[12.5px]
                   transition-colors"
            :class="values.motif === choix.cle
              ? 'border-[color:var(--accent)] bg-atelier'
              : 'border-trait hover:bg-atelier'"
          >
            <input
              type="radio"
              name="motif-annulation"
              :value="choix.cle"
              :checked="values.motif === choix.cle"
              @change="setFieldValue('motif', choix.cle)"
            />
            {{ choix.libelle }}
          </label>
        </div>

        <ChampTexte
          nom="explication"
          label="Votre explication au client"
          aide="C'est ce texte qu'il lira, mot pour mot. Une phrase honnête évite un litige."
        />

        <ul class="flex flex-col gap-1 rounded-lg bg-atelier p-3 text-[11.5px] text-encre-douce">
          <li v-for="(consequence, index) in consequences" :key="index" class="flex gap-2">
            <span class="text-[color:var(--accent)]">•</span>{{ consequence }}
          </li>
        </ul>

        <p v-if="erreur" class="bandeau bandeau-erreur">
          <AlertTriangle :size="15" class="mt-px shrink-0" /> {{ erreur }}
        </p>
      </form>

      <template #actions>
        <button type="button" class="bouton-neutre !py-2" @click="annulation = null">
          Garder la commande
        </button>
        <button
          type="button"
          class="bouton-accent !py-2"
          :disabled="occupe"
          @click="confirmerAnnulation"
        >
          <X :size="15" /> Annuler et rembourser
        </button>
      </template>
    </Popup>
  </div>
</template>
