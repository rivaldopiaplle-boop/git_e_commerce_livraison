<script setup lang="ts">
// « Ma course » — l'écran du livreur Express, celui où il passe sa journée.
//
// Une seule course à la fois : c'est une contrainte du métier, tenue par le
// serveur, pas une limite d'affichage. L'écran ne montre donc jamais de liste.
//
// Trois actions, et elles n'existent que sur mobile (D-40) : récupérer le
// colis, confirmer la remise avec le code du client, signaler une absence.
// La position part avec la confirmation — c'est ce qui prouve qu'on y était.
import {
  IonBadge, IonButton, IonIcon, IonInput, IonModal, IonTextarea,
} from '@ionic/vue'
import { Geolocation } from '@capacitor/geolocation'
import { euros } from '@partage/metier'
import {
  bicycleOutline, callOutline, locationOutline, navigateOutline, storefrontOutline,
} from 'ionicons/icons'
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'

import Ecran from '@/composants/Ecran.vue'
import { useLivreur } from '@/magasins/livreur'
import { useRafraichissement } from '@/rafraichissement'

const livreur = useLivreur()
const routeur = useRouter()

const course = computed(() => livreur.courseActuelle)
const remise = ref(false)
const absence = ref(false)
const code = ref('')
const commentaire = ref('')
const occupe = ref(false)
const erreur = ref('')

useRafraichissement(() => livreur.charger(), { periodique: true })

/** La position, si le téléphone veut bien la donner.
 *
 *  On ne bloque JAMAIS la confirmation dessus : un sous-sol sans signal ne
 *  doit pas empêcher un livreur de finir sa journée. La position est une
 *  preuve utile, pas une condition.
 */
async function position() {
  try {
    const p = await Geolocation.getCurrentPosition({ timeout: 4000 })
    return { lat: p.coords.latitude, lon: p.coords.longitude }
  } catch {
    return undefined
  }
}

async function recuperer() {
  if (!course.value) return
  occupe.value = true
  erreur.value = ''
  try {
    await livreur.recupererColis(course.value.id)
  } catch (echec) {
    erreur.value = echec instanceof Error ? echec.message : 'Action refusée.'
  } finally {
    occupe.value = false
  }
}

async function confirmer() {
  if (!course.value) return
  occupe.value = true
  erreur.value = ''
  try {
    await livreur.confirmerRemise(course.value.id, code.value, await position())
    remise.value = false
    code.value = ''
  } catch (echec) {
    erreur.value = echec instanceof Error ? echec.message : 'Confirmation refusée.'
  } finally {
    occupe.value = false
  }
}

async function declarerAbsence() {
  if (!course.value) return
  occupe.value = true
  try {
    await livreur.signalerAbsence(course.value.id, commentaire.value)
    absence.value = false
    commentaire.value = ''
  } catch (echec) {
    erreur.value = echec instanceof Error ? echec.message : 'Signalement refusé.'
  } finally {
    occupe.value = false
  }
}

/** Ouvre l'itinéraire dans l'application de cartes du téléphone.
 *
 *  On ne construit pas de carte maison : celle du téléphone connaît déjà le
 *  trafic, les sens interdits et la voix du guidage (règle d'or n°5).
 */
function guider() {
  const adresse = course.value?.adresse
  if (!adresse) return
  const destination = encodeURIComponent(
    `${adresse.rue}, ${adresse.code_postal} ${adresse.ville}`,
  )
  window.open(`https://www.google.com/maps/dir/?api=1&destination=${destination}`, '_system')
}
</script>

