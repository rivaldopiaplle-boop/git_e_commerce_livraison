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
  AlertTriangle, Bike, Check, ClipboardList, Eye, Package, X,
} from '@lucide/vue'
import { computed, onMounted, ref } from 'vue'

import { commandes, type SousCommande } from '../../api/commandes'
import ActionLigne from '../../composants/ActionLigne.vue'
import Liste from '../../composants/Liste.vue'
import type { Colonne } from '../../composants/liste'
import Onglets from '../../composants/Onglets.vue'
import Volet from '../../composants/Volet.vue'

type Ligne = SousCommande & { [cle: string]: unknown }

const liste = ref<Ligne[]>([])
const chargement = ref(true)
const erreur = ref('')
const onglet = ref('a_faire')
const selection = ref<Ligne | null>(null)
const occupe = ref(false)

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

const LIBELLES: Record<string, string> = {
  EN_PREPARATION: 'Commencer la préparation',
  PRETE: 'Marquer prête',
  EXPEDIEE: 'Expédier',
  ANNULEE: 'Annuler la commande',
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
    selection.value = parEtape(onglet.value)[0] ?? null
  } finally {
    chargement.value = false
  }
}

onMounted(charger)

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

const colonnes: Colonne<Ligne>[] = [
  { cle: 'numero', titre: 'Commande', largeur: 180 },
  { cle: 'articles', titre: 'Contenu' },
  { cle: 'montant', titre: 'Votre part', largeur: 110, aligne: 'droite', masquerSous: 'md',
    champTri: 'montant_vendeur_centimes' },
  { cle: 'statut', titre: 'État', largeur: 120, aligne: 'centre' },
]

const euros = (centimes: number) =>
  (centimes / 100).toLocaleString('fr-FR', { style: 'currency', currency: 'EUR' })
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
        <span class="min-w-0 truncate text-encre-douce">
          {{ ligne.lignes.reduce((total, l) => total + l.quantite, 0) }} article(s) —
          {{ ligne.lignes.map((l) => l.nom_produit_capture).join(', ') }}
        </span>
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
          @click="selection = selection?.id === ligne.id ? null : ligne"
        />
        <ActionLigne
          v-if="suiteNormale(ligne)"
          :titre="LIBELLES[suiteNormale(ligne)!] ?? 'Étape suivante'"
          :icone="Check"
          ton="accent"
          :desactive="occupe"
          @click="avancer(ligne, suiteNormale(ligne)!)"
        />
        <ActionLigne
          v-if="(ligne.suites_possibles ?? []).includes('ANNULEE')"
          titre="Annuler cette commande"
          :icone="X"
          ton="danger"
          :desactive="occupe"
          @click="avancer(ligne, 'ANNULEE')"
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
    <Volet
      v-if="selection"
      :titre="selection.numero_commande ?? `Commande n° ${selection.id}`"
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
          {{ LIBELLES[suiteNormale(selection)!] ?? 'Étape suivante' }}
        </button>
        <p class="mt-2 text-[11px] leading-relaxed text-encre-douce">
          On passe au statut suivant, jamais à un statut choisi librement : c'est le
          serveur qui dit ce qui est possible.
        </p>
      </div>
    </Volet>
  </div>
</template>
