<script setup lang="ts">
// « Prochain arrêt » — un écran plein, pas une liste (D-90).
//
// Un livreur n'a pas besoin de rouvrir sa tournée entière dix fois par jour
// pour savoir où il va maintenant. Ici : l'arrêt suivant, la navigation, le
// bouton livré ou absent, et rien d'autre.
import { IonButton, IonIcon, IonInput, IonModal } from '@ionic/vue'
import { Geolocation } from '@capacitor/geolocation'
import {
  alertCircleOutline, checkmarkDoneOutline, listOutline, locationOutline,
  navigateOutline,
} from 'ionicons/icons'
import { computed, defineAsyncComponent, ref } from 'vue'
import { useRouter } from 'vue-router'

import Ecran from '@/composants/Ecran.vue'
import { useLivreur } from '@/magasins/livreur'
import { useRafraichissement } from '@/rafraichissement'

const livreur = useLivreur()
const routeur = useRouter()

const arret = computed(() => livreur.prochainArret)

/**
 * Ce qu'il reste vraiment à faire — O-5.
 *
 * Ta remarque : *« tu cliques les livraisons échouées, ça ramène sur les
 * gains, pourquoi ? »*. L'écran ne savait dire qu'une chose — « tournée
 * terminée, voir mes gains » — et il la disait dès que « prochain arrêt »
 * était vide, y compris quand des arrêts avaient échoué. On atterrissait sur
 * ses gains sans comprendre pourquoi, et sans savoir ce qui restait.
 *
 * Il compte donc, et il dit.
 */
const bilan = computed(() => {
  const arrets = livreur.tournee?.arrets ?? []
  return {
    total: arrets.length,
    livres: arrets.filter((a) => a.statut === 'LIVRE').length,
    echoues: arrets.filter((a) => a.statut === 'ECHOUE').length,
    restants: arrets.filter((a) => ['A_FAIRE', 'REPORTE'].includes(a.statut)).length,
  }
})

/** Ma position, quand le navigateur veut bien la donner. */
const moi = ref<{ lat: number; lon: number } | null>(null)

/**
 * Les deux points du trajet : moi, puis l'arrêt.
 *
 * Sans ma position — géolocalisation refusée, origine non sécurisée — il ne
 * reste que l'arrêt, et la carte le montre seul plutôt que de disparaître.
 * Un écran qui s'efface parce qu'une permission manque punit la personne pour
 * un choix qu'elle avait le droit de faire.
 */
const trajet = computed(() => {
  const adresse = arret.value?.livraison.adresse
  const points = []
  if (moi.value) points.push({ ...moi.value, depart: true })
  if (adresse?.latitude && adresse?.longitude) {
    points.push({
      lat: Number(adresse.latitude),
      lon: Number(adresse.longitude),
      rang: arret.value?.ordre,
    })
  }
  return points
})
const remise = ref(false)
const code = ref('')
const occupe = ref(false)
const erreur = ref('')

/**
 * L'arrêt courant se recharge en fond : il change quand l'entrepôt réordonne
 * la tournée, et le livreur ne doit pas rouler vers l'ancien.
 */
useRafraichissement(async () => {
  await livreur.charger()
  moi.value = (await position()) ?? null
}, { periodique: true })

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

/**
 * « Personne à l'adresse » — et ce qui se passe ensuite (O-5).
 *
 * Ta remarque : *« personne à l'adresse n'a pas de suite »*. C'était vrai, et
 * la cause était côté serveur : l'arrêt restait « à faire », donc « prochain
 * arrêt » redonnait la même adresse indéfiniment. Le livreur signalait, et
 * rien ne bougeait.
 *
 * Il part maintenant **en fin de tournée** à la première tentative, et l'écran
 * dit lequel des deux cas s'est produit — un geste dont on ne voit pas l'effet
 * est un geste qu'on refait trois fois.
 */
const resultatAbsence = ref('')

async function absent() {
  if (!arret.value) return
  occupe.value = true
  erreur.value = ''
  try {
    const retour = await livreur.signalerAbsence(
      arret.value.livraison.id, 'Personne à l’adresse.',
    )
    resultatAbsence.value = retour?.tentative >= 2
      ? 'Deuxième passage sans réponse : le colis repart chez le vendeur, et le '
        + 'client est prévenu.'
      : 'Tentative 1 sur 2. Cet arrêt repasse en fin de tournée : continuez, vous '
        + 'y reviendrez.'
  } catch (echec) {
    erreur.value = echec instanceof Error ? echec.message : 'Signalement refusé.'
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

// MapLibre pese pres d'un mega-octet. Charge paresseusement, il n'arrive
// qu'au moment ou une carte s'affiche : un livreur en 4G ne telecharge pas un
// moteur de cartographie pour consulter ses gains.
const Carte = defineAsyncComponent(() => import('@/composants/Carte.vue'))
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

      <!-- La carte AVANT les boutons : on regarde où c'est, puis on agit. -->
      <Carte v-if="trajet.length" :points="trajet" profil="voiture" hauteur="220px" />

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

      <p v-if="resultatAbsence" class="suite">{{ resultatAbsence }}</p>
      <p v-if="erreur" class="erreur">{{ erreur }}</p>
    </template>

    <div v-else-if="!livreur.tournee" class="etat-vide">
      <IonIcon :icon="listOutline" class="grande-icone" />
      <b>Aucune tournée</b>
      <span>
        L'entrepôt vous en confiera une quand les colis de votre zone seront
        arrivés et rangés.
      </span>
      <IonButton fill="outline" size="small" class="ion-margin-top"
                 @click="routeur.push('/accueil')">
        Retour à l'accueil
      </IonButton>
    </div>

    <!-- Terminée VRAIMENT : tous les arrêts sont livrés. -->
    <div v-else-if="!bilan.echoues" class="etat-vide">
      <IonIcon :icon="checkmarkDoneOutline" class="grande-icone" />
      <b>Tournée terminée</b>
      <span>
        {{ bilan.livres }} arrêt{{ bilan.livres > 1 ? 's' : '' }} livré{{
          bilan.livres > 1 ? 's' : '' }}. Bonne fin de journée.
      </span>
      <IonButton fill="outline" size="small" class="ion-margin-top"
                 @click="routeur.push('/gains')">
        Voir mes gains
      </IonButton>
    </div>

    <!-- Terminée AVEC des échecs : ce n'est pas la même chose, et envoyer
         quelqu'un vers ses gains à ce moment-là ne répond à rien (O-5). -->
    <div v-else class="etat-vide">
      <IonIcon :icon="alertCircleOutline" class="grande-icone alerte" />
      <b>Plus rien à livrer, mais {{ bilan.echoues }} échec{{
        bilan.echoues > 1 ? 's' : '' }}</b>
      <span>
        {{ bilan.livres }} arrêt{{ bilan.livres > 1 ? 's' : '' }} livré{{
          bilan.livres > 1 ? 's' : '' }} sur {{ bilan.total }}.
        Les colis non remis après deux passages repartent chez leur vendeur, et
        les clients sont prévenus — vous n'avez rien à faire de plus.
      </span>
      <IonButton fill="outline" size="small" class="ion-margin-top"
                 @click="routeur.push('/historique')">
        Voir le détail de ma journée
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
.grande-icone.alerte {
  color: #b8650f;
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
.suite {
  margin: 10px 0 0;
  padding: 10px 12px;
  border-radius: 10px;
  background: var(--accent-doux);
  font-size: 11.5px;
  line-height: 1.6;
  color: var(--rd-encre-douce);
}
</style>
