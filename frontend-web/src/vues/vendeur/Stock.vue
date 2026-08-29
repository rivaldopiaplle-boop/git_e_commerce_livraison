<script setup lang="ts">
// L'ecran de stock : un vrai ecran, plus un renvoi vers le catalogue.
//
// Ce que le vendeur y fait vraiment : voir ce qui manque, ajuster, et pouvoir
// expliquer un ecart le lendemain — d'ou le motif obligatoire et l'historique.
import { AlertTriangle, Boxes, Check, History, Search } from '@lucide/vue'
import { computed, onMounted, ref } from 'vue'

import { EchecApi } from '../../api/client'
import { vendeur, type Mouvement } from '../../api/vendeur'
import type { Produit } from '../../composants/CarteProduit.vue'
import Onglets from '../../composants/Onglets.vue'
import Squelette from '../../composants/Squelette.vue'

const produits = ref<Produit[]>([])
const chargement = ref(true)
const onglet = ref('tout')
const filtre = ref('')

const ouvert = ref<number | null>(null)
const mouvements = ref<Mouvement[]>([])
const ajustement = ref({ quantite: '', type: 'AJUSTEMENT', motif: '' })
const erreur = ref('')
const message = ref('')
const occupe = ref(false)

async function charger() {
  chargement.value = true
  try {
    produits.value = await vendeur.mesProduits()
  } finally {
    chargement.value = false
  }
}

onMounted(charger)

const manquants = computed(() => produits.value.filter((p) => !p.disponible))
const visibles = computed(() => {
  const base = onglet.value === 'manquants' ? manquants.value : produits.value
  const recherche = filtre.value.trim().toLowerCase()
  return recherche ? base.filter((p) => p.nom.toLowerCase().includes(recherche)) : base
})

async function ouvrir(produit: Produit) {
  if (ouvert.value === produit.id) {
    ouvert.value = null
    return
  }
  ouvert.value = produit.id
  ajustement.value = { quantite: '', type: 'AJUSTEMENT', motif: '' }
  erreur.value = ''
  message.value = ''
  mouvements.value = await vendeur.stock.mouvements(produit.id)
}

async function appliquer(produit: Produit) {
  erreur.value = ''
  occupe.value = true
  try {
    const resultat = await vendeur.stock.ajuster(
      produit.id,
      Number(ajustement.value.quantite),
      ajustement.value.type,
      ajustement.value.motif,
    )
    mouvements.value = [resultat.mouvement, ...mouvements.value]
    ajustement.value = { quantite: '', type: 'AJUSTEMENT', motif: '' }
    message.value = `Stock a ${resultat.stock_disponible}.`
    await charger()
  } catch (echec) {
    erreur.value = echec instanceof EchecApi ? echec.erreur.message : 'Ajustement refuse.'
  } finally {
    occupe.value = false
  }
}
</script>

