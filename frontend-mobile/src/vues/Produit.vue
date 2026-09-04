<script setup lang="ts">
// La fiche produit mobile.
//
// La barre du bas est **collante** : prix et bouton restent visibles pendant
// qu'on lit la description. Devoir remonter en haut de page pour acheter est
// l'irritant mobile le plus classique, et le plus facile à éviter.
import { IonBadge, IonButton, IonIcon, IonSpinner } from '@ionic/vue'
import { euros } from '@partage/metier'
import { notificationsOutline, starOutline } from 'ionicons/icons'
import { computed, ref } from 'vue'
import { useRoute } from 'vue-router'

import Ecran from '@/composants/Ecran.vue'
import { usePanier } from '@/magasins/panier'
import { useSession } from '@/magasins/session'
import { useRafraichissement } from '@/rafraichissement'

const route = useRoute()
const session = useSession()
const panier = usePanier()

type Media = { url: string; texte_alternatif: string; anime: boolean }

const produit = ref<Record<string, any> | null>(null)
const chargement = ref(true)

/**
 * Les vues du produit, dans l'ordre, l'apercu anime en dernier.
 *
 * Le mobile n'affichait que la photo principale, alors que le web avait une
 * galerie complete. Depuis le bloc N-1, un produit peut avoir une seule photo
 * comme quatre vues : la bande ne s'affiche donc que s'il y a de quoi la
 * remplir — un carrousel a une image est un carrousel casse.
 */
const medias = computed<Media[]>(() => {
  const fiche = produit.value
  if (!fiche) return []
  const vues: Media[] = (fiche.photos ?? []).map((photo: Record<string, string>) => ({
    url: photo.url,
    texte_alternatif: photo.texte_alternatif || fiche.nom,
    anime: false,
  }))
  if (!vues.length && fiche.image) {
    vues.push({ url: fiche.image, texte_alternatif: fiche.nom, anime: false })
  }
  if (fiche.apercu?.url) {
    vues.push({
      url: fiche.apercu.url,
      texte_alternatif: `${fiche.nom} — aperçu animé`,
      anime: true,
    })
  }
  return vues
})

const vueActive = ref(0)

/** Le point suit le doigt : sans lui, on ne sait pas combien il reste de vues. */
function suivreDefilement(evenement: Event) {
  const bande = evenement.target as HTMLElement
  vueActive.value = Math.round(bande.scrollLeft / bande.clientWidth)
}

/**
 * La fiche se recharge à chaque visite : un produit passé en rupture ou dont
 * le prix a changé depuis la dernière fois ne doit pas s'afficher tel qu'il
 * était il y a un quart d'heure (O-5).
 */
useRafraichissement(async () => {
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
      <!-- Une seule vue : une image, sans habillage inutile. Plusieurs : une
           bande qu'on fait defiler au pouce, avec un point par vue. -->
      <img
        v-if="medias.length === 1"
        :src="medias[0].url"
        :alt="medias[0].texte_alternatif"
        class="photo"
      />
      <div v-else-if="medias.length > 1" class="galerie">
        <div class="bande" @scroll.passive="suivreDefilement">
          <img
            v-for="(media, index) in medias"
            :key="index"
            :src="media.url"
            :alt="media.texte_alternatif"
            class="photo vue"
          />
        </div>
        <div class="points">
          <span
            v-for="(media, index) in medias"
            :key="index"
            :class="index === vueActive ? 'actif' : ''"
          />
        </div>
      </div>

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
.galerie {
  margin-bottom: 12px;
}
.bande {
  display: flex;
  gap: 8px;
  overflow-x: auto;
  scroll-snap-type: x mandatory;
  scrollbar-width: none;
}
.bande::-webkit-scrollbar {
  display: none;
}
.vue {
  flex: 0 0 100%;
  scroll-snap-align: center;
  margin-bottom: 0;
}
.points {
  display: flex;
  justify-content: center;
  gap: 6px;
  margin-top: 8px;
}
.points span {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--rd-trait);
  transition: background-color 150ms, width 150ms;
}
.points span.actif {
  width: 18px;
  border-radius: 3px;
  background: var(--accent);
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
