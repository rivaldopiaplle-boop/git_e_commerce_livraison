<script setup lang="ts">
// « Ma tournée » — l'écran du livreur Standard.
//
// Les arrêts sont **dans leur ordre**, et cet ordre ne se réorganise pas ici :
// c'est le gestionnaire d'entrepôt qui le valide en amont (D-86). Un livreur
// qui réordonnerait sa tournée casserait l'optimisation faite pour toute la
// zone.
import { IonBadge, IonIcon } from '@ionic/vue'
import { checkmarkCircle, listOutline, locationOutline } from 'ionicons/icons'
import { computed, defineAsyncComponent } from 'vue'
import { useRouter } from 'vue-router'

import Ecran from '@/composants/Ecran.vue'
import { useLivreur } from '@/magasins/livreur'
import { useRafraichissement } from '@/rafraichissement'

const livreur = useLivreur()
const routeur = useRouter()

useRafraichissement(() => livreur.charger(), { periodique: true })

/**
 * La tournée entière sur une carte, dans son ordre.
 *
 * Le livreur ne réordonne rien (D-86), mais **voir** la forme de sa journée
 * change tout : il sait s'il redescend une avenue ou s'il zigzague, et il
 * peut le dire à l'entrepôt. Une liste de quinze adresses ne dit jamais ça.
 */
const pointsTournee = computed(() =>
  (livreur.tournee?.arrets ?? [])
    .map((arret) => ({
      lat: Number(arret.livraison.adresse?.latitude),
      lon: Number(arret.livraison.adresse?.longitude),
      rang: arret.ordre,
    }))
    .filter((point) => Number.isFinite(point.lat) && Number.isFinite(point.lon)),
)

// MapLibre pese pres d'un mega-octet. Charge paresseusement, il n'arrive
// qu'au moment ou une carte s'affiche : un livreur en 4G ne telecharge pas un
// moteur de cartographie pour consulter ses gains.
const Carte = defineAsyncComponent(() => import('@/composants/Carte.vue'))
</script>

<template>
  <Ecran titre="Ma tournée" sous-titre="Livreur · Standard" :rafraichir="livreur.charger">
    <template v-if="livreur.tournee">
      <div class="carte-mobile resume">
        <div>
          <b>{{ livreur.tournee.entrepot }}</b>
          <span class="sous-titre">
            {{ livreur.tournee.zone ?? 'zone non définie' }} ·
            {{ livreur.tournee.nombre_arrets }} arrêts ·
            {{ livreur.tournee.distance_totale_km ?? '—' }} km
          </span>
        </div>
        <IonBadge>{{ livreur.tournee.libelle_statut }}</IonBadge>
      </div>

      <Carte v-if="pointsTournee.length > 1" :points="pointsTournee" profil="voiture"
             hauteur="220px" />

      <button
        v-for="arret in livreur.tournee.arrets"
        :key="arret.id"
        type="button"
        class="carte-mobile arret"
        :class="arret.statut === 'LIVRE' ? 'fait' : ''"
        @click="routeur.push('/arret')"
      >
        <span class="numero">
          <IonIcon v-if="arret.statut === 'LIVRE'" :icon="checkmarkCircle" />
          <template v-else>{{ arret.ordre }}</template>
        </span>
        <span class="detail">
          <b>{{ arret.livraison.client }}</b>
          <span class="sous-titre">
            <IonIcon :icon="locationOutline" />
            {{ arret.livraison.adresse?.rue }}, {{ arret.livraison.adresse?.ville }}
          </span>
        </span>
        <IonBadge :color="arret.statut === 'LIVRE' ? 'success' : 'medium'">
          {{ arret.libelle_statut }}
        </IonBadge>
      </button>

      <p class="note">
        L'ordre des arrêts est calculé par l'entrepôt pour raccourcir votre trajet.
        Il ne se change pas depuis le téléphone.
      </p>
    </template>

    <div v-else class="etat-vide">
      <IonIcon :icon="listOutline" class="grande-icone" />
      <b>Aucune tournée pour aujourd'hui</b>
      <span>
        Votre prochaine tournée apparaîtra ici dès que l'entrepôt vous l'aura affectée.
      </span>
    </div>
  </Ecran>
</template>

<style scoped>
.resume {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 10px;
}
.resume b {
  font-size: 14px;
}
.arret {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
  text-align: left;
  transition: transform 0.12s ease;
}
.arret:active {
  transform: scale(0.98);
}
.arret.fait {
  opacity: 0.55;
}
.numero {
  width: 30px;
  height: 30px;
  flex-shrink: 0;
  border-radius: 50%;
  display: grid;
  place-items: center;
  background: var(--accent);
  color: #fff;
  font-weight: 800;
  font-size: 12.5px;
}
.detail {
  flex: 1;
  min-width: 0;
}
.detail b {
  display: block;
  font-size: 13.5px;
}
.detail .sous-titre {
  display: flex;
  align-items: center;
  gap: 4px;
}
.grande-icone {
  font-size: 34px;
  color: var(--rd-trait);
}
.note {
  font-size: 11px;
  color: var(--rd-encre-douce);
  line-height: 1.55;
}
</style>