<template>
  <Ecran titre="Ma course" sous-titre="Livreur · Express" :rafraichir="livreur.charger">
    <template v-if="course">
      <div class="carte-mobile">
        <div class="entete">
          <div>
            <b class="client">{{ course.client }}</b>
            <span class="sous-titre">{{ course.numero_commande }}</span>
          </div>
          <IonBadge>{{ course.libelle_statut }}</IonBadge>
        </div>

        <div class="trajet">
          <div class="etape">
            <IonIcon :icon="storefrontOutline" />
            <span>
              <b>À récupérer</b>
              {{ course.boutiques.join(', ') }}
            </span>
          </div>
          <div class="etape">
            <IonIcon :icon="locationOutline" />
            <span>
              <b>À livrer</b>
              {{ course.adresse?.rue }}<br />
              {{ course.adresse?.code_postal }} {{ course.adresse?.ville }}
              <em v-if="course.adresse?.instructions">
                « {{ course.adresse.instructions }} »
              </em>
            </span>
          </div>
        </div>

        <div class="chiffres">
          <span><b>{{ course.distance_km }} km</b> de trajet</span>
          <span><b>{{ euros(course.remuneration_livreur_centimes) }}</b> pour vous</span>
        </div>
      </div>

      <IonButton expand="block" fill="outline" @click="guider">
        <IonIcon slot="start" :icon="navigateOutline" />
        M'y conduire
      </IonButton>

      <IonButton
        v-if="course.statut_livraison === 'ATTRIBUEE'"
        expand="block"
        :disabled="occupe"
        @click="recuperer"
      >
        J'ai le colis, je pars
      </IonButton>

      <template v-else>
        <IonButton expand="block" :disabled="occupe" @click="remise = true">
          Confirmer la remise
        </IonButton>
        <IonButton expand="block" fill="clear" color="medium" :disabled="occupe"
                   @click="absence = true">
          Personne à l'adresse
        </IonButton>
      </template>

      <p class="note">
        Le client vous donnera un code à quatre chiffres. C'est lui qui prouve que le bon
        colis est arrivé à la bonne personne — et qui vous protège s'il conteste.
      </p>
    </template>

    <div v-else class="etat-vide">
      <IonIcon :icon="bicycleOutline" class="grande-icone" />
      <b>Aucune course en cours</b>
      <span>
        Vous serez prévenu dès qu'une livraison Express est disponible près de vous.
      </span>
      <IonButton fill="outline" size="small" class="ion-margin-top"
                 @click="routeur.push('/proximite')">
        Voir ce qui est disponible
      </IonButton>
    </div>

    <!-- La remise : formulaire court, donc feuille modale (D-60) -->
    <IonModal :is-open="remise" :initial-breakpoint="0.55" :breakpoints="[0, 0.55]"
              @did-dismiss="remise = false">
      <div class="feuille">
        <h2>Code de remise</h2>
        <p>Demandez au client le code à quatre chiffres affiché sur sa commande.</p>
        <IonInput
          v-model="code"
          type="tel"
          inputmode="numeric"
          :maxlength="8"
          fill="outline"
          label="Code"
          label-placement="floating"
          class="code"
        />
        <p v-if="erreur" class="erreur">{{ erreur }}</p>
        <IonButton expand="block" :disabled="occupe || !code" @click="confirmer">
          Confirmer la livraison
        </IonButton>
        <IonButton expand="block" fill="clear" color="medium" @click="remise = false">
          Annuler
        </IonButton>
      </div>
    </IonModal>

    <!-- L'absence : deux tentatives, puis retour (D-23) -->
    <IonModal :is-open="absence" :initial-breakpoint="0.6" :breakpoints="[0, 0.6]"
              @did-dismiss="absence = false">
      <div class="feuille">
        <h2>Personne à l'adresse ?</h2>
        <p>
          Une deuxième tentative sera possible. Au deuxième échec, le colis repart chez le
          vendeur et le client en est prévenu.
        </p>
        <IonTextarea
          v-model="commentaire"
          fill="outline"
          label="Ce que vous avez constaté"
          label-placement="floating"
          :auto-grow="true"
          placeholder="Interphone sans réponse, avis de passage déposé…"
        />
        <IonButton expand="block" color="warning" :disabled="occupe" @click="declarerAbsence">
          Signaler l'absence
        </IonButton>
        <IonButton expand="block" fill="clear" color="medium" @click="absence = false">
          Annuler
        </IonButton>
      </div>
    </IonModal>
  </Ecran>
</template>

<style scoped>
.entete {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 10px;
}
.client {
  font-size: 15px;
}
.trajet {
  margin: 12px 0;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.etape {
  display: flex;
  gap: 10px;
  font-size: 12.5px;
}
.etape ion-icon {
  font-size: 17px;
  color: var(--accent);
  flex-shrink: 0;
  margin-top: 2px;
}
.etape b {
  display: block;
  font-size: 10.5px;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--rd-encre-douce);
}
.etape em {
  display: block;
  margin-top: 3px;
  color: var(--rd-encre-douce);
  font-style: normal;
}
.chiffres {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  border-top: 1px solid var(--rd-trait-doux);
  padding-top: 10px;
  font-size: 11.5px;
  color: var(--rd-encre-douce);
}
.chiffres b {
  color: var(--ion-text-color);
  font-size: 13px;
}
.note {
  font-size: 11px;
  color: var(--rd-encre-douce);
  line-height: 1.55;
  margin-top: 14px;
}
.grande-icone {
  font-size: 34px;
  color: var(--rd-trait);
}
.feuille {
  padding: 20px 18px calc(20px + var(--rd-marge-basse, 12px));
}
.feuille h2 {
  margin: 0 0 4px;
  font-size: 16px;
}
.feuille p {
  margin: 0 0 14px;
  font-size: 12.5px;
  color: var(--rd-encre-douce);
  line-height: 1.55;
}
.code {
  margin-bottom: 14px;
  font-size: 22px;
  letter-spacing: 0.3em;
  text-align: center;
}
.erreur {
  color: var(--ion-color-danger, #9c2116);
  font-size: 12.5px;
}
</style>
