<script setup lang="ts">
// « Prochain arrêt » — un écran plein, pas une liste (D-90).
//
// Un livreur n'a pas besoin de rouvrir sa tournée entière dix fois par jour
// pour savoir où il va maintenant. Ici : l'arrêt suivant, la navigation, le
// bouton livré ou absent, et rien d'autre.
import { IonButton, IonIcon, IonInput, IonModal } from '@ionic/vue'
import { Geolocation } from '@capacitor/geolocation'
import { checkmarkDoneOutline, locationOutline, navigateOutline } from 'ionicons/icons'
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import Ecran from '@/composants/Ecran.vue'
import { useLivreur } from '@/magasins/livreur'

const livreur = useLivreur()
const routeur = useRouter()

const arret = computed(() => livreur.prochainArret)
const remise = ref(false)
const code = ref('')
const occupe = ref(false)
const erreur = ref('')

onMounted(() => livreur.charger())

async function position() {
  try {
    const p = await Geolocation.getCurrentPosition({ timeout: 4000 })
    return { lat: p.coords.latitude, lon: p.coords.longitude }
  } catch {
    return undefined
  }
}

async function confirmer() {
  if (!arret.value) return
  occupe.value = true
  erreur.value = ''
  try {
    await livreur.confirmerRemise(arret.value.livraison.id, code.value, await position())
    remise.value = false
    code.value = ''
  } catch (echec) {
    erreur.value = echec instanceof Error ? echec.message : 'Confirmation refusée.'
  } finally {
    occupe.value = false
  }
}

async function absent() {
  if (!arret.value) return
  occupe.value = true
  try {
    await livreur.signalerAbsence(arret.value.livraison.id, 'Personne à l’adresse.')
  } finally {
    occupe.value = false
  }
}

function guider() {
  const adresse = arret.value?.livraison.adresse
  if (!adresse) return
  const destination = encodeURIComponent(
    `${adresse.rue}, ${adresse.code_postal} ${adresse.ville}`,
  )
  window.open(`https://www.google.com/maps/dir/?api=1&destination=${destination}`, '_system')
}
</script>

<template>
  <Ecran titre="Prochain arrêt" sous-titre="Livreur · Standard" :rafraichir="livreur.charger">
    <template v-if="arret">
      <div class="carte-mobile plein">
        <span class="rang">Arrêt {{ arret.ordre }} sur {{ livreur.tournee?.nombre_arrets }}</span>
        <b class="client">{{ arret.livraison.client }}</b>

        <p class="adresse">
          <IonIcon :icon="locationOutline" />
          {{ arret.livraison.adresse?.rue }}<br />
          {{ arret.livraison.adresse?.code_postal }} {{ arret.livraison.adresse?.ville }}
        </p>
        <p v-if="arret.livraison.adresse?.instructions" class="consigne">
          « {{ arret.livraison.adresse.instructions }} »
        </p>
      </div>

      <IonButton expand="block" fill="outline" @click="guider">
        <IonIcon slot="start" :icon="navigateOutline" />
        M'y conduire
      </IonButton>
      <IonButton expand="block" :disabled="occupe" @click="remise = true">
        <IonIcon slot="start" :icon="checkmarkDoneOutline" />
        Livré
      </IonButton>
      <IonButton expand="block" fill="clear" color="medium" :disabled="occupe" @click="absent">
        Personne à l'adresse
      </IonButton>
    </template>

    <div v-else class="etat-vide">
      <IonIcon :icon="checkmarkDoneOutline" class="grande-icone" />
      <b>Tournée terminée</b>
      <span>Tous vos arrêts sont faits. Bonne fin de journée.</span>
      <IonButton fill="outline" size="small" class="ion-margin-top"
                 @click="routeur.push('/gains')">
        Voir mes gains
      </IonButton>
    </div>

    <IonModal :is-open="remise" :initial-breakpoint="0.5" :breakpoints="[0, 0.5]"
              @did-dismiss="remise = false">
      <div class="feuille">
        <h2>Code de remise</h2>
        <p>Demandez au client le code affiché sur sa commande.</p>
        <IonInput v-model="code" type="tel" inputmode="numeric" fill="outline"
                  label="Code" label-placement="floating" class="code" />
        <p v-if="erreur" class="erreur">{{ erreur }}</p>
        <IonButton expand="block" :disabled="occupe || !code" @click="confirmer">
          Confirmer la livraison
        </IonButton>
      </div>
    </IonModal>
  </Ecran>
</template>

<style scoped>
.plein {
  padding: 20px 16px;
}
.rang {
  font-size: 10.5px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--rd-encre-douce);
}
.client {
  display: block;
  font-size: 22px;
  margin: 4px 0 12px;
}
.adresse {
  margin: 0;
  font-size: 14px;
  line-height: 1.6;
}
.adresse ion-icon {
  color: var(--accent);
  vertical-align: -2px;
  margin-right: 4px;
}
.consigne {
  margin: 10px 0 0;
  padding: 10px 12px;
  border-radius: 10px;
  background: var(--rd-atelier);
  font-size: 12.5px;
  color: var(--rd-encre-douce);
}
.grande-icone {
  font-size: 34px;
  color: var(--rd-trait);
}
.feuille {
  padding: 20px 18px calc(20px + env(safe-area-inset-bottom));
}
.feuille h2 {
  margin: 0 0 4px;
  font-size: 16px;
}
.feuille p {
  margin: 0 0 14px;
  font-size: 12.5px;
  color: var(--rd-encre-douce);
}
.code {
  margin-bottom: 14px;
  font-size: 22px;
  letter-spacing: 0.3em;
  text-align: center;
}
.erreur {
  color: #9c2116;
}
</style>
