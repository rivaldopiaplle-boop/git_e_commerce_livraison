<script setup lang="ts">
// La fiche produit mobile.
//
// La barre du bas est **collante** : prix et bouton restent visibles pendant
// qu'on lit la description. Devoir remonter en haut de page pour acheter est
// l'irritant mobile le plus classique, et le plus facile à éviter.
import { IonBadge, IonButton, IonIcon, IonSpinner } from '@ionic/vue'
import { euros } from '@partage/metier'
import { notificationsOutline, starOutline } from 'ionicons/icons'
import { onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'

import Ecran from '@/composants/Ecran.vue'
import { usePanier } from '@/magasins/panier'
import { useSession } from '@/magasins/session'

const route = useRoute()
const session = useSession()
const panier = usePanier()

const produit = ref<Record<string, any> | null>(null)
const chargement = ref(true)

onMounted(async () => {
  try {
    produit.value = await session.client.get(`/produits/${route.params.id}`)
  } finally {
    chargement.value = false
  }
})
</script>

<template>
  <Ecran :titre="produit?.nom ?? 'Produit'" sous-titre="Fiche produit">
    <div v-if="chargement" class="chargement"><IonSpinner name="dots" /></div>

    <template v-else-if="produit">
      <img v-if="produit.image" :src="produit.image" :alt="produit.nom" class="photo" />

      <div class="carte-mobile">
        <IonBadge :color="produit.boutique.type_service === 'EXPRESS' ? 'warning' : 'medium'">
          {{ produit.boutique.type_service === 'EXPRESS' ? 'Express' : 'Standard' }}
        </IonBadge>
        <h1>{{ produit.nom }}</h1>
        <span class="sous-titre">
          {{ produit.boutique.nom }} · {{ produit.boutique.ville }}
        </span>
        <p class="description">{{ produit.description }}</p>
      </div>

      <div v-if="produit.avis?.nombre" class="carte-mobile">
        <div class="note">
          <IonIcon :icon="starOutline" />
          <b>{{ produit.avis.note_moyenne }} / 5</b>
          <span class="sous-titre">{{ produit.avis.nombre }} avis</span>
        </div>
        <div v-for="avis in produit.avis.avis.slice(0, 4)" :key="avis.id" class="avis">
          <b>{{ avis.auteur }} · {{ avis.note }}/5</b>
          <span>{{ avis.commentaire }}</span>
        </div>
      </div>

      <!-- La barre collante : elle suit le défilement. -->
      <div class="barre">
        <span class="prix">{{ euros(produit.prix_centimes) }}</span>
        <IonButton
          v-if="produit.disponible"
          :disabled="panier.occupe"
          @click="panier.ajouter(produit.id)"
        >
          Ajouter au panier
        </IonButton>
        <IonButton v-else fill="outline">
          <IonIcon slot="start" :icon="notificationsOutline" />
          Me prévenir
        </IonButton>
      </div>
    </template>
  </Ecran>
</template>

<style scoped>
.chargement {
  display: grid;
  place-items: center;
  padding: 40px;
}
.photo {
  width: 100%;
  aspect-ratio: 4 / 3;
  object-fit: cover;
  border-radius: 14px;
  margin-bottom: 12px;
}
h1 {
  font-size: 19px;
  margin: 8px 0 2px;
}
.description {
  margin: 12px 0 0;
  font-size: 13px;
  line-height: 1.6;
  color: var(--rd-encre-douce);
}
.note {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 10px;
}
.note ion-icon {
  color: var(--accent);
}
.avis {
  border-top: 1px solid var(--rd-trait-doux);
  padding: 8px 0;
  font-size: 12px;
}
.avis b {
  display: block;
  font-size: 12px;
}
.avis span {
  color: var(--rd-encre-douce);
}
.barre {
  position: sticky;
  bottom: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  background: #fff;
  border-top: 1px solid var(--rd-trait);
  margin: 12px -14px -24px;
  padding: 10px 14px calc(10px + env(safe-area-inset-bottom));
}
.prix {
  font-size: 20px;
  font-weight: 800;
  color: var(--accent);
}
</style>
