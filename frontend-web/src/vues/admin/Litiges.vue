<script setup lang="ts">
// L'arbitrage des litiges — D-94.
//
// L'écran était un dépliant en lecture seule, et il ne pouvait pas être autre
// chose : arbitrer suppose un paiement à rembourser, et le paiement n'existait
// pas. Il existe maintenant, donc l'écran tranche.
//
// Deux choses qui se voient, et qui sont le cœur de la décision D-94 :
//
//   · **on n'arbitre pas avant que le vendeur ait pu répondre.** Le bouton est
//     grisé, avec l'échéance dans son infobulle. Sans ce garde-fou, la
//     procédure contradictoire n'est qu'un décor ;
//   · **une décision est toujours motivée**, y compris favorable au client.
//     Le formulaire refuse de partir sans motif — les deux parties liront
//     cette phrase, et elle doit s'expliquer six mois plus tard.
import {
  AlertTriangle, Ban, Eye, Gavel, Scale, Store, Undo2, User,
} from '@lucide/vue'
import { computed, ref } from 'vue'

import { useRafraichissement } from '../../rafraichissement'
import { EchecApi } from '../../api/client'
import { espaces, type Litige } from '../../api/espaces'
import ActionLigne from '../../composants/ActionLigne.vue'
import Liste from '../../composants/Liste.vue'
import type { Colonne } from '../../composants/liste'
import Onglets from '../../composants/Onglets.vue'
import Popup from '../../composants/Popup.vue'
import FicheContextuelle from '../../composants/FicheContextuelle.vue'
import { useNotification } from '../../notifications'

type Ligne = Litige & { [cle: string]: unknown }

const { succes, echec: prevenir } = useNotification()

const litiges = ref<Ligne[]>([])
const chargement = ref(true)
const onglet = ref('ouverts')
const selection = ref<Ligne | null>(null)
// L'oeil ouvre une popup par-dessus la liste (M-1) : le panneau de droite,
// lui, reste le contexte permanent de la ligne active.
const apercu = ref(false)

const arbitrage = ref<Ligne | null>(null)
const decision = ref<'REMBOURSER' | 'REFUSER'>('REMBOURSER')
const motivation = ref('')
const partiel = ref(false)
const montantEuros = ref(0)
const envoi = ref(false)
const erreur = ref('')

async function charger() {
  chargement.value = true
  try {
    const donnees = await espaces.admin.litiges()
    litiges.value = donnees.litiges as Ligne[]
  } finally {
    chargement.value = false
  }
}

useRafraichissement(charger, { periodique: true })

const ouverts = computed(() =>
  litiges.value.filter((d) => ['OUVERT', 'EN_COURS'].includes(d.statut)),
)
const clos = computed(() =>
  litiges.value.filter((d) => ['RESOLU', 'REJETE'].includes(d.statut)),
)
const visibles = computed(() => (onglet.value === 'clos' ? clos.value : ouverts.value))

const euros = (centimes: number) =>
  (centimes / 100).toLocaleString('fr-FR', { style: 'currency', currency: 'EUR' })
const quand = (date: string | null) =>
  date ? new Date(date).toLocaleDateString('fr-FR') : '—'
const quandEtHeure = (date: string | null) =>
  date ? new Date(date).toLocaleString('fr-FR', {
    day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit',
  }) : '—'

const BADGES: Record<string, string> = {
  OUVERT: 'badge-erreur',
  EN_COURS: 'badge-attente',
  RESOLU: 'badge-ok',
  REJETE: 'badge-neutre',
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
  { cle: 'dossier', titre: 'Dossier', champTri: 'id' },
  { cle: 'client', titre: 'Client', champTri: 'client' },
  { cle: 'montant', titre: 'Montant', champTri: 'montant_commande_centimes', aligne: 'droite' },
  { cle: 'instruction', titre: 'Instruction' },
  { cle: 'statut', titre: 'Statut', champTri: 'statut' },
]

/** L'infobulle du bouton d'arbitrage dit POURQUOI il est gris. */
function pourquoiPasEncore(dossier: Ligne) {
  if (dossier.arbitrable) return 'Arbitrer ce dossier'
  return `La boutique a jusqu'au ${quandEtHeure(dossier.date_limite_reponse)} `
    + 'pour donner sa version'
}

function ouvrirArbitrage(dossier: Ligne) {
  arbitrage.value = dossier
  decision.value = 'REMBOURSER'
  motivation.value = ''
  partiel.value = false
  montantEuros.value = dossier.montant_commande_centimes / 100
  erreur.value = ''
}

async function trancher() {
  if (!arbitrage.value) return
  envoi.value = true
  erreur.value = ''
  try {
    await espaces.admin.arbitrer(arbitrage.value.id, {
      decision: decision.value,
      motivation: motivation.value,
      ...(decision.value === 'REMBOURSER' && partiel.value
        ? { montant_centimes: Math.round(montantEuros.value * 100) }
        : {}),
    })
    succes(
      decision.value === 'REMBOURSER' ? 'Litige résolu' : 'Litige rejeté',
      'Le client et la boutique ont été prévenus de la même décision.',
    )
    arbitrage.value = null
    selection.value = null
    await charger()
  } catch (souci) {
    erreur.value = souci instanceof EchecApi ? souci.erreur.message : 'Arbitrage impossible.'
    prevenir('Décision refusée', erreur.value)
  } finally {
    envoi.value = false
  }
}
</script>

