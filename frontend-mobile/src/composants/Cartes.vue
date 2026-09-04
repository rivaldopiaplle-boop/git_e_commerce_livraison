<script setup lang="ts">
// Le carnet de cartes, côté téléphone — O-5, D-150.
//
// Même règle que sur le web, et elle compte encore plus au pouce :
// **s'il y a déjà une carte, pas de formulaire.** Une ligne, un bouton. Le
// coût de saisie est payé une seule fois — c'était ta contrainte, *« que ça ne
// prenne pas beaucoup de temps »*.
//
// Le clavier est forcé en numérique et les champs portent leur `autocomplete` :
// sur un téléphone, le gestionnaire de mots de passe remplit la carte tout
// seul, et seize chiffres tapés au pouce sont seize occasions de se tromper.
import { IonButton, IonIcon, IonInput, IonSpinner } from '@ionic/vue'
import { EchecApi } from '@partage/api'
import { addOutline, cardOutline, trashOutline, warningOutline } from 'ionicons/icons'
import { computed, onMounted, ref } from 'vue'

import { useSession } from '@/magasins/session'

type Carte = {
  id: number
  marque: string
  quatre_derniers: string
  mois_expiration: number
  annee_expiration: number
  par_defaut: boolean
  expiree: boolean
  libelle: string
}

const emet = defineEmits<{ (evenement: 'choisie', carte: Carte | null): void }>()

const session = useSession()
const cartes = ref<Carte[]>([])
const essais = ref<{ numero: string; marque: string; effet: string }[]>([])
const choisie = ref<number | null>(null)
const formulaire = ref(false)
const occupe = ref(false)

const numero = ref('')
const expiration = ref('')
const cryptogramme = ref('')
const erreur = ref('')

const carteRetenue = computed(() =>
  cartes.value.find((carte) => carte.id === choisie.value) ?? null,
)

async function charger() {
  try {
    const donnees = await session.client.get<{
      cartes: Carte[]
      cartes_d_essai: { numero: string; marque: string; effet: string }[]
    }>('/moi/cartes')
    cartes.value = donnees.cartes
    essais.value = donnees.cartes_d_essai
    choisie.value = (donnees.cartes.find((carte) => carte.par_defaut)
      ?? donnees.cartes[0])?.id ?? null
    formulaire.value = !donnees.cartes.length
    emet('choisie', carteRetenue.value)
  } catch {
    // Un carnet vide vaut mieux qu'un écran en erreur : le formulaire
    // s'ouvrira, et le serveur refusera proprement si quelque chose cloche.
  }
}

onMounted(charger)

function surNumero(valeur: string | number | null | undefined) {
  const chiffres = String(valeur ?? '').replace(/\D/g, '').slice(0, 19)
  numero.value = chiffres.replace(/(.{4})/g, '$1 ').trim()
}

function surExpiration(valeur: string | number | null | undefined) {
  const chiffres = String(valeur ?? '').replace(/\D/g, '').slice(0, 4)
  expiration.value = chiffres.length > 2
    ? `${chiffres.slice(0, 2)}/${chiffres.slice(2)}`
    : chiffres
}

async function ajouter() {
  occupe.value = true
  erreur.value = ''
  const [mois, annee] = expiration.value.split('/')
  try {
    await session.client.post<Carte>('/moi/cartes', {
      numero: numero.value.replace(/\s/g, ''),
      mois: mois ?? '',
      annee: annee ?? '',
      cryptogramme: cryptogramme.value,
    })
    numero.value = expiration.value = cryptogramme.value = ''
    formulaire.value = false
    await charger()
  } catch (souci) {
    erreur.value = souci instanceof EchecApi ? souci.erreur.message : 'Carte refusée.'
  } finally {
    occupe.value = false
  }
}

function choisir(carte: Carte) {
  choisie.value = carte.id
  emet('choisie', carte)
}

async function retirer(carte: Carte) {
  occupe.value = true
  try {
    const donnees = await session.client.supprimer<{ cartes: Carte[] }>(
      `/moi/cartes/${carte.id}`,
    )
    cartes.value = donnees.cartes
    choisie.value = donnees.cartes[0]?.id ?? null
    formulaire.value = !donnees.cartes.length
    emet('choisie', carteRetenue.value)
  } finally {
    occupe.value = false
  }
}

function remplirAvec(essai: string) {
  surNumero(essai)
  expiration.value = '12/30'
  cryptogramme.value = essai.startsWith('37') ? '1234' : '123'
}
</script>

