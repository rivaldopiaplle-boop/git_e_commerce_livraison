<script setup lang="ts">
// La vignette produit du mobile — O-1, O-2, O-8.
//
// Elle sert partout : les carrousels de l'accueil, la grille de recherche, les
// suggestions d'une fiche. **Une seule définition** évite qu'un produit ait
// l'air différent selon l'écran où on le croise — c'était le cas, et c'est ce
// qui donne l'impression d'une application « détachée ».
//
// Deux choses la distinguent d'une simple image avec un prix :
//
//   · **elle est entièrement cliquable**, et le bouton d'ajout ne vole pas ce
//     clic (O-8). On tape la carte, on ouvre la fiche ; on tape le « + », on
//     ajoute sans quitter l'écran ;
//   · **elle dit ce qu'elle sait** : rupture, distance, mode de livraison. Une
//     vignette qui ne montre qu'un prix oblige à ouvrir la fiche pour
//     apprendre que le produit n'est pas disponible.
import { IonIcon, IonSpinner } from '@ionic/vue'
import { euros } from '@partage/metier'
import {
  addOutline, bicycleOutline, checkmarkOutline, cubeOutline, star,
} from 'ionicons/icons'
import { ref } from 'vue'
import { useRouter } from 'vue-router'

import { usePanier } from '@/magasins/panier'

type Produit = {
  id: number
  nom: string
  image?: string
  prix_centimes: number
  disponible?: boolean
  distance_km?: number | null
  boutique?: { nom: string; type_service?: string }
  /** La note publique. `sur` dit si elle porte sur le produit ou sa boutique :
   *  faire passer l'une pour l'autre serait un petit mensonge que les gens
   *  repèrent (O-5). */
  note?: { moyenne: number; nombre: number; sur: 'produit' | 'boutique' } | null
}

const proprietes = withDefaults(defineProps<{
  produit: Produit
  /** `carte` pour un carrousel horizontal, `tuile` pour une grille. */
  forme?: 'carte' | 'tuile'
}>(), { forme: 'carte' })

const routeur = useRouter()
const panier = usePanier()

const occupe = ref(false)
const ajoute = ref(false)

/**
 * Ajouter sans quitter l'écran.
 *
 * `stop` sur le clic : sans lui, le « + » ouvrirait aussi la fiche, et on se
 * retrouverait sur une page qu'on n'a pas demandée après chaque ajout.
 */
async function ajouter() {
  if (occupe.value || proprietes.produit.disponible === false) return
  occupe.value = true
  try {
    await panier.ajouter(proprietes.produit.id, 1)
    ajoute.value = true
    // La coche retombe : elle confirme le geste, elle ne devient pas un état.
    setTimeout(() => (ajoute.value = false), 1400)
  } finally {
    occupe.value = false
  }
}
</script>

<template>
  <button
    type="button"
    class="vignette"
    :class="forme"
    @click="routeur.push(`/produit/${produit.id}`)"
  >
    <span class="cadre">
      <img v-if="produit.image" :src="produit.image" :alt="produit.nom" loading="lazy" />
      <span v-else class="sans-image">{{ produit.nom.slice(0, 2).toUpperCase() }}</span>

      <span v-if="produit.disponible === false" class="voile-rupture">Rupture</span>

      <span
        v-else
        class="ajout"
        :class="ajoute ? 'fait' : ''"
        role="button"
        :aria-label="`Ajouter ${produit.nom} au panier`"
        @click.stop="ajouter"
      >
        <IonSpinner v-if="occupe" name="dots" />
        <IonIcon v-else :icon="ajoute ? checkmarkOutline : addOutline" />
      </span>
    </span>

    <span class="nom">{{ produit.nom }}</span>
    <span class="ligne">
      <b>{{ euros(produit.prix_centimes) }}</b>
      <span v-if="produit.boutique" class="boutique">
        <IonIcon
          :icon="produit.boutique.type_service === 'EXPRESS' ? bicycleOutline : cubeOutline"
        />
        {{ produit.boutique.nom }}
      </span>
    </span>
    <span class="bas">
      <!-- La note se lit AVANT d'ouvrir la fiche : c'est à ce moment-là qu'un
           avis sert à choisir entre deux produits (O-5). -->
      <span v-if="produit.note" class="note" :title="produit.note.sur === 'boutique'
        ? `Note de la boutique (${produit.note.nombre} avis)`
        : `Note du produit (${produit.note.nombre} avis)`">
        <IonIcon :icon="star" />
        {{ produit.note.moyenne }}
        <span class="portee">{{ produit.note.sur === 'boutique' ? 'boutique' : '' }}</span>
      </span>
      <span v-if="produit.distance_km != null" class="distance">
        {{ produit.distance_km }} km
      </span>
    </span>
  </button>
</template>

<style scoped>
.vignette {
  display: flex;
  flex-direction: column;
  gap: 3px;
  padding: 0;
  border: 0;
  background: none;
  text-align: left;
  min-width: 0;
}
.vignette.carte {
  width: 146px;
  flex: 0 0 146px;
}
.vignette.tuile {
  width: 100%;
}
.cadre {
  position: relative;
  display: block;
  width: 100%;
  aspect-ratio: 4 / 3;
  border-radius: 12px;
  overflow: hidden;
  background: var(--rd-trait-doux, #eef0f4);
  margin-bottom: 5px;
}
.cadre img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.sans-image {
  display: grid;
  place-items: center;
  width: 100%;
  height: 100%;
  font-size: 22px;
  font-weight: 800;
  color: var(--rd-encre-douce);
}
.voile-rupture {
  position: absolute;
  inset: 0;
  display: grid;
  place-items: center;
  background: rgba(15, 20, 32, 0.52);
  color: #fff;
  font-size: 12px;
  font-weight: 700;
}
.ajout {
  position: absolute;
  right: 6px;
  bottom: 6px;
  width: 30px;
  height: 30px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  background: #fff;
  color: var(--accent);
  font-size: 17px;
  box-shadow: 0 2px 6px rgb(15 20 32 / 0.22);
}
.ajout.fait {
  background: var(--accent);
  color: #fff;
}
.nom {
  font-size: 12.5px;
  font-weight: 600;
  line-height: 1.3;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.ligne {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 6px;
}
.ligne b {
  font-size: 13px;
  color: var(--accent);
}
.boutique {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  font-size: 10.5px;
  color: var(--rd-encre-douce);
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.bas {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 10.5px;
  color: var(--rd-encre-douce);
}
.note {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  font-weight: 700;
  color: var(--ion-text-color);
}
.note ion-icon {
  color: #e0a106;
  font-size: 11px;
}
.portee {
  font-weight: 400;
  color: var(--rd-encre-douce);
}
.distance {
  font-size: 10.5px;
}
</style>
