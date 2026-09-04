<script setup lang="ts">
// Les demandes de correction d'identité, arbitrées par l'administration.
//
// C'est l'autre bout de D-77 : si l'identité est gelée côté utilisateur, il
// faut bien que quelqu'un puisse la corriger quand elle est fausse. Sans cet
// écran, le gel serait une impasse.
//
// Accepter **applique** la correction. Une acceptation qui obligerait
// l'administrateur à recopier la valeur à la main finirait par produire des
// fautes de frappe — donc des identités fausses validées par l'administration.
import { ArrowRight, BadgeCheck, Check, X } from '@lucide/vue'
import Button from 'primevue/button'
import Tag from 'primevue/tag'
import Textarea from 'primevue/textarea'
import { computed, ref } from 'vue'

import { useRafraichissement } from '../../rafraichissement'
import { profil as api, type Demande } from '../../api/espaces'
import ActionLigne from '../../composants/ActionLigne.vue'
import Liste from '../../composants/Liste.vue'
import type { Colonne } from '../../composants/liste'
import Onglets from '../../composants/Onglets.vue'
import Popup from '../../composants/Popup.vue'
import Volet from '../../composants/Volet.vue'
import { useNotification } from '../../notifications'

type Ligne = Demande & { [cle: string]: unknown }

const notifier = useNotification()
const demandes = ref<Ligne[]>([])
const chargement = ref(true)
const occupe = ref(false)
const onglet = ref('EN_ATTENTE')
const selection = ref<Ligne | null>(null)

const arbitrage = ref<{ demande: Ligne; accepter: boolean } | null>(null)
const commentaire = ref('')

async function charger() {
  chargement.value = true
  try {
    const donnees = await api.demandesAArbitrer()
    demandes.value = donnees.demandes as Ligne[]
    selection.value = demandes.value.find((d) => d.statut === 'EN_ATTENTE') ?? null
  } finally {
    chargement.value = false
  }
}

useRafraichissement(charger)

const visibles = computed(() =>
  onglet.value === 'TOUTES'
    ? demandes.value
    : demandes.value.filter((demande) => demande.statut === onglet.value),
)
const compteur = (statut: string) =>
  demandes.value.filter((demande) => demande.statut === statut).length

const TONS: Record<string, 'success' | 'warn' | 'danger'> = {
  ACCEPTEE: 'success',
  EN_ATTENTE: 'warn',
  REFUSEE: 'danger',
}

function ouvrir(demande: Ligne, accepter: boolean) {
  arbitrage.value = { demande, accepter }
  commentaire.value = accepter ? 'Pièce justificative fournie et vérifiée.' : ''
}

async function trancher() {
  if (!arbitrage.value) return
  occupe.value = true
  try {
    await api.arbitrer(
      arbitrage.value.demande.id,
      arbitrage.value.accepter,
      commentaire.value,
    )
    notifier.succes(
      arbitrage.value.accepter
        ? 'Correction appliquée, et le demandeur est prévenu.'
        : 'Demande refusée, avec votre motif.',
    )
    arbitrage.value = null
    await charger()
  } catch (echec) {
    notifier.echec(echec)
  } finally {
    occupe.value = false
  }
}

const colonnes: Colonne<Ligne>[] = [
  { cle: 'demandeur', titre: 'Demandeur' },
  { cle: 'champs', titre: 'Ce qui doit changer' },
  { cle: 'depuis', titre: 'Déposée le', largeur: 110, aligne: 'droite', masquerSous: 'md',
    champTri: 'date_demande' },
  { cle: 'statut', titre: 'État', largeur: 110, aligne: 'centre' },
]

const quand = (date: string | null) =>
  date ? new Date(date).toLocaleDateString('fr-FR') : '—'
</script>

