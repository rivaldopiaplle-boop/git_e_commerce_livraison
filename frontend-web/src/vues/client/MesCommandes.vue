<script setup lang="ts">
// Le suivi client.
//
// Deux choses ajoutées au bloc K :
//
//   · la liste commune du projet, avec ses boutons-symboles — consulter le
//     détail, et **donner son avis** ;
//   · l'avis lui-même, qui n'existait nulle part : « le client ne peut pas
//     donner son avis » (K-1). On ne note que ce qu'on a reçu (R-06), donc
//     le bouton n'apparaît que sur une commande livrée.
//
// La frise de suivi reste, mais dans le volet : elle n'a de sens que pour la
// commande qu'on regarde, pas pour les quinze à la fois.
import {
  AlertTriangle, Bike, CheckCircle2, CreditCard, Eye, FileText, Package, Receipt,
  ShieldAlert, Star,
} from '@lucide/vue'
import { computed, ref } from 'vue'
import { useRoute } from 'vue-router'

import { useRafraichissement } from '../../rafraichissement'
import { api, EchecApi } from '../../api/client'
import { useNotification } from '../../notifications'
import { commandes, type Commande } from '../../api/commandes'
import { espaces } from '../../api/espaces'
import Rating from 'primevue/rating'

import ActionLigne from '../../composants/ActionLigne.vue'
import Liste from '../../composants/Liste.vue'
import type { Colonne } from '../../composants/liste'
import Popup from '../../composants/Popup.vue'
import FicheContextuelle from '../../composants/FicheContextuelle.vue'

type Ligne = Commande & { [cle: string]: unknown }
type ElementNotable = {
  cible: string
  id_cible: number
  libelle: string
  sous_titre: string
  note: number | null
  commentaire: string
}

const notifier = useNotification()
const route = useRoute()
const liste = ref<Ligne[]>([])
const chargement = ref(true)
const selection = ref<Ligne | null>(null)
// L'oeil ouvre une popup par-dessus la liste (M-1) : le panneau de droite,
// lui, reste le contexte permanent de la ligne active.
const apercu = ref(false)

const avisOuvert = ref<Ligne | null>(null)

// Le litige (D-94). Un client qui recoit un colis incomplet doit pouvoir le
// dire depuis la commande concernee, pas depuis un formulaire de contact
// generique ou il devrait tout ressaisir.
const litigeOuvert = ref<Ligne | null>(null)
const motifLitige = ref('INCOMPLET')
const recitLitige = ref('')
const MOTIFS = [
  { cle: 'NON_RECU', libelle: 'Je n’ai jamais recu ma commande' },
  { cle: 'INCOMPLET', libelle: 'Il manque des articles' },
  { cle: 'ENDOMMAGE', libelle: 'Un produit est arrive abime' },
  { cle: 'NON_CONFORME', libelle: 'Ce n’est pas ce que j’avais commande' },
]
// On ne conteste pas une livraison qui n'a pas eu lieu : le suivi repond a
// « ou est ma commande ? », un litige non.
const CONTESTABLES = ['LIVREE', 'ECHEC_LIVRAISON']
const notables = ref<ElementNotable[]>([])
const choisi = ref<ElementNotable | null>(null)
const note = ref(5)
const commentaire = ref('')
const erreur = ref('')
/**
 * On n'ouvre la première ligne utile qu'au premier chargement.
 *
 * Depuis que l'écran se rafraîchit en fond (O-5), rouvrir d'office à chaque
 * passage ferait sauter le volet de droite toutes les vingt secondes, sous les
 * yeux de la personne en train de lire.
 */
const premierChargement = ref(true)
const occupe = ref(false)

useRafraichissement(async () => {
  try {
    liste.value = (await commandes.miennes()) as Ligne[]
    if (premierChargement.value) selection.value = liste.value[0] ?? null
    premierChargement.value = false
  } finally {
    chargement.value = false
  }
}, { periodique: true })

const euros = (centimes: number) =>
  (centimes / 100).toLocaleString('fr-FR', { style: 'currency', currency: 'EUR' })