<template>
  <div class="mx-auto max-w-[1020px] animate-[apparition_0.2s_ease-out]">
    <Onglets
      v-model="onglet"
      :onglets="[
        { cle: 'ouverts', libelle: 'En instruction', compteur: ouverts.length },
        { cle: 'clos', libelle: 'Dossiers clos', compteur: clos.length },
      ]"
    />

    <Liste
      :colonnes="colonnes"
      :lignes="visibles"
      :cle-ligne="(dossier) => dossier.id"
      :chargement="chargement"
      :recherche="(d) => `${d.id} ${d.client} ${d.commande} ${d.libelle_motif}`"
      :active="(d) => selection?.id === d.id"
      @ligne-cliquee="(d) => (selection = selection?.id === d.id ? null : d)"
      placeholder="Numéro de dossier, client, commande…"
    >
      <template #col-dossier="{ ligne }">
        <span class="flex min-w-0 items-center gap-2">
          <AlertTriangle
            :size="14"
            class="shrink-0"
            :class="ligne.statut === 'OUVERT' ? 'text-alerte' : 'text-encre-douce'"
          />
          <span class="min-w-0">
            <b class="block truncate">N° {{ ligne.id }} — {{ ligne.libelle_motif }}</b>
            <span class="text-[11.2px] text-encre-douce">
              {{ ligne.commande }} · {{ quand(ligne.date_ouverture) }}
            </span>
          </span>
        </span>
      </template>

      <template #col-client="{ ligne }">
        <span class="min-w-0 truncate text-encre-douce">{{ ligne.client }}</span>
      </template>

      <template #col-montant="{ ligne }">
        <b>{{ euros(ligne.montant_commande_centimes) }}</b>
        <span v-if="ligne.montant_rembourse_centimes" class="block text-[11px] text-avis">
          −{{ euros(ligne.montant_rembourse_centimes) }} remboursés
        </span>
      </template>

      <!-- Où en est l'instruction : c'est la colonne qui décide de l'action -->
      <template #col-instruction="{ ligne }">
        <span v-if="ligne.date_reponse_vendeur" class="badge badge-ok">Boutique entendue</span>
        <span v-else-if="ligne.delai_expire" class="badge badge-attente">Délai dépassé</span>
        <span v-else class="badge badge-cours">
          Réponse attendue avant {{ quandEtHeure(ligne.date_limite_reponse) }}
        </span>
      </template>

      <template #col-statut="{ ligne }">
        <span class="badge" :class="BADGES[ligne.statut] ?? 'badge-neutre'">
          {{ ligne.libelle_statut }}
        </span>
      </template>

      <template #actions="{ ligne }">
        <ActionLigne
          titre="Consulter le dossier"
          :icone="Eye"
          :ton="selection?.id === ligne.id ? 'accent' : 'neutre'"
          @click="consulter(ligne)"
        />
        <ActionLigne
          :titre="pourquoiPasEncore(ligne)"
          :icone="Gavel"
          ton="accent"
          :desactive="!ligne.arbitrable || ['RESOLU', 'REJETE'].includes(ligne.statut)"
          @click="ouvrirArbitrage(ligne)"
        />
      </template>

      <template #vide>
        <div class="vide">
          <Scale :size="30" class="text-trait" />
          <b class="vide-titre">
            {{ onglet === 'clos' ? 'Aucun dossier clos' : 'Aucun litige en instruction' }}
          </b>
          <p class="vide-texte">
            Un client ouvre un litige après livraison. Tant qu'il n'y en a pas, c'est que
            les commandes arrivent comme prévu.
          </p>
        </div>
      </template>
    </Liste>

    <!-- Le dossier complet, dans le volet : les deux versions côte à côte -->
    <FicheContextuelle
      v-if="selection"
      :titre="`Litige n° ${selection.id}`"
      :apercu-ouvert="apercu"
      @fermer-apercu="apercu = false"
    >
      <div class="flex flex-col gap-4 p-4 text-[12.5px]">
        <div class="kpi">
          <div class="kpi-nombre">{{ euros(selection.montant_commande_centimes) }}</div>
          <div class="kpi-libelle">Commande {{ selection.commande }}</div>
        </div>

        <dl class="flex flex-col gap-2.5">
          <div class="flex gap-2">
            <dt class="flex w-24 shrink-0 items-center gap-1.5 font-bold text-encre-douce">
              <User :size="12" /> Client
            </dt>
            <dd>{{ selection.client }}</dd>
          </div>
          <div class="flex gap-2">
            <dt class="flex w-24 shrink-0 items-center gap-1.5 font-bold text-encre-douce">
              <Store :size="12" /> Boutique
            </dt>
            <dd>{{ selection.boutiques.join(', ') || '—' }}</dd>
          </div>
        </dl>

        <section class="carte">
          <h4 class="carte-titre"><span>Ce que dit le client</span></h4>
          <p class="px-4 py-3 leading-relaxed">« {{ selection.description }} »</p>
        </section>

        <section class="carte">
          <h4 class="carte-titre"><span>Ce que dit la boutique</span></h4>
          <p v-if="selection.reponse_vendeur" class="px-4 py-3 leading-relaxed">
            « {{ selection.reponse_vendeur }} »
          </p>
          <p v-else class="px-4 py-3 leading-relaxed text-encre-douce">
            {{ selection.delai_expire
              ? 'La boutique n’a pas répondu dans le délai de 48 heures. Vous pouvez '
                + 'trancher avec les éléments dont vous disposez.'
              : `Réponse attendue avant le ${quandEtHeure(selection.date_limite_reponse)}.` }}
          </p>
        </section>

        <section v-if="selection.resolution" class="carte">
          <h4 class="carte-titre"><span>Décision rendue</span></h4>
          <p class="px-4 py-3 leading-relaxed">{{ selection.resolution }}</p>
        </section>

        <button
          v-if="!['RESOLU', 'REJETE'].includes(selection.statut)"
          type="button"
          class="bouton-accent"
          :disabled="!selection.arbitrable"
          :title="pourquoiPasEncore(selection)"
          @click="ouvrirArbitrage(selection)"
        >
          <Gavel :size="15" />
          Arbitrer ce dossier
        </button>
      </div>
    </FicheContextuelle>

    <!-- La décision -->
    <Popup
      v-if="arbitrage"
      :titre="`Arbitrer le litige n° ${arbitrage.id}`"
      explication="Le client et la boutique recevront la même décision, avec votre motivation.
                   Elle doit s'expliquer six mois plus tard."
      @fermer="arbitrage = null"
    >
      <div class="flex flex-col gap-4">
        <div class="flex flex-col gap-2">
          <label
            class="flex cursor-pointer items-start gap-3 rounded-lg border p-3 text-[12.5px]
                   transition-colors"
            :class="decision === 'REMBOURSER' ? 'border-[color:var(--accent)] bg-atelier'
                                              : 'border-trait hover:bg-atelier'"
          >
            <input v-model="decision" type="radio" value="REMBOURSER" class="mt-0.5" />
            <span>
              <b class="flex items-center gap-1.5"><Undo2 :size="13" /> Rembourser le client</b>
              <span class="text-encre-douce">
                Le versement à la boutique est annulé, et le remboursement est tracé.
              </span>
            </span>
          </label>
          <label
            class="flex cursor-pointer items-start gap-3 rounded-lg border p-3 text-[12.5px]
                   transition-colors"
            :class="decision === 'REFUSER' ? 'border-[color:var(--accent)] bg-atelier'
                                           : 'border-trait hover:bg-atelier'"
          >
            <input v-model="decision" type="radio" value="REFUSER" class="mt-0.5" />
            <span>
              <b class="flex items-center gap-1.5"><Ban :size="13" /> Rejeter la réclamation</b>
              <span class="text-encre-douce">
                Le versement à la boutique reprend son cours.
              </span>
            </span>
          </label>
        </div>

        <div v-if="decision === 'REMBOURSER'" class="flex flex-col gap-2">
          <label class="flex items-center gap-2 text-[12.5px]">
            <input v-model="partiel" type="checkbox" />
            Rembourser une partie seulement
          </label>
          <label v-if="partiel" class="flex flex-col gap-1.5">
            <span class="etiquette">
              Montant remboursé (maximum {{ euros(arbitrage.montant_commande_centimes) }})
            </span>
            <input
              v-model.number="montantEuros"
              type="number"
              step="0.01"
              min="0.01"
              :max="arbitrage.montant_commande_centimes / 100"
              class="champ-clair"
            />
          </label>
        </div>

        <label class="flex flex-col gap-1.5">
          <span class="etiquette">Motivation — les deux parties la liront</span>
          <textarea
            v-model="motivation"
            rows="4"
            class="champ-clair"
            placeholder="Ce qui fonde votre décision, en quelques phrases."
          />
        </label>

        <p v-if="!arbitrage.reponse_vendeur" class="bandeau">
          <AlertTriangle :size="15" class="mt-px shrink-0" />
          La boutique n'a pas donné sa version dans le délai imparti. Votre décision
          repose sur les seuls éléments du client, et cela figurera au dossier.
        </p>

        <p v-if="erreur" class="bandeau bandeau-erreur">
          <AlertTriangle :size="15" class="mt-px shrink-0" />
          {{ erreur }}
        </p>
      </div>

      <template #actions>
        <button type="button" class="bouton-neutre" @click="arbitrage = null">Annuler</button>
        <button
          type="button"
          class="bouton-accent"
          :disabled="envoi || motivation.trim().length < 10"
          @click="trancher"
        >
          <Gavel :size="15" />
          {{ envoi ? 'Décision…' : 'Rendre la décision' }}
        </button>
      </template>
    </Popup>
  </div>
</template>
