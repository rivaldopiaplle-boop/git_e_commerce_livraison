<script setup lang="ts">
// « Mes gains » — ce que le travail rapporte, course par course (D-29, D-91).
//
// Le livreur Standard est payé **à l'arrêt** : une tournée de dix arrêts ne
// vaut pas une tournée de trois. L'écran l'écrit en toutes lettres plutôt
// qu'un total sec, sinon personne ne comprend comment le chiffre est fait.
import { IonIcon } from '@ionic/vue'
import { euros, jour } from '@partage/metier'
import { walletOutline } from 'ionicons/icons'
import { computed, onMounted } from 'vue'

import Ecran from '@/composants/Ecran.vue'
import { useLivreur } from '@/magasins/livreur'
import { useSession } from '@/magasins/session'

const livreur = useLivreur()
const session = useSession()

onMounted(() => livreur.charger())

const moyenne = computed(() =>
  livreur.gains.courses_terminees
    ? livreur.gains.total_centimes / livreur.gains.courses_terminees
    : 0,
)
</script>

<template>
  <Ecran titre="Mes gains" sous-titre="Livreur" :rafraichir="livreur.charger">
    <div class="carte-mobile total">
      <IonIcon :icon="walletOutline" />
      <b>{{ euros(livreur.gains.total_centimes) }}</b>
      <span>
        {{ livreur.gains.courses_terminees }} livraisons ·
        {{ euros(moyenne) }} en moyenne ·
        {{ livreur.gains.distance_km.toFixed(1) }} km
      </span>
    </div>

    <p class="explication">
      {{ session.modeLivraison === 'STANDARD'
        ? 'En Standard, vous êtes payé à l’arrêt : une tournée de dix arrêts ne vaut pas une tournée de trois.'
        : 'En Express, chaque course est payée selon sa distance, par bandes.' }}
      Un gain est acquis à la confirmation de livraison, et suspendu si un litige est
      ouvert sur la commande — jamais versé puis repris.
    </p>

    <h2 class="titre-section">Le détail</h2>
    <div v-for="course in livreur.terminees" :key="course.id" class="carte-mobile ligne">
      <span class="detail">
        <b>{{ course.client }}</b>
        <span class="sous-titre">
          {{ course.numero_commande }} · {{ jour(course.date_reelle) }} ·
          {{ course.distance_km }} km
        </span>
      </span>
      <b class="montant">{{ euros(course.remuneration_livreur_centimes) }}</b>
    </div>

    <div v-if="!livreur.terminees.length" class="etat-vide">
      <b>Aucune livraison terminée</b>
      <span>Vos gains apparaîtront ici dès votre première livraison confirmée.</span>
    </div>
  </Ecran>
</template>

<style scoped>
.total {
  text-align: center;
  padding: 20px;
}
.total ion-icon {
  font-size: 22px;
  color: var(--accent);
}
.total b {
  display: block;
  font-size: 30px;
  font-weight: 800;
  margin: 4px 0 2px;
}
.total span {
  font-size: 11.5px;
  color: var(--rd-encre-douce);
}
.explication {
  font-size: 11.5px;
  line-height: 1.6;
  color: var(--rd-encre-douce);
  margin: 0 0 16px;
}
.titre-section {
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--rd-encre-douce);
  margin: 0 0 8px;
}
.ligne {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}
.detail b {
  display: block;
  font-size: 13px;
}
.montant {
  font-size: 14px;
  color: var(--accent);
}
</style>
