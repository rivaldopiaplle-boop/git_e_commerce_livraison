<script setup lang="ts">
// « À proximité » — les courses Express à prendre, les plus proches d'abord.
//
// Accepter est une **action instantanée** : pas de popup, pas de navigation,
// juste un retour visuel puis la bascule vers « Ma course » (D-60). Quand on
// est à vélo au feu rouge, une confirmation en deux écrans fait rater la
// course.
import { IonButton, IonIcon, IonSpinner } from '@ionic/vue'
import { euros } from '@partage/metier'
import { Geolocation } from '@capacitor/geolocation'
import { locationOutline, storefrontOutline } from 'ionicons/icons'
import { computed, defineAsyncComponent, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import Ecran from '@/composants/Ecran.vue'
import { useLivreur } from '@/magasins/livreur'
import { useSession } from '@/magasins/session'

const livreur = useLivreur()
const session = useSession()
const routeur = useRouter()

const occupe = ref(0)
const erreur = ref('')
const moi = ref<{ lat: number; lon: number } | null>(null)

/**
 * Les courses libres, sur une carte.
 *
 * La liste dit « 2,4 km » ; elle ne dit pas si la course part dans la
 * direction où l'on va déjà. Deux courses à la même distance ne se valent pas
 * quand l'une est à l'opposé (N-5). On ne trace aucun itinéraire ici : c'est
 * un choix qu'on fait d'un coup d'œil, pas un trajet qu'on suit.
 */
const pointsCourses = computed(() => {
  const points = livreur.disponibles
    .map((course, rang) => ({
      lat: Number(course.adresse?.latitude),
      lon: Number(course.adresse?.longitude),
      rang: rang + 1,
      libelle: `${course.client} — ${course.adresse?.ville ?? ''}`,
    }))
    .filter((point) => Number.isFinite(point.lat) && Number.isFinite(point.lon))
  return moi.value ? [{ ...moi.value, depart: true }, ...points] : points
})

/** On envoie la position AVANT de demander la liste : c'est elle qui décide
 *  du tri, et une liste non triée oblige à comparer huit adresses de tête. */
async function charger() {
  try {
    const p = await Geolocation.getCurrentPosition({ timeout: 4000 })
    moi.value = { lat: p.coords.latitude, lon: p.coords.longitude }
    await session.client.post('/livreurs/position', {
      latitude: p.coords.latitude,
      longitude: p.coords.longitude,
    })
  } catch {
    // Sans position, le serveur rend la liste non triée plutôt que rien.
  }
  await livreur.chargerDisponibles()
}

onMounted(charger)

async function prendre(identifiant: number) {
  occupe.value = identifiant
  erreur.value = ''
  try {
    await livreur.accepter(identifiant)
    routeur.push('/courses')
  } catch (echec) {
    erreur.value = echec instanceof Error ? echec.message : 'Course indisponible.'
    await livreur.chargerDisponibles()
  } finally {
    occupe.value = 0
  }
}

// MapLibre pese pres d'un mega-octet. Charge paresseusement, il n'arrive
// qu'au moment ou une carte s'affiche : un livreur en 4G ne telecharge pas un
// moteur de cartographie pour consulter ses gains.
const Carte = defineAsyncComponent(() => import('@/composants/Carte.vue'))
</script>

<template>
  <Ecran titre="À proximité" sous-titre="Livreur · Express" :rafraichir="charger">
    <p v-if="erreur" class="erreur">{{ erreur }}</p>

    <!-- Où sont les courses, avant de lire ce qu'elles rapportent -->
    <Carte v-if="pointsCourses.length" :points="pointsCourses" :itineraire="false"
           hauteur="200px" />

    <div v-for="course in livreur.disponibles" :key="course.id" class="carte-mobile">
      <div class="entete">
        <b>{{ course.client }}</b>
        <span class="gain">{{ euros(course.remuneration_livreur_centimes) }}</span>
      </div>
      <p class="trajet">
        <IonIcon :icon="storefrontOutline" /> {{ course.boutiques.join(', ') }}
        <br />
        <IonIcon :icon="locationOutline" />
        {{ course.adresse?.code_postal }} {{ course.adresse?.ville }}
        <span v-if="course.distance_km"> · {{ course.distance_km }} km</span>
      </p>
      <IonButton expand="block" size="small" :disabled="occupe === course.id"
                 @click="prendre(course.id)">
        <IonSpinner v-if="occupe === course.id" name="dots" />
        <span v-else>Prendre cette course</span>
      </IonButton>
    </div>

    <div v-if="!livreur.disponibles.length" class="etat-vide">
      <IonIcon :icon="locationOutline" class="grande-icone" />
      <b>Aucune course disponible</b>
      <span>
        Soit rien n'est libre près de vous, soit vous avez déjà une course en cours —
        on n'en prend qu'une à la fois.
      </span>
      <IonButton fill="outline" size="small" class="ion-margin-top"
                 @click="routeur.push('/courses')">
        Voir ma course
      </IonButton>
    </div>
  </Ecran>
</template>

<style scoped>
.entete {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}
.entete b {
  font-size: 14px;
}
.gain {
  font-weight: 800;
  color: var(--accent);
}
.trajet {
  margin: 8px 0 12px;
  font-size: 12.5px;
  color: var(--rd-encre-douce);
  line-height: 1.7;
}
.trajet ion-icon {
  vertical-align: -2px;
  margin-right: 4px;
}
.grande-icone {
  font-size: 34px;
  color: var(--rd-trait);
}
.erreur {
  color: #9c2116;
  font-size: 12.5px;
}
</style>