<template>
  <div class="mx-auto max-w-[1020px] animate-[apparition_0.2s_ease-out]">
    <Onglets
      v-model="onglet"
      :onglets="[
        { cle: 'EN_ATTENTE', libelle: 'À arbitrer', compteur: compteur('EN_ATTENTE') },
        { cle: 'ACCEPTEE', libelle: 'Acceptées', compteur: compteur('ACCEPTEE') },
        { cle: 'REFUSEE', libelle: 'Refusées', compteur: compteur('REFUSEE') },
        { cle: 'TOUTES', libelle: 'Toutes', compteur: demandes.length },
      ]"
    />

    <Liste
      :colonnes="colonnes"
      :lignes="visibles"
      :cle-ligne="(demande) => demande.id"
      :chargement="chargement"
      :recherche="(d) => `${d.demandeur.nom} ${d.demandeur.email} ${d.motif}`"
      :active="(d) => selection?.id === d.id"
      placeholder="Nom, adresse e-mail, motif…"
      @ligne-cliquee="(d) => (selection = selection?.id === d.id ? null : d)"
    >
      <template #col-demandeur="{ ligne }">
        <span class="min-w-0">
          <b class="block truncate">{{ ligne.demandeur.nom }}</b>
          <span class="text-[11.2px] text-encre-douce">{{ ligne.demandeur.email }}</span>
        </span>
      </template>
      <template #col-champs="{ ligne }">
        <span class="flex min-w-0 flex-wrap items-center gap-1.5">
          <span
            v-for="champ in ligne.champs"
            :key="champ.champ"
            class="flex items-center gap-1 text-[11.5px]"
          >
            <span class="text-encre-douce line-through">{{ champ.valeur_actuelle || '—' }}</span>
            <ArrowRight :size="10" class="text-encre-douce" />
            <b>{{ champ.valeur_demandee }}</b>
          </span>
        </span>
      </template>
      <template #col-depuis="{ ligne }">
        <span class="text-encre-douce">{{ quand(ligne.date_demande) }}</span>
      </template>
      <template #col-statut="{ ligne }">
        <Tag :value="ligne.libelle_statut" :severity="TONS[ligne.statut] ?? 'secondary'" />
      </template>

      <template #actions="{ ligne }">
        <ActionLigne
          titre="Accepter et appliquer la correction"
          :icone="Check"
          ton="accent"
          :desactive="occupe || ligne.statut !== 'EN_ATTENTE'"
          @click="ouvrir(ligne, true)"
        />
        <ActionLigne
          titre="Refuser cette demande"
          :icone="X"
          ton="danger"
          :desactive="occupe || ligne.statut !== 'EN_ATTENTE'"
          @click="ouvrir(ligne, false)"
        />
      </template>

      <template #vide>
        <div class="vide">
          <BadgeCheck :size="30" class="text-trait" />
          <b class="vide-titre">Aucune demande à cet état</b>
          <p class="vide-texte">
            Nom, prénom et date de naissance sont gelés : les corriger passe par ici.
          </p>
        </div>
      </template>
    </Liste>

    <Volet v-if="selection" :titre="selection.demandeur.nom">
      <dl class="flex flex-col gap-2.5 text-[12px]">
        <div>
          <dt class="text-encre-douce">Compte</dt>
          <dd class="font-semibold break-all">{{ selection.demandeur.email }}</dd>
          <dd class="text-encre-douce">{{ selection.demandeur.role.toLowerCase() }}</dd>
        </div>
        <div>
          <dt class="text-encre-douce">Ce qui doit changer</dt>
          <dd v-for="champ in selection.champs" :key="champ.champ" class="mt-1">
            <span class="etiquette">{{ champ.libelle }}</span>
            <span class="mt-0.5 flex items-center gap-1.5">
              <span class="text-encre-douce line-through">{{ champ.valeur_actuelle || '—' }}</span>
              <ArrowRight :size="11" />
              <b>{{ champ.valeur_demandee }}</b>
            </span>
          </dd>
        </div>
        <div v-if="selection.motif">
          <dt class="text-encre-douce">Motif invoqué</dt>
          <dd class="leading-relaxed">« {{ selection.motif }} »</dd>
        </div>
        <div v-if="selection.commentaire_decision">
          <dt class="text-encre-douce">Votre décision</dt>
          <dd class="leading-relaxed">{{ selection.commentaire_decision }}</dd>
        </div>
      </dl>

      <div v-if="selection.statut === 'EN_ATTENTE'" class="mt-4 flex flex-col gap-2">
        <Button label="Accepter et appliquer" size="small" :disabled="occupe"
                @click="ouvrir(selection, true)" />
        <Button label="Refuser" severity="danger" outlined size="small" :disabled="occupe"
                @click="ouvrir(selection, false)" />
      </div>
    </Volet>

    <!-- Un arbitrage est irréversible : on confirme et on explique (D-60) -->
    <Popup
      v-if="arbitrage"
      :titre="arbitrage.accepter ? 'Accepter cette correction ?' : 'Refuser cette demande ?'"
      :explication="arbitrage.accepter
        ? `L'identité de ${arbitrage.demande.demandeur.nom} sera modifiée immédiatement, et la personne prévenue. Cette décision ne se rejoue pas.`
        : `${arbitrage.demande.demandeur.nom} recevra votre motif. Elle pourra déposer une nouvelle demande ensuite.`"
      @fermer="arbitrage = null"
    >
      <label class="flex flex-col gap-1.5">
        <span class="etiquette">
          Commentaire
          <span v-if="!arbitrage.accepter" class="text-alerte">obligatoire</span>
        </span>
        <Textarea
          v-model="commentaire"
          rows="3"
          auto-resize
          :placeholder="arbitrage.accepter
            ? 'Pièce justificative vérifiée…'
            : 'Expliquez ce qui manque pour que la demande puisse aboutir.'"
        />
      </label>

      <template #actions>
        <Button label="Annuler" severity="secondary" outlined size="small"
                @click="arbitrage = null" />
        <Button
          :label="arbitrage.accepter ? 'Accepter et appliquer' : 'Refuser'"
          :severity="arbitrage.accepter ? undefined : 'danger'"
          size="small"
          :disabled="occupe || (!arbitrage.accepter && !commentaire.trim())"
          @click="trancher"
        />
      </template>
    </Popup>
  </div>
</template>