// Le vocabulaire diffère selon le circuit : le client d'un restaurant ne
// comprendrait pas « expédiée vers l'entrepôt ».
const ETAPES_EXPRESS = ['PAYEE', 'EN_PREPARATION', 'PRETE', 'EN_LIVRAISON', 'LIVREE']
const ETAPES_STANDARD = [
  'PAYEE', 'EN_PREPARATION', 'EXPEDIEE_ENTREPOT', 'RECUE_ENTREPOT', 'EN_TOURNEE', 'LIVREE',
]
const LIBELLES: Record<string, string> = {
  EN_ATTENTE_PAIEMENT: 'En attente de paiement',
  PAYEE: 'Payée',
  EN_PREPARATION: 'En préparation',
  PRETE: 'Prête',
  EXPEDIEE_ENTREPOT: "Vers l'entrepôt",
  RECUE_ENTREPOT: "À l'entrepôt",
  EN_TOURNEE: 'En tournée',
  EN_LIVRAISON: 'En livraison',
  LIVREE: 'Livrée',
  ANNULEE: 'Annulée',
  REMBOURSEE: 'Remboursée',
  ECHEC_LIVRAISON: 'Échec de livraison',
}

const etapes = (commande: Ligne) =>
  commande.type_service === 'EXPRESS' ? ETAPES_EXPRESS : ETAPES_STANDARD
const position = (commande: Ligne) => etapes(commande).indexOf(commande.statut_actuel)

const BADGES: Record<string, string> = {
  LIVREE: 'badge-ok',
  ANNULEE: 'badge-erreur',
  ECHEC_LIVRAISON: 'badge-erreur',
  REMBOURSEE: 'badge-neutre',
  EN_ATTENTE_PAIEMENT: 'badge-attente',
}

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
  { cle: 'numero', titre: 'Commande', largeur: 190, champTri: 'date_commande' },
  { cle: 'boutiques', titre: 'Boutiques' },
  { cle: 'montant', titre: 'Montant', largeur: 100, aligne: 'droite', masquerSous: 'sm',
    champTri: 'montant_total_centimes' },
  { cle: 'statut', titre: 'Suivi', largeur: 140, aligne: 'centre' },
]

async function ouvrirAvis(commande: Ligne) {
  erreur.value = ''
  avisOuvert.value = commande
  const donnees = await api.get<{ livree: boolean; elements: ElementNotable[] }>(
    `/commandes/${commande.id}/avis`,
  )
  notables.value = donnees.elements
  choisi.value = donnees.elements[0] ?? null
  note.value = choisi.value?.note ?? 5
  commentaire.value = choisi.value?.commentaire ?? ''
}

function ouvrirLitige(commande: Ligne) {
  litigeOuvert.value = commande
  motifLitige.value = 'INCOMPLET'
  recitLitige.value = ''
  erreur.value = ''
}

async function envoyerLitige() {
  if (!litigeOuvert.value) return
  erreur.value = ''
  occupe.value = true
  try {
    await espaces.client.ouvrirLitige(litigeOuvert.value.id, {
      motif: motifLitige.value,
      description: recitLitige.value,
    })
    notifier.succes(
      'Votre signalement est enregistré',
      'La boutique a 48 heures pour répondre, puis un administrateur tranchera.',
    )
    litigeOuvert.value = null
  } catch (echec) {
    erreur.value = echec instanceof EchecApi ? echec.erreur.message
      : "Le signalement n'a pas été pris."
    notifier.echec(erreur.value)
  } finally {
    occupe.value = false
  }
}

function choisir(element: ElementNotable) {
  choisi.value = element
  note.value = element.note ?? 5
  commentaire.value = element.commentaire ?? ''
}

async function envoyerAvis() {
  if (!avisOuvert.value || !choisi.value) return
  erreur.value = ''
  occupe.value = true
  try {
    const donnees = await api.post<{ livree: boolean; elements: ElementNotable[] }>(
      `/commandes/${avisOuvert.value.id}/avis`,
      {
        cible: choisi.value.cible,
        id_cible: choisi.value.id_cible,
        note: note.value,
        commentaire: commentaire.value,
      },
    )
    notables.value = donnees.elements
    notifier.succes(`Votre avis sur « ${choisi.value.libelle} » est enregistré.`, 'Merci')
    const suivant = donnees.elements.find((element) => element.note === null)
    if (suivant) choisir(suivant)
  } catch (echec) {
    erreur.value = echec instanceof EchecApi ? echec.erreur.message : "L'avis n'a pas été pris."
    notifier.echec(erreur.value)
  } finally {
    occupe.value = false
  }
}

/** Les cibles, groupees et expliquees.
 *
 *  « Il peut donner un avis sur Julien alors que le produit est pour
 *  TechSophie » : le livreur proposé EST celui de la commande, mais l'écran
 *  alignait les trois cibles à plat, si bien qu'un nom de personne côtoyait un
 *  nom de boutique sans que rien n'explique le lien (D-72).
 */
