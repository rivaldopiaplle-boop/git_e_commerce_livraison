<script setup lang="ts">
// Les comptes de la plateforme.
//
// Suspendre, jamais supprimer : les commandes passees referencent ce compte,
// et une plateforme qui efface ses utilisateurs efface ses preuves (D-13).
// Le bouton dit donc « suspendre », et il se rejoue en sens inverse.
import { Ban, RotateCcw, Search, Users } from '@lucide/vue'
import { computed, onMounted, ref } from 'vue'

import { EchecApi } from '../../api/client'
import { espaces, type CompteAdmin } from '../../api/espaces'
import Onglets from '../../composants/Onglets.vue'
import Squelette from '../../composants/Squelette.vue'

const comptes = ref<CompteAdmin[]>([])
const repartition = ref<{ role: string; nombre: number }[]>([])
const chargement = ref(true)
const recherche = ref('')
const onglet = ref('TOUS')
const erreur = ref('')
const occupe = ref(false)

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
    comptes.value = donnees.utilisateurs
    repartition.value = donnees.repartition
  } finally {
    chargement.value = false
  }
}

onMounted(charger)

const visibles = computed(() => {
  const texte = recherche.value.trim().toLowerCase()
  return comptes.value.filter((compte) => {
    if (onglet.value !== 'TOUS' && compte.role !== onglet.value) return false
    if (!texte) return true
    return `${compte.prenom} ${compte.nom} ${compte.email} ${compte.rattachement}`
      .toLowerCase()
      .includes(texte)
  })
})

const compteur = (role: string) =>
  repartition.value.find((entree) => entree.role === role)?.nombre ?? 0

async function basculer(compte: CompteAdmin) {
  erreur.value = ''
  occupe.value = true
  try {
    const resultat = await espaces.admin.suspendre(compte.id)
    compte.statut_compte = resultat.statut_compte
  } catch (echec) {
    erreur.value = echec instanceof EchecApi ? echec.erreur.message : "L action a echoue."
  } finally {
    occupe.value = false
  }
}

const quand = (date: string) => new Date(date).toLocaleDateString('fr-FR')
</script>

<template>
  <div class="mx-auto max-w-[1060px] animate-[apparition_0.2s_ease-out]">
    <Onglets
      v-model="onglet"
      :onglets="[
        { cle: 'TOUS', libelle: 'Tous', compteur: comptes.length },
        ...Object.entries(LIBELLES).map(([cle, libelle]) => ({
          cle, libelle, compteur: compteur(cle),
        })),
      ]"
    />

    <div class="mb-4 flex items-center gap-2 rounded-full bg-papier px-3.5 py-2 ring-1
                ring-trait">
      <Search :size="14" class="text-encre-douce" />
      <input
        v-model="recherche"
        type="search"
        placeholder="Nom, adresse e-mail, boutique…"
        class="w-full bg-transparent text-[12.5px] focus:outline-none"
      />
    </div>

    <p v-if="erreur" class="bandeau bandeau-erreur mb-3">{{ erreur }}</p>

    <div v-if="chargement" class="flex flex-col gap-2">
      <Squelette v-for="n in 6" :key="n" hauteur="52px" />
    </div>

    <div v-else-if="!visibles.length" class="carte">
      <div class="vide">
        <Users :size="30" class="text-trait" />
        <b class="vide-titre">Aucun compte ne correspond</b>
      </div>
    </div>

    <div v-else class="carte">
      <div v-for="compte in visibles" :key="compte.id" class="ligne">
        <span
          class="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-atelier
                 text-[11.5px] font-bold text-encre-douce"
        >
          {{ compte.prenom.charAt(0).toUpperCase() }}
        </span>
        <span class="min-w-0 flex-1">
          <b class="block truncate">{{ compte.prenom }} {{ compte.nom }}</b>
          <span class="text-[11.2px] text-encre-douce">{{ compte.email }}</span>
        </span>
        <span class="hidden w-40 truncate text-encre-douce md:block">
          {{ compte.rattachement || '—' }}
        </span>
        <span class="badge badge-neutre w-[104px] justify-center">
          {{ LIBELLES[compte.role] ?? compte.role }}
        </span>
        <span class="badge w-[112px] justify-center"
              :class="STATUTS[compte.statut_compte] ?? 'badge-neutre'">
          {{ compte.statut_compte.toLowerCase().replace(/_/g, ' ') }}
        </span>
        <span class="hidden w-20 text-right text-[11.5px] text-encre-douce lg:block">
          {{ quand(compte.date_inscription) }}
        </span>
        <button
          v-if="compte.role !== 'ADMIN'"
          type="button"
          class="bouton-ligne"
          :class="compte.statut_compte === 'SUSPENDU' ? 'bouton-ligne-accent'
                                                       : 'bouton-ligne-danger'"
          :title="compte.statut_compte === 'SUSPENDU' ? 'Reactiver ce compte'
                                                      : 'Suspendre ce compte'"
          :disabled="occupe"
          @click="basculer(compte)"
        >
          <component :is="compte.statut_compte === 'SUSPENDU' ? RotateCcw : Ban" :size="14" />
          <span class="sr-only">
            {{ compte.statut_compte === 'SUSPENDU' ? 'Reactiver' : 'Suspendre' }}
          </span>
        </button>
        <span v-else class="w-7" />
      </div>
    </div>
  </div>
</template>
