<script setup lang="ts">
// Le carnet d'adresses du client.
//
// L'entree existait dans la barre laterale et ne menait nulle part. Elle
// compte pourtant : c'est l'adresse qui decide quelles boutiques Express
// apparaissent au catalogue (D-09), et le client doit pouvoir en changer
// sans passer par le tunnel de commande.
import { Check, Home, MapPin, Plus, Star, Trash2 } from '@lucide/vue'
import { onMounted, ref } from 'vue'

import { EchecApi } from '../../api/client'
import { useNotification } from '../../notifications'
import { espaces, type Adresse } from '../../api/espaces'
import Popup from '../../composants/Popup.vue'
import Squelette from '../../composants/Squelette.vue'

const notifier = useNotification()
const adresses = ref<Adresse[]>([])
const chargement = ref(true)
const erreur = ref('')
const occupe = ref(false)
const ajout = ref(false)

const nouvelle = ref({
  libelle: 'Domicile', rue: '', complement: '', code_postal: '', ville: '',
  instructions_livraison: '',
})

async function charger() {
  chargement.value = true
  try {
    adresses.value = await espaces.client.adresses()
  } finally {
    chargement.value = false
  }
}

onMounted(charger)

async function agir(action: Promise<Adresse[]>, reussite?: string) {
  erreur.value = ''
  occupe.value = true
  try {
    adresses.value = await action
    if (reussite) notifier.succes(reussite)
  } catch (echec) {
    erreur.value = echec instanceof EchecApi ? echec.erreur.message : "L'action a échoué."
    notifier.echec(erreur.value)
  } finally {
    occupe.value = false
  }
}

async function ajouter() {
  await agir(espaces.client.ajouterAdresse(nouvelle.value), 'Adresse ajoutee a votre carnet.')
  if (!erreur.value) {
    ajout.value = false
    nouvelle.value = {
      libelle: 'Domicile', rue: '', complement: '', code_postal: '', ville: '',
      instructions_livraison: '',
    }
  }
}
</script>

<template>
  <div class="mx-auto max-w-[760px] animate-[apparition_0.2s_ease-out]">
    <div class="mb-4 flex items-center justify-between gap-3">
      <p class="text-[12.5px] text-encre-douce">
        L adresse principale sert a filtrer le catalogue Express : seules les boutiques
        qui livrent chez vous y apparaissent.
      </p>
      <button type="button" class="bouton-accent shrink-0" @click="ajout = true">
        <Plus :size="15" />
        Nouvelle adresse
      </button>
    </div>

    <p v-if="erreur" class="bandeau bandeau-erreur mb-3">{{ erreur }}</p>

    <div v-if="chargement" class="flex flex-col gap-2">
      <Squelette v-for="n in 2" :key="n" hauteur="76px" />
    </div>

    <div v-else-if="!adresses.length" class="carte">
      <div class="vide">
        <MapPin :size="30" class="text-trait" />
        <b class="vide-titre">Aucune adresse enregistree</b>
        <p class="vide-texte">
          Ajoutez-en une : le catalogue vous montrera alors les boutiques Express qui
          livrent reellement chez vous, au lieu de toutes les autres.
        </p>
        <button type="button" class="bouton-accent mt-4" @click="ajout = true">
          <Plus :size="15" /> Ajouter une adresse
        </button>
      </div>
    </div>

    <div v-else class="flex flex-col gap-3">
      <div
        v-for="adresse in adresses"
        :key="adresse.id"
        class="carte p-4"
        :style="adresse.est_principale ? { borderColor: 'var(--accent)' } : undefined"
      >
        <div class="flex items-start gap-3">
          <span
            class="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg"
            :style="{ background: 'var(--accent-doux)', color: 'var(--accent)' }"
          >
            <Home :size="18" />
          </span>

          <div class="min-w-0 flex-1">
            <div class="flex flex-wrap items-center gap-2">
              <b class="text-[13.5px]">{{ adresse.libelle || 'Adresse' }}</b>
              <span v-if="adresse.est_principale" class="badge badge-ok">
                <Star :size="10" /> principale
              </span>
            </div>
            <p class="mt-1 text-[12.5px] text-encre-douce">
              {{ adresse.rue }}<template v-if="adresse.complement">, {{ adresse.complement }}</template>
              <br />
              {{ adresse.code_postal }} {{ adresse.ville }}
            </p>
            <p v-if="adresse.instructions_livraison" class="mt-1.5 text-[12px] text-encre-douce">
              « {{ adresse.instructions_livraison }} »
            </p>
          </div>

          <div class="flex shrink-0 gap-1.5">
            <button
              v-if="!adresse.est_principale"
              type="button"
              class="bouton-ligne"
              title="Definir comme adresse principale"
              :disabled="occupe"
              @click="agir(
                espaces.client.modifierAdresse(adresse.id, { est_principale: true }),
                'Adresse principale mise a jour.',
              )"
            >
              <Star :size="14" />
              <span class="sr-only">Definir comme principale</span>
            </button>
            <button
              type="button"
              class="bouton-ligne bouton-ligne-danger"
              title="Retirer du carnet"
              :disabled="occupe"
              @click="agir(espaces.client.retirerAdresse(adresse.id), 'Adresse retiree du carnet.')"
            >
              <Trash2 :size="14" />
              <span class="sr-only">Retirer</span>
            </button>
          </div>
        </div>
      </div>
    </div>

    <Popup
      v-if="ajout"
      titre="Ajouter une adresse"
      explication="Elle rejoint votre carnet. La premiere adresse enregistree devient
                   automatiquement l'adresse principale."
      @fermer="ajout = false"
    >
      <form class="flex flex-col gap-3" @submit.prevent="ajouter">
        <label class="flex flex-col gap-1.5">
          <span class="etiquette">Libelle</span>
          <input v-model="nouvelle.libelle" class="champ-clair" placeholder="Domicile, Bureau…" />
        </label>
        <label class="flex flex-col gap-1.5">
          <span class="etiquette">Rue</span>
          <input v-model="nouvelle.rue" class="champ-clair" required />
        </label>
        <label class="flex flex-col gap-1.5">
          <span class="etiquette">Complement</span>
          <input v-model="nouvelle.complement" class="champ-clair"
                 placeholder="Batiment, etage, code…" />
        </label>
        <div class="flex gap-3">
          <label class="flex w-32 flex-col gap-1.5">
            <span class="etiquette">Code postal</span>
            <input v-model="nouvelle.code_postal" class="champ-clair" required />
          </label>
          <label class="flex flex-1 flex-col gap-1.5">
            <span class="etiquette">Ville</span>
            <input v-model="nouvelle.ville" class="champ-clair" required />
          </label>
        </div>
        <label class="flex flex-col gap-1.5">
          <span class="etiquette">Instructions pour le livreur</span>
          <input v-model="nouvelle.instructions_livraison" class="champ-clair"
                 placeholder="Code portail, etage, laisser chez le gardien…" />
        </label>
      </form>

      <template #actions>
        <button type="button" class="bouton-neutre !py-2" @click="ajout = false">Annuler</button>
        <button type="button" class="bouton-accent !py-2" :disabled="occupe" @click="ajouter">
          <Check :size="15" /> Enregistrer
        </button>
      </template>
    </Popup>
  </div>
</template>
