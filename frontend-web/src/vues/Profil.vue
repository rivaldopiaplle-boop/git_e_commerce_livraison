<script setup lang="ts">
// Le profil : ce que chacun peut changer chez lui.
import { Check, Mail, Phone, UserRound } from '@lucide/vue'
import { ref } from 'vue'

import { api, EchecApi } from '../api/client'
import { useAuthentification } from '../stores/authentification'

const session = useAuthentification()

const champs = ref({
  prenom: session.utilisateur?.prenom ?? '',
  nom: session.utilisateur?.nom ?? '',
  telephone: session.utilisateur?.telephone ?? '',
})
const message = ref('')
const erreur = ref('')
const occupe = ref(false)

async function enregistrer() {
  message.value = ''
  erreur.value = ''
  occupe.value = true
  try {
    await api.patch('/moi', champs.value)
    await session.restaurer()
    message.value = 'Modifications enregistrees.'
  } catch (echec) {
    erreur.value = echec instanceof EchecApi ? echec.erreur.message : 'Enregistrement impossible.'
  } finally {
    occupe.value = false
  }
}
</script>

<template>
  <div class="mx-auto max-w-[620px] animate-[apparition_0.2s_ease-out]">
    <section class="carte">
      <h3 class="carte-titre">
        <span class="flex items-center gap-2"><UserRound :size="15" /> Mes informations</span>
      </h3>

      <form class="flex flex-col gap-4 p-5" @submit.prevent="enregistrer">
        <div class="flex flex-wrap gap-3">
          <label class="flex flex-1 flex-col gap-1.5">
            <span class="text-[12.5px] font-semibold text-encre-douce">Prenom</span>
            <input v-model="champs.prenom" class="champ-clair" required />
          </label>
          <label class="flex flex-1 flex-col gap-1.5">
            <span class="text-[12.5px] font-semibold text-encre-douce">Nom</span>
            <input v-model="champs.nom" class="champ-clair" required />
          </label>
        </div>

        <label class="flex flex-col gap-1.5">
          <span class="flex items-center gap-1.5 text-[12.5px] font-semibold text-encre-douce">
            <Phone :size="13" /> Telephone
          </span>
          <input v-model="champs.telephone" class="champ-clair" />
        </label>

        <label class="flex flex-col gap-1.5">
          <span class="flex items-center gap-1.5 text-[12.5px] font-semibold text-encre-douce">
            <Mail :size="13" /> Adresse e-mail
          </span>
          <input :value="session.utilisateur?.email" class="champ-clair" disabled />
          <span class="text-[11.5px] text-encre-douce">
            L adresse sert d identifiant de connexion : elle ne se change pas ici.
          </span>
        </label>

        <p v-if="message" class="rounded-lg bg-[#e2f7ea] px-3.5 py-2.5 text-[12.5px]
                                 text-[#116b34]">
          {{ message }}
        </p>
        <p v-if="erreur" class="rounded-lg bg-[#fbe4e2] px-3.5 py-2.5 text-[12.5px]
                                text-[#9c2116]">
          {{ erreur }}
        </p>

        <button type="submit" class="bouton-accent self-start" :disabled="occupe">
          <Check :size="16" /> Enregistrer
        </button>
      </form>
    </section>
  </div>
</template>
