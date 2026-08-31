<script setup lang="ts">
// Le catalogue mobile.
//
// Grille verticale : c'est de la recherche active, on veut tout voir (D-69).
// Le bouton d'ajout est **visible en permanence** et large d'au moins 44 px —
// il n'y a pas de survol sur un téléphone pour révéler une action, et le pouce
// doit le retrouver sans réfléchir d'une carte à l'autre.
import {
  IonBadge, IonButton, IonIcon, IonSearchbar, IonSegment, IonSegmentButton, IonSpinner,
} from '@ionic/vue'
import type { Produit } from '@partage/types'
import { euros } from '@partage/metier'
import { addOutline, bagHandleOutline, notificationsOutline } from 'ionicons/icons'
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'

import Ecran from '@/composants/Ecran.vue'
import { usePanier } from '@/magasins/panier'
import { useSession } from '@/magasins/session'

const session = useSession()
const panier = usePanier()
const routeur = useRouter()

const produits = ref<Produit[]>([])
const recherche = ref('')
const service = ref('')
const chargement = ref(false)

async function charger() {
  chargement.value = true
  try {
    const parametres = new URLSearchParams()
    if (recherche.value.trim()) parametres.set('recherche', recherche.value.trim())
    if (service.value) parametres.set('type_service', service.value)
    const suffixe = parametres.toString() ? `?${parametres}` : ''
    produits.value = await session.client.get<Produit[]>(`/produits${suffixe}`)
  } finally {
    chargement.value = false
  }
}

onMounted(charger)
// On attend que la frappe se calme : une requête par lettre saturerait le
// réseau d'un téléphone en 4G.
let minuteur: ReturnType<typeof setTimeout>
watch([recherche, service], () => {
  clearTimeout(minuteur)
  minuteur = setTimeout(charger, 300)
})

const nombre = computed(() => panier.contenu.nombre_articles)
</script>

<template>
  <Ecran titre="Catalogue" sous-titre="Espace client" :rafraichir="charger">
    <template #actions>
      <IonButton fill="clear" @click="routeur.push('/panier')">
        <IonIcon slot="icon-only" :icon="bagHandleOutline" style="color: #fff" />
        <IonBadge v-if="nombre" color="light" class="pastille">{{ nombre }}</IonBadge>
      </IonButton>
    </template>

    <IonSearchbar
      v-model="recherche"
      placeholder="Un burger, un casque…"
      :debounce="0"
      class="recherche"
    />
    <IonSegment v-model="service" class="filtre">
      <IonSegmentButton value="">Tout</IonSegmentButton>
      <IonSegmentButton value="EXPRESS">Express</IonSegmentButton>
      <IonSegmentButton value="STANDARD">Standard</IonSegmentButton>
    </IonSegment>

    <div v-if="chargement" class="chargement"><IonSpinner name="dots" /></div>

    <div v-else class="grille">
      <article v-for="produit in produits" :key="produit.id" class="produit"
               @click="routeur.push(`/produit/${produit.id}`)">
        <div class="image">
          <img v-if="produit.image" :src="produit.image" :alt="produit.nom"
               :class="produit.disponible ? '' : 'indispo'" />
          <IonBadge v-if="!produit.disponible" color="danger" class="rupture">Rupture</IonBadge>
          <!-- Zone tactile de 44 px, toujours au même endroit. -->
          <button
            type="button"
            class="ajouter"
            :aria-label="produit.disponible ? 'Ajouter au panier' : 'Être prévenu du retour'"
            @click.stop="produit.disponible
              ? panier.ajouter(produit.id)
              : routeur.push(`/produit/${produit.id}`)"
          >
            <IonIcon :icon="produit.disponible ? addOutline : notificationsOutline" />
          </button>
        </div>
        <b class="nom">{{ produit.nom }}</b>
        <span class="boutique">{{ produit.boutique.nom }}</span>
        <span class="prix">{{ euros(produit.prix_centimes) }}</span>
      </article>
    </div>

    <div v-if="!chargement && !produits.length" class="etat-vide">
      <b>Aucun produit ne livre chez vous</b>
      <span>
        Les boutiques Express trop lointaines n'apparaissent jamais ici : mieux vaut un
        catalogue court qu'une promesse intenable.
      </span>
    </div>
  </Ecran>
</template>

<style scoped>
.pastille {
  position: absolute;
  top: 2px;
  right: 2px;
  font-size: 9px;
}
.recherche {
  --background: #fff;
  --border-radius: 12px;
  padding: 0 0 8px;
}
.filtre {
  margin-bottom: 12px;
}
.chargement {
  display: grid;
  place-items: center;
  padding: 40px;
}
.grille {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}
.produit {
  background: #fff;
  border: 1px solid var(--rd-trait-doux);
  border-radius: 14px;
  overflow: hidden;
  padding-bottom: 10px;
  transition: transform 0.12s ease;
}
.produit:active {
  transform: scale(0.97);
}
.image {
  position: relative;
  aspect-ratio: 4 / 3;
  background: var(--rd-atelier);
}
.image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.image img.indispo {
  opacity: 0.4;
  filter: grayscale(1);
}
.rupture {
  position: absolute;
  top: 6px;
  left: 6px;
  font-size: 9.5px;
}
.ajouter {
  position: absolute;
  right: 6px;
  bottom: 6px;
  width: 44px;
  height: 44px;
  border: none;
  border-radius: 12px;
  background: var(--accent);
  color: #fff;
  display: grid;
  place-items: center;
  box-shadow: 0 3px 8px rgba(15, 20, 32, 0.2);
}
.ajouter ion-icon {
  font-size: 20px;
}
.nom {
  display: block;
  font-size: 12.5px;
  padding: 8px 10px 0;
}
.boutique {
  display: block;
  font-size: 11px;
  color: var(--rd-encre-douce);
  padding: 0 10px;
}
.prix {
  display: block;
  font-size: 13.5px;
  font-weight: 800;
  color: var(--accent);
  padding: 4px 10px 0;
}
</style>
