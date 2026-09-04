<script setup lang="ts">
// L'historique des livraisons, tous statuts confondus.
//
// Les échecs y figurent au même titre que les réussites : un livreur doit
// pouvoir montrer qu'il est passé deux fois avant qu'un colis reparte.
import { IonBadge, IonIcon, IonSegment, IonSegmentButton } from '@ionic/vue'
import { jour, tonDuStatut } from '@partage/metier'
import { receiptOutline } from 'ionicons/icons'
import { computed, ref } from 'vue'

import Ecran from '@/composants/Ecran.vue'
import { useLivreur } from '@/magasins/livreur'
import { useRafraichissement } from '@/rafraichissement'

const livreur = useLivreur()
const filtre = ref('toutes')

useRafraichissement(() => livreur.charger())

const TONS: Record<string, string> = {
  succes: 'success', erreur: 'danger', cours: 'primary', attente: 'warning', neutre: 'medium',
}

const visibles = computed(() => {
  const toutes = [...livreur.terminees, ...livreur.enCours]
  if (filtre.value === 'livrees') {
    return toutes.filter((c) => c.statut_livraison === 'LIVREE')
  }
  if (filtre.value === 'echecs') {
    return toutes.filter((c) => c.statut_livraison === 'ECHOUEE')
  }
  return toutes
})
</script>

<template>
  <Ecran titre="Historique" sous-titre="Livreur" :rafraichir="livreur.charger">
    <IonSegment v-model="filtre" class="filtre">
      <IonSegmentButton value="toutes">Toutes</IonSegmentButton>
      <IonSegmentButton value="livrees">Livrées</IonSegmentButton>
      <IonSegmentButton value="echecs">Échecs</IonSegmentButton>
    </IonSegment>

    <div v-for="course in visibles" :key="course.id" class="carte-mobile ligne">
      <span class="detail">
        <b>{{ course.client }}</b>
        <span class="sous-titre">
          {{ course.numero_commande }} · {{ jour(course.date_reelle ?? course.date_estimee) }}
          <template v-if="course.nombre_tentatives > 1">
            · {{ course.nombre_tentatives }} tentatives
          </template>
        </span>
      </span>
      <IonBadge :color="TONS[tonDuStatut(course.statut_livraison)]">
        {{ course.libelle_statut }}
      </IonBadge>
    </div>

    <div v-if="!visibles.length" class="etat-vide">
      <IonIcon :icon="receiptOutline" class="grande-icone" />
      <b>Rien à cet état</b>
      <span>Vos livraisons passées apparaîtront ici.</span>
    </div>
  </Ecran>
</template>

<style scoped>
.filtre {
  margin-bottom: 12px;
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
.grande-icone {
  font-size: 34px;
  color: var(--rd-trait);
}
</style>
