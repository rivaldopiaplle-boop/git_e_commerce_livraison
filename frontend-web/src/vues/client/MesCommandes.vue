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
  Bike, CheckCircle2, Eye, Package, Receipt, Star,
} from '@lucide/vue'
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'

import { api, EchecApi } from '../../api/client'
import { useNotification } from '../../notifications'
import { commandes, type Commande } from '../../api/commandes'
import ActionLigne from '../../composants/ActionLigne.vue'
import Liste from '../../composants/Liste.vue'
import type { Colonne } from '../../composants/liste'
import Popup from '../../composants/Popup.vue'
import Volet from '../../composants/Volet.vue'

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

const avisOuvert = ref<Ligne | null>(null)
const notables = ref<ElementNotable[]>([])
const choisi = ref<ElementNotable | null>(null)
const note = ref(5)
const commentaire = ref('')
const erreur = ref('')
const occupe = ref(false)

onMounted(async () => {
  try {
    liste.value = (await commandes.miennes()) as Ligne[]
    selection.value = liste.value[0] ?? null
  } finally {
    chargement.value = false
  }
})

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

const restantsANoter = computed(
  () => notables.value.filter((element) => element.note === null).length,
)

const quand = (date: string) => new Date(date).toLocaleDateString('fr-FR')
</script>

<template>
  <div class="mx-auto max-w-[1020px] animate-[apparition_0.2s_ease-out]">
    <p v-if="route.query.creees" class="bandeau bandeau-info mb-4">
      <CheckCircle2 :size="15" class="mt-px shrink-0" />
      {{ route.query.creees }} commande{{ Number(route.query.creees) > 1 ? 's' : '' }} créée{{
        Number(route.query.creees) > 1 ? 's' : ''
      }}. Vous suivez chacune ci-dessous.
    </p>

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
          titre="Suivre cette commande"
          :icone="Eye"
          :ton="selection?.id === ligne.id ? 'accent' : 'neutre'"
          @click="selection = selection?.id === ligne.id ? null : ligne"
        />
        <ActionLigne
          :titre="ligne.statut_actuel === 'LIVREE' ? 'Donner mon avis'
                                                   : 'On note une commande une fois reçue'"
          :icone="Star"
          :desactive="ligne.statut_actuel !== 'LIVREE'"
          @click="ouvrirAvis(ligne)"
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
    <Volet v-if="selection" :titre="selection.numero_commande">
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
    </Volet>

    <!-- L'avis : une popup, comme toute action courte (règle d'or n°9) -->
    <Popup
      v-if="avisOuvert"
      titre="Donner mon avis"
      explication="On ne note que ce qu'on a reçu. Choisissez ce que vous voulez noter :
                   la boutique, un produit, ou le livreur."
      @fermer="avisOuvert = null"
    >
      <div class="flex flex-wrap gap-1.5">
        <button
          v-for="element in notables"
          :key="`${element.cible}-${element.id_cible}`"
          type="button"
          class="puce-filtre"
          :class="choisi === element || (choisi?.cible === element.cible
                  && choisi?.id_cible === element.id_cible) ? 'puce-filtre-active' : ''"
          @click="choisir(element)"
        >
          {{ element.libelle }}
          <Star v-if="element.note" :size="11" />
        </button>
      </div>

      <template v-if="choisi">
        <p class="mt-3 text-[11.5px] text-encre-douce">
          {{ choisi.sous_titre }} — {{ choisi.libelle }}
        </p>

        <div class="mt-2 flex items-center gap-1.5">
          <button
            v-for="valeur in [1, 2, 3, 4, 5]"
            :key="valeur"
            type="button"
            class="bouton-ligne !h-9 !w-9"
            :class="valeur <= note ? 'bouton-ligne-accent' : ''"
            :title="`${valeur} sur 5`"
            @click="note = valeur"
          >
            <Star :size="16" />
            <span class="sr-only">{{ valeur }} sur 5</span>
          </button>
          <span class="ml-2 text-[12.5px] font-bold">{{ note }} / 5</span>
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
  </div>
</template>
