<script setup lang="ts">
// Le personnel de la boutique.
//
// L'ecran affiche ce a quoi un gestionnaire N'A PAS acces, en toutes lettres.
// C'est la premiere question d'un commercant avant de creer un compte pour son
// employe, et la matrice des droits y repond depuis le debut (D-04) : autant
// la montrer plutot que de la laisser dans un document.
import { AlertTriangle, Check, Mail, Users, UserPlus, X } from '@lucide/vue'
import { onMounted, ref } from 'vue'

import { EchecApi } from '../../api/client'
import { espaces, type MembrePersonnel } from '../../api/espaces'
import Popup from '../../composants/Popup.vue'
import Squelette from '../../composants/Squelette.vue'

const personnel = ref<MembrePersonnel[]>([])
const acces = ref<{ libelle: string; autorise: boolean }[]>([])
const chargement = ref(true)
const creation = ref(false)
const occupe = ref(false)
const erreur = ref('')
const message = ref('')

const nouveau = ref({ prenom: '', nom: '', email: '', mot_de_passe: '' })

async function charger() {
  chargement.value = true
  try {
    const donnees = await espaces.vendeur.personnel()
    personnel.value = donnees.personnel
    acces.value = donnees.acces
  } finally {
    chargement.value = false
  }
}

onMounted(charger)

async function creer() {
  erreur.value = ''
  occupe.value = true
  try {
    await espaces.vendeur.creerGestionnaire(nouveau.value)
    message.value = `Le compte de ${nouveau.value.prenom} est cree.`
    creation.value = false
    nouveau.value = { prenom: '', nom: '', email: '', mot_de_passe: '' }
    await charger()
  } catch (echec) {
    erreur.value = echec instanceof EchecApi ? echec.erreur.message : 'Creation refusee.'
  } finally {
    occupe.value = false
  }
}
</script>

<template>
  <div class="mx-auto grid max-w-[980px] animate-[apparition_0.2s_ease-out] gap-4 lg:grid-cols-3">
    <div class="lg:col-span-2">
      <div class="mb-4 flex items-center justify-between gap-3">
        <p class="text-[12.5px] text-encre-douce">
          Vos employes preparent les commandes et corrigent le stock. Ils ne sont pas
          rattaches a la plateforme, mais a votre boutique.
        </p>
        <button type="button" class="bouton-accent shrink-0" @click="creation = true">
          <UserPlus :size="15" />
          Creer un compte
        </button>
      </div>

      <p v-if="message" class="bandeau bandeau-info mb-3">
        <Check :size="15" class="mt-px shrink-0" /> {{ message }}
      </p>

      <div v-if="chargement" class="flex flex-col gap-2">
        <Squelette v-for="n in 2" :key="n" hauteur="56px" />
      </div>

      <div v-else-if="!personnel.length" class="carte">
        <div class="vide">
          <Users :size="30" class="text-trait" />
          <b class="vide-titre">Vous travaillez seul pour l instant</b>
          <p class="vide-texte">
            Creez un compte pour un employe : il pourra preparer les commandes et corriger
            le stock, sans jamais voir vos prix d achat ni votre chiffre d affaires.
          </p>
          <button type="button" class="bouton-accent mt-4" @click="creation = true">
            <UserPlus :size="15" /> Creer un compte
          </button>
        </div>
      </div>

      <div v-else class="carte">
        <h3 class="carte-titre">
          <span>{{ personnel.length }} personne(s)</span>
        </h3>
        <div v-for="membre in personnel" :key="membre.id" class="ligne">
          <span
            class="flex h-9 w-9 shrink-0 items-center justify-center rounded-full text-[12px]
                   font-bold text-white"
            :style="{ background: 'var(--accent)' }"
          >
            {{ membre.utilisateur.prenom.charAt(0).toUpperCase() }}
          </span>
          <span class="min-w-0 flex-1">
            <b class="block truncate">
              {{ membre.utilisateur.prenom }} {{ membre.utilisateur.nom }}
            </b>
            <span class="flex items-center gap-1 text-[11.2px] text-encre-douce">
              <Mail :size="11" /> {{ membre.utilisateur.email }}
            </span>
          </span>
          <span class="badge badge-cours">preparation + stock</span>
        </div>
      </div>
    </div>

    <!-- Ce que le personnel ne voit pas : dit une fois, en clair. -->
    <aside class="carte h-fit">
      <h3 class="carte-titre">Ce a quoi ils ont acces</h3>
      <div v-for="droit in acces" :key="droit.libelle" class="ligne">
        <component
          :is="droit.autorise ? Check : X"
          :size="15"
          class="shrink-0"
          :class="droit.autorise ? 'text-succes' : 'text-alerte'"
        />
        <span class="flex-1" :class="droit.autorise ? '' : 'text-encre-douce line-through'">
          {{ droit.libelle }}
        </span>
      </div>
      <p class="border-t border-trait-doux px-4 py-3 text-[11.5px] leading-relaxed
                text-encre-douce">
        Ces limites sont verifiees par le serveur, pas seulement masquees a l ecran :
        un employe qui appellerait l adresse du chiffre d affaires recevrait un refus.
      </p>
    </aside>

    <Popup
      v-if="creation"
      titre="Creer un compte gestionnaire"
      explication="Ce compte appartient a votre boutique. Il n'a jamais acces au chiffre
                   d'affaires ni aux prix, et vous pouvez le retirer a tout moment."
      @fermer="creation = false"
    >
      <form class="flex flex-col gap-3" @submit.prevent="creer">
        <div class="flex gap-3">
          <label class="flex flex-1 flex-col gap-1.5">
            <span class="etiquette">Prenom</span>
            <input v-model="nouveau.prenom" class="champ-clair" required />
          </label>
          <label class="flex flex-1 flex-col gap-1.5">
            <span class="etiquette">Nom</span>
            <input v-model="nouveau.nom" class="champ-clair" required />
          </label>
        </div>
        <label class="flex flex-col gap-1.5">
          <span class="etiquette">Adresse e-mail</span>
          <input v-model="nouveau.email" type="email" class="champ-clair" required />
        </label>
        <label class="flex flex-col gap-1.5">
          <span class="etiquette">Mot de passe provisoire</span>
          <input
            v-model="nouveau.mot_de_passe"
            type="text"
            class="champ-clair"
            minlength="10"
            required
          />
          <span class="text-[11.5px] text-encre-douce">
            Dix caracteres au minimum. Communiquez-le a votre employe, qui le changera.
          </span>
        </label>

        <p v-if="erreur" class="bandeau bandeau-erreur">
          <AlertTriangle :size="15" class="mt-px shrink-0" /> {{ erreur }}
        </p>
      </form>

      <template #actions>
        <button type="button" class="bouton-neutre !py-2" @click="creation = false">
          Annuler
        </button>
        <button type="button" class="bouton-accent !py-2" :disabled="occupe" @click="creer">
          <Check :size="15" /> Creer le compte
        </button>
      </template>
    </Popup>
  </div>
</template>