const groupesNotables = computed(() => {
  const par = (cible: string) => notables.value.filter((e) => e.cible === cible)
  return [
    { cle: 'VENDEUR', titre: 'La boutique',
      explication: 'Celle qui a préparé votre commande.', elements: par('VENDEUR') },
    { cle: 'PRODUIT', titre: 'Les produits reçus',
      explication: 'Uniquement ceux de cette commande.', elements: par('PRODUIT') },
    { cle: 'LIVREUR', titre: 'La livraison',
      explication: 'La personne qui vous a apporté cette commande.',
      elements: par('LIVREUR') },
  ].filter((groupe) => groupe.elements.length)
})

const restantsANoter = computed(
  () => notables.value.filter((element) => element.note === null).length,
)

const quand = (date: string) => new Date(date).toLocaleDateString('fr-FR')

// Une commande creee n'est pas une commande payee, et tant qu'elle ne l'est
// pas elle immobilise du stock (D-15). Le rappeler en haut de l'ecran est ce
// qui evite qu'un client croie avoir termine.
const impayees = computed(() =>
  liste.value.filter((c) => c.statut_actuel === 'EN_ATTENTE_PAIEMENT'),
)

/** La facture n'existe qu'apres la capture : avant, le bouton ne promet rien. */
const AVANT_PAIEMENT = ['EN_ATTENTE_PAIEMENT', 'ANNULEE']
</script>

