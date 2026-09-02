<script setup lang="ts">
// Les comptes de la plateforme.
//
// Suspendre, jamais supprimer : les commandes passées référencent ce compte,
// et une plateforme qui efface ses utilisateurs efface ses preuves (D-13).
// Le bouton dit donc « suspendre », et il se rejoue en sens inverse.
import { Ban, Eye, RotateCcw, Users } from '@lucide/vue'
import { computed, onMounted, ref } from 'vue'

import { EchecApi } from '../../api/client'
import { useNotification } from '../../notifications'
import { espaces, type CompteAdmin } from '../../api/espaces'
import Button from 'primevue/button'
import Textarea from 'primevue/textarea'

import ActionLigne from '../../composants/ActionLigne.vue'
import Liste from '../../composants/Liste.vue'
import type { Colonne } from '../../composants/liste'
import Onglets from '../../composants/Onglets.vue'
import Popup from '../../composants/Popup.vue'
import FicheContextuelle from '../../composants/FicheContextuelle.vue'

type Ligne = CompteAdmin & { [cle: string]: unknown }

const notifier = useNotification()
const comptes = ref<Ligne[]>([])
const repartition = ref<{ role: string; nombre: number }[]>([])
const chargement = ref(true)
const onglet = ref('TOUS')
const occupe = ref(false)
const selection = ref<Ligne | null>(null)
// L'oeil ouvre une popup par-dessus la liste (M-1) : le panneau de droite,
// lui, reste le contexte permanent de la ligne active.
const apercu = ref(false)

const LIBELLES: Record<string, string> = {
  CLIENT: 'Clients',
  VENDEUR: 'Vendeurs',
  GESTIONNAIRE: 'Gestionnaires',
  LIVREUR: 'Livreurs',
  ADMIN: 'Admins',
}

const STATUTS: Record<string, string> = {
  ACTIF: 'badge-ok',
  EN_ATTENTE_VALIDATION: 'badge-attente',
  SUSPENDU: 'badge-erreur',
  DESACTIVE: 'badge-neutre',
}

async function charger() {
  chargement.value = true
  try {
    const donnees = await espaces.admin.utilisateurs()
    comptes.value = donnees.utilisateurs as Ligne[]
    repartition.value = donnees.repartition
  } finally {
    chargement.value = false
  }
}

onMounted(charger)

const visibles = computed(() =>
  onglet.value === 'TOUS'
    ? comptes.value
    : comptes.value.filter((compte) => compte.role === onglet.value),
)

const compteur = (role: string) =>
  repartition.value.find((entree) => entree.role === role)?.nombre ?? 0

// Suspendre exige un motif : la personne doit savoir ce qu'on lui reproche,
// et elle en est prevenue (D-93). Reactiver n'en demande pas.
const bascule = ref<Ligne | null>(null)
const motif = ref('')

function ouvrirBascule(compte: Ligne) {
  bascule.value = compte
  motif.value = ''
  if (compte.statut_compte === 'SUSPENDU') basculer()
}

async function basculer() {
  const compte = bascule.value
  if (!compte) return
  occupe.value = true
  try {
    const resultat = await espaces.admin.basculerCompte(compte.id, motif.value)
    compte.statut_compte = resultat.statut_compte
    notifier.succes(
      resultat.statut_compte === 'SUSPENDU'
        ? `Le compte de ${compte.prenom} ${compte.nom} est suspendu, et la personne est prévenue.`
        : `Le compte de ${compte.prenom} ${compte.nom} est réactivé.`,
    )
    bascule.value = null
  } catch (echec) {
    notifier.echec(echec instanceof EchecApi ? echec.erreur.message : "L'action a échoué.")
  } finally {
    occupe.value = false
  }
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
  { cle: 'personne', titre: 'Personne', champTri: 'nom' },
  { cle: 'rattachement', titre: 'Rattachement', masquerSous: 'md' },
  { cle: 'role', titre: 'Rôle', largeur: 116, aligne: 'centre' },
  { cle: 'statut', titre: 'Statut', largeur: 124, aligne: 'centre' },
  { cle: 'inscription', titre: 'Inscrit le', largeur: 96, aligne: 'droite', masquerSous: 'lg',
    champTri: 'date_inscription' },
]

const quand = (date: string) => new Date(date).toLocaleDateString('fr-FR')
const lisible = (statut: string) => statut.toLowerCase().replace(/_/g, ' ')
</script>

