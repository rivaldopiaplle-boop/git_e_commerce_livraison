<script setup lang="ts">
// La connexion mobile.
//
// Les comptes de démonstration sont proposés d'un bouton : c'est ce qui rend
// une démonstration à deux rôles tenable sur un téléphone, où taper une
// adresse et un mot de passe prend trente secondes (règle d'or n°3).
import {
  IonButton, IonContent, IonInput, IonNote, IonPage, IonSpinner,
} from '@ionic/vue'
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { MOT_DE_PASSE_DEMO } from '@/config'
import { useSession } from '@/magasins/session'

const session = useSession()
const routeur = useRouter()
const route = useRoute()

const email = ref('')
const motDePasse = ref('')
const erreur = ref('')

// Seuls les deux rôles qui existent sur mobile (D-40) : le client, présent
// sur les deux supports, et le livreur, qui n'existe que là.
const COMPTES = [
  { email: 'amine@exemple.fr', qui: 'Livreur Express', aide: 'une course à la fois' },
  { email: 'julien@exemple.fr', qui: 'Livreur Standard', aide: 'une tournée d’arrêts' },
  { email: 'lea@exemple.fr', qui: 'Cliente', aide: 'catalogue, panier, suivi' },
]

async function valider() {
  erreur.value = ''
  try {
    await session.connecter(email.value, motDePasse.value)
    // On revient là où on allait, plutôt qu'à l'accueil : sinon il faut
    // refaire son chemin (D-66).
    routeur.replace((route.query.suite as string) || '/accueil')
  } catch (echec) {
    erreur.value = echec instanceof Error ? echec.message : 'Connexion impossible.'
  }
}

function remplir(compte: { email: string }) {
  email.value = compte.email
  motDePasse.value = MOT_DE_PASSE_DEMO
  erreur.value = ''
}
</script>

<template>
  <IonPage>
    <IonContent :fullscreen="true" class="fond">
      <div class="ecran">
        <div class="marque">
          <span class="logo">R</span>
          <h1>RivDinde</h1>
          <p>commander, livrer, suivre</p>
        </div>

        <form class="formulaire" @submit.prevent="valider">
          <IonInput
            v-model="email"
            label="Adresse e-mail"
            label-placement="floating"
            type="email"
            fill="outline"
            autocomplete="email"
            :clear-input="true"
          />
          <IonInput
            v-model="motDePasse"
            label="Mot de passe"
            label-placement="floating"
            type="password"
            fill="outline"
            autocomplete="current-password"
          />

          <IonNote v-if="erreur" color="danger" class="erreur">{{ erreur }}</IonNote>

          <IonButton
            type="submit"
            expand="block"
            :disabled="session.chargement || !email || !motDePasse"
          >
            <IonSpinner v-if="session.chargement" name="dots" />
            <span v-else>Se connecter</span>
          </IonButton>
        </form>

        <div class="demo">
          <span class="titre">Comptes de démonstration</span>
          <button
            v-for="compte in COMPTES"
            :key="compte.email"
            type="button"
            class="compte"
            @click="remplir(compte)"
          >
            <b>{{ compte.qui }}</b>
            <span>{{ compte.aide }}</span>
          </button>
        </div>

        <p class="mention">
          Environnement de démonstration — aucune commande réelle, aucun paiement réel.
        </p>
      </div>
    </IonContent>
  </IonPage>
</template>

<style scoped>
.fond {
  --background: #f4f5f8;
}
.ecran {
  min-height: 100%;
  padding: calc(48px + env(safe-area-inset-top)) 22px 32px;
  display: flex;
  flex-direction: column;
  gap: 26px;
}
.marque {
  text-align: center;
}
.logo {
  display: inline-grid;
  place-items: center;
  width: 62px;
  height: 62px;
  border-radius: 20px;
  background: #ea8c2a;
  color: #fff;
  font-size: 30px;
  font-weight: 800;
}
.marque h1 {
  margin: 14px 0 2px;
  font-size: 26px;
  font-weight: 700;
}
.marque p {
  margin: 0;
  font-size: 11.5px;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: #b8650f;
  font-weight: 600;
}
.formulaire {
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.erreur {
  font-size: 12.5px;
}
.demo {
  border-top: 1px solid #e4e7ee;
  padding-top: 18px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.demo .titre {
  font-size: 10.5px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #5b6478;
  text-align: center;
  margin-bottom: 4px;
}
.compte {
  border: 1px solid #e4e7ee;
  background: #fff;
  border-radius: 12px;
  padding: 11px 14px;
  text-align: left;
}
.compte b {
  display: block;
  font-size: 13px;
}
.compte span {
  font-size: 11.5px;
  color: #5b6478;
}
.mention {
  margin: 0;
  text-align: center;
  font-size: 11px;
  color: #5b6478;
}
</style>