<template>
  <div class="carte-mobile">
    <b class="titre-carte"><IonIcon :icon="cardOutline" /> Moyen de paiement</b>

    <div v-if="cartes.length" class="liste">
      <label
        v-for="carte in cartes"
        :key="carte.id"
        class="ligne"
        :class="choisie === carte.id ? 'active' : ''"
      >
        <input
          type="radio"
          name="carte"
          :checked="choisie === carte.id"
          @change="choisir(carte)"
        />
        <span class="detail">
          <b>{{ carte.libelle }}</b>
          <span class="sous-titre">
            expire {{ String(carte.mois_expiration).padStart(2, '0') }}/{{
              String(carte.annee_expiration).slice(-2) }}
            <template v-if="carte.expiree"> · expirée</template>
          </span>
        </span>
        <button type="button" class="retirer" :disabled="occupe"
                @click.prevent.stop="retirer(carte)">
          <IonIcon :icon="trashOutline" />
        </button>
      </label>

      <IonButton v-if="!formulaire" size="small" fill="outline" @click="formulaire = true">
        <IonIcon :icon="addOutline" slot="start" /> Ajouter une carte
      </IonButton>
    </div>

    <form v-if="formulaire" class="formulaire" @submit.prevent="ajouter">
      <IonInput
        :value="numero"
        fill="outline"
        label="Numéro de carte"
        label-placement="floating"
        inputmode="numeric"
        autocomplete="cc-number"
        placeholder="4242 4242 4242 4242"
        @ion-input="surNumero($event.detail.value)"
      />
      <div class="deux">
        <IonInput
          :value="expiration"
          fill="outline"
          label="MM/AA"
          label-placement="floating"
          inputmode="numeric"
          autocomplete="cc-exp"
          @ion-input="surExpiration($event.detail.value)"
        />
        <IonInput
          v-model="cryptogramme"
          fill="outline"
          label="Cryptogramme"
          label-placement="floating"
          inputmode="numeric"
          autocomplete="cc-csc"
          :maxlength="4"
        />
      </div>

      <!-- Les cartes d'essai sont OFFERTES : une démonstration qu'on ne sait
           pas essayer ne se démontre pas. Et surtout, personne ne doit taper
           sa vraie carte ici. -->
      <div class="essais">
        <p class="avertissement">
          <IonIcon :icon="warningOutline" />
          <span>
            <b>N'entrez jamais votre vraie carte.</b>
            Seules les cartes d'essai ci-dessous sont acceptées.
          </span>
        </p>
        <div class="puces">
          <button
            v-for="essai in essais"
            :key="essai.numero"
            type="button"
            class="puce"
            @click="remplirAvec(essai.numero)"
          >
            •••• {{ essai.numero.slice(-4) }} · {{ essai.effet }}
          </button>
        </div>
      </div>

      <p v-if="erreur" class="erreur">{{ erreur }}</p>

      <IonButton expand="block" size="small" :disabled="occupe" @click="ajouter">
        <IonSpinner v-if="occupe" name="dots" />
        <span v-else>Enregistrer la carte</span>
      </IonButton>
      <IonButton v-if="cartes.length" expand="block" size="small" fill="clear"
                 color="medium" @click="formulaire = false">
        Annuler
      </IonButton>
    </form>
  </div>
</template>

<style scoped>
.titre-carte {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  margin-bottom: 10px;
}
.titre-carte ion-icon {
  color: var(--accent);
  font-size: 16px;
}
.liste {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.ligne {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 9px 10px;
  border: 1px solid var(--rd-trait);
  border-radius: 10px;
  font-size: 13px;
}
.ligne.active {
  border-color: var(--accent);
  background: var(--accent-doux);
}
.ligne .detail {
  flex: 1;
  min-width: 0;
}
.ligne .detail b {
  display: block;
  font-size: 13px;
}
.retirer {
  border: 0;
  background: none;
  color: var(--rd-encre-douce);
  font-size: 16px;
  padding: 4px;
}
.formulaire {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-top: 10px;
}
.deux {
  display: flex;
  gap: 10px;
}
.deux > * {
  flex: 1;
}
.essais {
  border-radius: 10px;
  background: var(--rd-atelier, #f4f5f8);
  padding: 10px;
}
.avertissement {
  display: flex;
  align-items: flex-start;
  gap: 7px;
  margin: 0;
  font-size: 11px;
  line-height: 1.55;
  color: var(--rd-encre-douce);
}
.avertissement ion-icon {
  font-size: 14px;
  color: #b8650f;
  flex-shrink: 0;
}
.avertissement b {
  color: var(--ion-text-color);
}
.puces {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 8px;
}
.puce {
  border: 1px solid var(--rd-trait);
  background: #fff;
  border-radius: 999px;
  padding: 5px 10px;
  font-size: 11px;
}
.erreur {
  font-size: 11.5px;
  line-height: 1.6;
  color: #9c2116;
  background: #fbe4e2;
  border-radius: 10px;
  padding: 10px 12px;
  margin: 0;
}
</style>