<template>
  <div class="mx-auto max-w-[1020px] animate-[apparition_0.2s_ease-out]">
    <p v-if="route.query.payees" class="bandeau bandeau-info mb-4">
      <CheckCircle2 :size="15" class="mt-px shrink-0" />
      {{ route.query.payees }} commande{{ Number(route.query.payees) > 1 ? 's' : '' }} payée{{
        Number(route.query.payees) > 1 ? 's' : ''
      }}. Les boutiques ont été prévenues, vous suivez chacune ci-dessous.
    </p>

    <!-- Ce qui attend un paiement, en haut et cliquable : le laisser au fond
         d'une liste reviendrait à le cacher. -->
    <div v-if="impayees.length" class="bandeau mb-4 items-center justify-between">
      <span class="flex items-start gap-2.5">
        <CreditCard :size="15" class="mt-px shrink-0" />
        <span>
          {{ impayees.length }} commande{{ impayees.length > 1 ? 's' : '' }}
          attend{{ impayees.length > 1 ? 'ent' : '' }} votre paiement. Vos articles sont
          mis de côté en attendant.
        </span>
      </span>
      <RouterLink :to="{ name: 'paiement' }" class="bouton-accent shrink-0 !py-1.5 !text-[12px]">
        Payer maintenant
      </RouterLink>
    </div>

    <Liste
      :colonnes="colonnes"
      :lignes="liste"
      :cle-ligne="(commande) => commande.id"
      :chargement="chargement"
      :recherche="(c) => `${c.numero_commande} ${c.boutiques.join(' ')}`"
      :active="(c) => selection?.id === c.id"
      @ligne-cliquee="(c) => (selection = selection?.id === c.id ? null : c)"
      placeholder="Numéro de commande, boutique…"
    >
      <template #col-numero="{ ligne }">
        <span class="flex min-w-0 items-center gap-2">
          <component
            :is="ligne.type_service === 'EXPRESS' ? Bike : Package"
            :size="14"
            class="shrink-0 text-encre-douce"
          />
          <span class="min-w-0">
            <b class="block truncate">{{ ligne.numero_commande }}</b>
            <span class="text-[11.2px] text-encre-douce">{{ quand(ligne.date_commande) }}</span>
          </span>
        </span>
      </template>
      <template #col-boutiques="{ ligne }">
        <span class="min-w-0 truncate text-encre-douce">{{ ligne.boutiques.join(', ') }}</span>
      </template>
      <template #col-montant="{ ligne }">
        <b>{{ euros(ligne.montant_total_centimes) }}</b>
      </template>
      <template #col-statut="{ ligne }">
        <span class="badge" :class="BADGES[ligne.statut_actuel] ?? 'badge-cours'">
          {{ LIBELLES[ligne.statut_actuel] ?? ligne.libelle_statut }}
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
          v-if="ligne.statut_actuel === 'EN_ATTENTE_PAIEMENT'"
          titre="Payer cette commande"
          :icone="CreditCard"
          ton="accent"
          :vers="{ name: 'paiement' }"
        />
        <ActionLigne
          :titre="AVANT_PAIEMENT.includes(ligne.statut_actuel)
            ? 'La facture existe une fois la commande payée'
            : 'Voir et imprimer la facture'"
          :icone="FileText"
          :desactive="AVANT_PAIEMENT.includes(ligne.statut_actuel)"
          :vers="{ name: 'facture', params: { id: ligne.id } }"
        />
        <ActionLigne
          :titre="ligne.statut_actuel === 'LIVREE' ? 'Donner mon avis'
                                                   : 'On note une commande une fois reçue'"
          :icone="Star"
          :desactive="ligne.statut_actuel !== 'LIVREE'"
          @click="ouvrirAvis(ligne)"
        />
        <ActionLigne
          :titre="CONTESTABLES.includes(ligne.statut_actuel)
            ? 'Signaler un problème sur cette commande'
            : 'Un signalement s’ouvre une fois la commande arrivée à son terme'"
          :icone="ShieldAlert"
          ton="danger"
          :desactive="!CONTESTABLES.includes(ligne.statut_actuel)"
          @click="ouvrirLitige(ligne)"
        />
      </template>

      <template #vide>
        <div class="vide">
          <Receipt :size="30" class="text-trait" />
          <b class="vide-titre">Aucune commande pour l'instant</b>
          <p class="vide-texte">
            Vos commandes apparaîtront ici, avec leur suivi étape par étape.
          </p>
          <RouterLink :to="{ name: 'vitrine' }" class="bouton-accent mt-4">
            Voir le catalogue
          </RouterLink>
        </div>
      </template>
    </Liste>

    <!-- Le suivi de la commande regardée, dans le volet -->
    <FicheContextuelle
      v-if="selection"
      :titre="selection.numero_commande"
      :apercu-ouvert="apercu"
      @fermer-apercu="apercu = false"
    >
      <dl class="flex flex-col gap-2 text-[12px]">
        <div class="flex justify-between gap-2">
          <dt class="text-encre-douce">Passée le</dt>
          <dd class="font-semibold">{{ quand(selection.date_commande) }}</dd>
        </div>
        <div class="flex justify-between gap-2">
          <dt class="text-encre-douce">Service</dt>
          <dd class="font-semibold">
            {{ selection.type_service === 'EXPRESS' ? 'Express' : 'Standard' }}
          </dd>
        </div>
        <div class="flex justify-between gap-2">
          <dt class="text-encre-douce">Total</dt>
          <dd class="font-semibold">{{ euros(selection.montant_total_centimes) }}</dd>
        </div>
        <div>
          <dt class="text-encre-douce">Livrée à</dt>
          <dd class="font-semibold">{{ selection.adresse }}</dd>
        </div>
      </dl>

      <b class="mt-4 block text-[11px] font-bold tracking-wider text-encre-douce uppercase">
        Où en est-elle
      </b>
      <ol class="mt-2 flex flex-col">
        <li
          v-for="(etape, index) in etapes(selection)"
          :key="etape"
          class="flex gap-2.5"
        >
          <span class="flex flex-col items-center">
            <span
              class="flex h-4 w-4 items-center justify-center rounded-full text-[9px] text-white"
              :style="{
                background: index <= position(selection) ? 'var(--accent)' : 'var(--color-trait)',
              }"
            >
              <CheckCircle2 v-if="index < position(selection)" :size="9" />
            </span>
            <span
              v-if="index < etapes(selection).length - 1"
              class="my-0.5 w-px flex-1"
              :style="{
                background: index < position(selection) ? 'var(--accent)' : 'var(--color-trait)',
              }"
            />
          </span>
          <span
            class="pb-3 text-[12px]"
            :class="index === position(selection) ? 'font-bold' : 'text-encre-douce'"
          >
            {{ LIBELLES[etape] ?? etape }}
          </span>
        </li>
      </ol>

      <button
        v-if="selection.statut_actuel === 'LIVREE'"
        type="button"
        class="bouton-accent w-full"
        @click="ouvrirAvis(selection)"
      >
        <Star :size="15" /> Donner mon avis
      </button>
    </FicheContextuelle>

    <!-- L'avis : une popup, comme toute action courte (règle d'or n°9) -->
    <Popup
      v-if="avisOuvert"
      titre="Donner mon avis"
      explication="On ne note que ce qu'on a reçu. Choisissez ce que vous voulez noter :
                   la boutique, un produit, ou le livreur."
      @fermer="avisOuvert = null"
    >
      <div v-for="groupe in groupesNotables" :key="groupe.titre" class="mb-3">
        <span class="etiquette">{{ groupe.titre }}</span>
        <p class="mb-1.5 text-[11px] text-encre-douce">{{ groupe.explication }}</p>
        <div class="flex flex-wrap gap-1.5">
          <button
            v-for="element in groupe.elements"
            :key="`${element.cible}-${element.id_cible}`"
            type="button"
            class="puce-filtre"
            :class="choisi?.cible === element.cible && choisi?.id_cible === element.id_cible
              ? 'puce-filtre-active' : ''"
            @click="choisir(element)"
          >
            {{ element.libelle }}
            <Star v-if="element.note" :size="11" />
          </button>
        </div>
      </div>

      <template v-if="choisi">
        <p class="mt-3 text-[11.5px] text-encre-douce">
          {{ choisi.sous_titre }} — {{ choisi.libelle }}
        </p>

        <div class="mt-2 flex items-center gap-3">
          <Rating v-model="note" />
          <b class="text-[12.5px]">{{ note }} / 5</b>
        </div>

        <label class="mt-3 flex flex-col gap-1.5">
          <span class="etiquette">Votre commentaire</span>
          <textarea
            v-model="commentaire"
            rows="3"
            class="champ-clair"
            placeholder="Ce qui vous a plu, ou pas."
          />
        </label>
      </template>

      <p v-if="erreur" class="bandeau bandeau-erreur mt-3">{{ erreur }}</p>
      <p v-else-if="restantsANoter" class="mt-3 text-[11.5px] text-encre-douce">
        Il vous reste {{ restantsANoter }} élément(s) à noter sur cette commande.
      </p>

      <template #actions>
        <button type="button" class="bouton-neutre !py-2" @click="avisOuvert = null">
          Fermer
        </button>
        <button
          type="button"
          class="bouton-accent !py-2"
          :disabled="occupe || !choisi"
          @click="envoyerAvis"
        >
          <Star :size="15" />
          {{ choisi?.note ? 'Modifier mon avis' : 'Publier mon avis' }}
        </button>
      </template>
    </Popup>

    <!-- Le signalement d'un problème (D-94) -->
    <Popup
      v-if="litigeOuvert"
      :titre="`Signaler un problème — ${litigeOuvert.numero_commande}`"
      explication="La boutique aura 48 heures pour donner sa version, puis un
                   administrateur tranchera avec les deux récits sous les yeux."
      @fermer="litigeOuvert = null"
    >
      <div class="flex flex-col gap-4">
        <div class="flex flex-col gap-2">
          <span class="etiquette">Que s'est-il passé ?</span>
          <label
            v-for="motif in MOTIFS"
            :key="motif.cle"
            class="flex cursor-pointer items-center gap-3 rounded-lg border p-2.5 text-[12.5px]
                   transition-colors"
            :class="motifLitige === motif.cle ? 'border-[color:var(--accent)] bg-atelier'
                                              : 'border-trait hover:bg-atelier'"
          >
            <input v-model="motifLitige" type="radio" :value="motif.cle" name="motif-litige" />
            {{ motif.libelle }}
          </label>
        </div>

        <label class="flex flex-col gap-1.5">
          <span class="etiquette">Racontez, en quelques phrases</span>
          <textarea
            v-model="recitLitige"
            rows="4"
            class="champ-clair"
            placeholder="Ce que vous avez reçu, ce qui manquait, dans quel état."
          />
          <span class="text-[11px] text-encre-douce">
            C'est ce texte que la boutique et l'administrateur liront pour trancher.
          </span>
        </label>

        <p v-if="erreur" class="bandeau bandeau-erreur">
          <AlertTriangle :size="15" class="mt-px shrink-0" />
          {{ erreur }}
        </p>
      </div>

      <template #actions>
        <button type="button" class="bouton-neutre !py-2" @click="litigeOuvert = null">
          Annuler
        </button>
        <button
          type="button"
          class="bouton-accent !py-2"
          :disabled="occupe || recitLitige.trim().length < 20"
          @click="envoyerLitige"
        >
          <ShieldAlert :size="15" />
          {{ occupe ? 'Envoi…' : 'Envoyer mon signalement' }}
        </button>
      </template>
    </Popup>
  </div>
</template>