<template>
  <div class="mx-auto max-w-[1080px] animate-[apparition_0.2s_ease-out]">
    <Onglets
      v-model="onglet"
      :onglets="[
        { cle: 'TOUS', libelle: 'Tous', compteur: comptes.length },
        ...Object.entries(LIBELLES).map(([cle, libelle]) => ({
          cle, libelle, compteur: compteur(cle),
        })),
      ]"
    />

    <Liste
      :colonnes="colonnes"
      :lignes="visibles"
      :cle-ligne="(compte) => compte.id"
      :chargement="chargement"
      :recherche="(c) => `${c.prenom} ${c.nom} ${c.email} ${c.rattachement}`"
      :active="(c) => selection?.id === c.id"
      @ligne-cliquee="(c) => (selection = selection?.id === c.id ? null : c)"
      placeholder="Nom, adresse e-mail, boutique…"
      :par-page="15"
    >
      <template #col-personne="{ ligne }">
        <span class="flex min-w-0 items-center gap-2.5">
          <span
            class="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-atelier
                   text-[11.5px] font-bold text-encre-douce"
          >
            {{ ligne.prenom.charAt(0).toUpperCase() }}
          </span>
          <span class="min-w-0">
            <b class="block truncate">{{ ligne.prenom }} {{ ligne.nom }}</b>
            <span class="text-[11.2px] text-encre-douce">{{ ligne.email }}</span>
          </span>
        </span>
      </template>
      <template #col-rattachement="{ ligne }">
        <span class="min-w-0 truncate text-encre-douce">{{ ligne.rattachement || '—' }}</span>
      </template>
      <template #col-role="{ ligne }">
        <span class="badge badge-neutre">{{ LIBELLES[ligne.role] ?? ligne.role }}</span>
      </template>
      <template #col-statut="{ ligne }">
        <span class="badge" :class="STATUTS[ligne.statut_compte] ?? 'badge-neutre'">
          {{ lisible(ligne.statut_compte) }}
        </span>
      </template>
      <template #col-inscription="{ ligne }">
        <span class="text-[11.5px] text-encre-douce">{{ quand(ligne.date_inscription) }}</span>
      </template>

      <template #actions="{ ligne }">
        <ActionLigne
          titre="Consulter ce compte"
          :icone="Eye"
          :ton="selection?.id === ligne.id ? 'accent' : 'neutre'"
          @click="consulter(ligne)"
        />
        <ActionLigne
          :titre="ligne.statut_compte === 'SUSPENDU' ? 'Réactiver ce compte'
                                                     : 'Suspendre ce compte'"
          :icone="ligne.statut_compte === 'SUSPENDU' ? RotateCcw : Ban"
          :ton="ligne.statut_compte === 'SUSPENDU' ? 'accent' : 'danger'"
          :desactive="occupe || ligne.role === 'ADMIN'"
          @click="ouvrirBascule(ligne)"
        />
      </template>

      <template #vide>
        <div class="vide">
          <Users :size="30" class="text-trait" />
          <b class="vide-titre">Aucun compte ne correspond</b>
        </div>
      </template>
    </Liste>

    <FicheContextuelle
      v-if="selection"
      :titre="`${selection.prenom} ${selection.nom}`"
      :apercu-ouvert="apercu"
      @fermer-apercu="apercu = false"
    >
      <dl class="flex flex-col gap-2 text-[12px]">
        <div>
          <dt class="text-encre-douce">Adresse e-mail</dt>
          <dd class="font-semibold break-all">{{ selection.email }}</dd>
        </div>
        <div class="flex justify-between gap-2">
          <dt class="text-encre-douce">Rôle</dt>
          <dd><span class="badge badge-neutre">{{ LIBELLES[selection.role] ?? selection.role }}</span></dd>
        </div>
        <div class="flex justify-between gap-2">
          <dt class="text-encre-douce">Statut</dt>
          <dd>
            <span class="badge" :class="STATUTS[selection.statut_compte] ?? 'badge-neutre'">
              {{ lisible(selection.statut_compte) }}
            </span>
          </dd>
        </div>
        <div v-if="selection.rattachement">
          <dt class="text-encre-douce">Rattachement</dt>
          <dd class="font-semibold">{{ selection.rattachement }}</dd>
        </div>
        <div class="flex justify-between gap-2">
          <dt class="text-encre-douce">Inscrit le</dt>
          <dd class="font-semibold">{{ quand(selection.date_inscription) }}</dd>
        </div>
      </dl>

      <button
        v-if="selection.role !== 'ADMIN'"
        type="button"
        class="mt-4 w-full"
        :class="selection.statut_compte === 'SUSPENDU' ? 'bouton-accent' : 'bouton-neutre'"
        :disabled="occupe"
        @click="ouvrirBascule(selection)"
      >
        <component :is="selection.statut_compte === 'SUSPENDU' ? RotateCcw : Ban" :size="15" />
        {{ selection.statut_compte === 'SUSPENDU' ? 'Réactiver le compte'
                                                  : 'Suspendre le compte' }}
      </button>

      <p class="mt-3 text-[11px] leading-relaxed text-encre-douce">
        Un compte n'est jamais supprimé : ses commandes passées le référencent, et une
        plateforme qui efface ses utilisateurs efface ses preuves.
      </p>
    </FicheContextuelle>

    <!-- Suspendre est reversible mais coupe l'acces immediatement : on
         confirme, et on explique ce qui va se passer (D-60, D-63). -->
    <Popup
      v-if="bascule && bascule.statut_compte !== 'SUSPENDU'"
      titre="Suspendre ce compte ?"
      :explication="`${bascule.prenom} ${bascule.nom} sera deconnecte immediatement et ne pourra plus entrer. Ses commandes et ses traces restent : rien n'est efface. Vous pourrez le reactiver a tout moment.`"
      @fermer="bascule = null"
    >
      <label class="flex flex-col gap-1.5">
        <span class="etiquette">Motif <span class="text-alerte">obligatoire</span></span>
        <Textarea
          v-model="motif"
          rows="3"
          auto-resize
          placeholder="Verification anti-fraude, signalements repetes…"
        />
      </label>

      <template #actions>
        <Button label="Annuler" severity="secondary" outlined size="small"
                @click="bascule = null" />
        <Button label="Suspendre le compte" severity="danger" size="small"
                :disabled="occupe || !motif.trim()" @click="basculer" />
      </template>
    </Popup>
  </div>
</template>
