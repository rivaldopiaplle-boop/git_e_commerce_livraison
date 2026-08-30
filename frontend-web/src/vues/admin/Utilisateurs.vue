<script setup lang="ts">
// Les comptes de la plateforme.
//
// Suspendre, jamais supprimer : les commandes passées référencent ce compte,
// et une plateforme qui efface ses utilisateurs efface ses preuves (D-13).
// Le bouton dit donc « suspendre », et il se rejoue en sens inverse.
import { Ban, Eye, RotateCcw, Users } from '@lucide/vue'
import { computed, onMounted, ref } from 'vue'

import { EchecApi } from '../../api/client'
import { espaces, type CompteAdmin } from '../../api/espaces'
import ActionLigne from '../../composants/ActionLigne.vue'
import Liste from '../../composants/Liste.vue'
import type { Colonne } from '../../composants/liste'
import Onglets from '../../composants/Onglets.vue'
import Volet from '../../composants/Volet.vue'

type Ligne = CompteAdmin & { [cle: string]: unknown }

const comptes = ref<Ligne[]>([])
const repartition = ref<{ role: string; nombre: number }[]>([])
const chargement = ref(true)
const onglet = ref('TOUS')
const erreur = ref('')
const occupe = ref(false)
const selection = ref<Ligne | null>(null)

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

async function basculer(compte: Ligne) {
  erreur.value = ''
  occupe.value = true
  try {
    const resultat = await espaces.admin.suspendre(compte.id)
    compte.statut_compte = resultat.statut_compte
  } catch (echec) {
    erreur.value = echec instanceof EchecApi ? echec.erreur.message : "L'action a échoué."
  } finally {
    occupe.value = false
  }
}

const colonnes: Colonne<Ligne>[] = [
  { cle: 'personne', titre: 'Personne', tri: (a, b) => a.nom.localeCompare(b.nom) },
  { cle: 'rattachement', titre: 'Rattachement', masquerSous: 'md' },
  { cle: 'role', titre: 'Rôle', largeur: 116, aligne: 'centre' },
  { cle: 'statut', titre: 'Statut', largeur: 124, aligne: 'centre' },
  { cle: 'inscription', titre: 'Inscrit le', largeur: 96, aligne: 'droite', masquerSous: 'lg',
    tri: (a, b) => a.date_inscription.localeCompare(b.date_inscription) },
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

    <p v-if="erreur" class="bandeau bandeau-erreur mb-3">{{ erreur }}</p>

    <Liste
      :colonnes="colonnes"
      :lignes="visibles"
      :cle-ligne="(compte) => compte.id"
      :chargement="chargement"
      :recherche="(c) => `${c.prenom} ${c.nom} ${c.email} ${c.rattachement}`"
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
          @click="selection = selection?.id === ligne.id ? null : ligne"
        />
        <ActionLigne
          :titre="ligne.statut_compte === 'SUSPENDU' ? 'Réactiver ce compte'
                                                     : 'Suspendre ce compte'"
          :icone="ligne.statut_compte === 'SUSPENDU' ? RotateCcw : Ban"
          :ton="ligne.statut_compte === 'SUSPENDU' ? 'accent' : 'danger'"
          :desactive="occupe || ligne.role === 'ADMIN'"
          @click="basculer(ligne)"
        />
      </template>

      <template #vide>
        <div class="vide">
          <Users :size="30" class="text-trait" />
          <b class="vide-titre">Aucun compte ne correspond</b>
        </div>
      </template>
    </Liste>

    <Volet v-if="selection" :titre="`${selection.prenom} ${selection.nom}`">
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
        @click="basculer(selection)"
      >
        <component :is="selection.statut_compte === 'SUSPENDU' ? RotateCcw : Ban" :size="15" />
        {{ selection.statut_compte === 'SUSPENDU' ? 'Réactiver le compte'
                                                  : 'Suspendre le compte' }}
      </button>

      <p class="mt-3 text-[11px] leading-relaxed text-encre-douce">
        Un compte n'est jamais supprimé : ses commandes passées le référencent, et une
        plateforme qui efface ses utilisateurs efface ses preuves.
      </p>
    </Volet>
  </div>
</template>