<template>
  <div class="mx-auto max-w-[1000px] animate-[apparition_0.2s_ease-out]">
    <Onglets
      v-model="onglet"
      :onglets="[
        { cle: 'tout', libelle: 'Tous les produits', compteur: produits.length },
        { cle: 'manquants', libelle: 'A reapprovisionner', compteur: manquants.length },
      ]"
    />

    <div class="mb-4 flex items-center gap-2 rounded-full bg-papier px-3.5 py-2 ring-1
                ring-trait">
      <Search :size="14" class="text-encre-douce" />
      <input
        v-model="filtre"
        type="search"
        placeholder="Filtrer par nom…"
        class="w-full bg-transparent text-[12.5px] focus:outline-none"
      />
    </div>

    <div v-if="chargement" class="flex flex-col gap-2">
      <Squelette v-for="n in 5" :key="n" hauteur="56px" />
    </div>

    <div v-else-if="!visibles.length" class="carte p-10 text-center">
      <span
        class="mx-auto flex h-12 w-12 items-center justify-center rounded-lg"
        :style="{ background: 'var(--accent-doux)', color: 'var(--accent)' }"
      >
        <Boxes :size="20" />
      </span>
      <b class="mt-3 block text-[14px]">
        {{ onglet === 'manquants' ? 'Rien a reapprovisionner' : 'Aucun produit' }}
      </b>
    </div>

    <div v-else class="carte">
      <template v-for="produit in visibles" :key="produit.id">
        <div class="ligne">
          <img
            v-if="produit.image"
            :src="produit.image"
            :alt="produit.nom"
            class="h-10 w-10 rounded-lg object-cover"
          />
          <span class="min-w-0 flex-1">
            <b class="block truncate">{{ produit.nom }}</b>
            <span class="text-[11.2px] text-encre-douce">{{ produit.boutique.nom }}</span>
          </span>

          <span v-if="!produit.disponible" class="badge badge-erreur">
            <AlertTriangle :size="10" class="mr-1 inline" /> rupture
          </span>
          <span v-else class="badge badge-ok">en stock</span>

          <button type="button" class="bouton-icone" title="Ajuster le stock"
                  @click="ouvrir(produit)">
            <Boxes :size="16" />
            <span class="sr-only">Ajuster le stock</span>
          </button>
        </div>

        <!-- Le detail se deplie sous la ligne : on ne quitte pas la liste -->
        <div v-if="ouvert === produit.id" class="border-b border-trait-doux bg-atelier px-4 py-4">
          <form class="flex flex-wrap items-end gap-2.5" @submit.prevent="appliquer(produit)">
            <label class="flex w-24 flex-col gap-1">
              <span class="text-[11.5px] font-semibold text-encre-douce">Quantite</span>
              <input v-model="ajustement.quantite" required placeholder="+5 / -2"
                     class="champ-clair !py-1.5 !text-[12.5px]" />
            </label>
            <label class="flex w-40 flex-col gap-1">
              <span class="text-[11.5px] font-semibold text-encre-douce">Type</span>
              <select v-model="ajustement.type" class="champ-clair !py-1.5 !text-[12.5px]">
                <option value="REAPPRO">Reapprovisionnement</option>
                <option value="AJUSTEMENT">Ajustement manuel</option>
                <option value="RETOUR">Retour</option>
              </select>
            </label>
            <label class="flex min-w-[180px] flex-1 flex-col gap-1">
              <span class="text-[11.5px] font-semibold text-encre-douce">
                Motif
                <span v-if="ajustement.type === 'AJUSTEMENT'" class="text-[#9c2116]">
                  obligatoire
                </span>
              </span>
              <input
                v-model="ajustement.motif"
                :required="ajustement.type === 'AJUSTEMENT'"
                placeholder="Casse, inventaire…"
                class="champ-clair !py-1.5 !text-[12.5px]"
              />
            </label>
            <button type="submit" class="bouton-accent !py-2" :disabled="occupe">
              <Check :size="15" /> Appliquer
            </button>
          </form>

          <p v-if="erreur" class="mt-2.5 text-[12px] text-[#9c2116]">{{ erreur }}</p>
          <p v-if="message" class="mt-2.5 text-[12px] text-[#116b34]">{{ message }}</p>

          <div v-if="mouvements.length" class="mt-4">
            <b class="flex items-center gap-1.5 text-[11.5px] tracking-wider text-encre-douce
                      uppercase">
              <History :size="12" /> Historique
            </b>
            <div class="mt-2 flex flex-col gap-1">
              <div
                v-for="mouvement in mouvements.slice(0, 6)"
                :key="mouvement.id"
                class="flex items-center gap-3 text-[12px]"
              >
                <span class="w-32 text-encre-douce">
                  {{ new Date(mouvement.date_mouvement).toLocaleDateString('fr-FR') }}
                </span>
                <span class="w-40">{{ mouvement.libelle_type }}</span>
                <span
                  class="w-12 font-bold"
                  :class="mouvement.quantite > 0 ? 'text-[#116b34]' : 'text-[#9c2116]'"
                >
                  {{ mouvement.quantite > 0 ? '+' : '' }}{{ mouvement.quantite }}
                </span>
                <span class="w-16 text-encre-douce">→ {{ mouvement.stock_apres }}</span>
                <span class="flex-1 truncate text-encre-douce">{{ mouvement.motif || '—' }}</span>
                <span class="text-encre-douce">{{ mouvement.auteur }}</span>
              </div>
            </div>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>
