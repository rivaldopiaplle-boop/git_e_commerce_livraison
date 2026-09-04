<script setup lang="ts">
// La carte — D-142.
//
// **MapLibre GL JS**, et pas Leaflet : les tuiles sont vectorielles, donc le
// texte reste net à tous les niveaux de zoom, la rotation existe, et le rendu
// ressemble à celui d'une vraie application de livraison plutôt qu'à une
// mosaïque d'images. C'est ce que tu as demandé au bloc N-5 — *« une vraie API
// de carte sophistiquée »*.
//
// MapLibre est la branche libre de Mapbox GL, sous licence BSD : pas de clé,
// pas de compteur d'affichages, pas de conditions qui changent. Le fond de
// carte, lui, vient d'`@partage/carte` — OpenFreeMap sans clé par défaut.
//
// **Le trajet est demandé au serveur** (`POST /itineraire`) et non calculé
// ici : la clé d'itinéraire ne doit jamais partir dans le navigateur. Elle,
// contrairement à la clé de tuiles, est un vrai secret.
import { CENTRE_PAR_DEFAUT, cadre, styleDeCarte, type Point } from '@partage/carte'
import * as maplibre from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'

import { api } from '../api/client'

const proprietes = withDefaults(defineProps<{
  points: Point[]
  /** Le mode de déplacement : il change la durée et le tracé. */
  profil?: 'velo' | 'voiture' | 'pieton'
  /** Sans tracé, la carte ne montre que les pastilles. */
  itineraire?: boolean
  hauteur?: string
}>(), {
  profil: 'voiture',
  itineraire: true,
  hauteur: '320px',
})

const conteneur = ref<HTMLElement | null>(null)
const resume = ref<{ distance_km: number; duree_minutes: number; simule: boolean } | null>(null)
const erreur = ref('')

let carte: maplibre.Map | null = null
let marqueurs: maplibre.Marker[] = []

/** Une pastille dessinée à la main : les marqueurs par défaut sont énormes. */
function pastille(point: Point) {
  const element = document.createElement('div')
  element.className = 'pastille-carte'
  if (point.depart) element.classList.add('depart')
  element.textContent = point.depart ? '' : String(point.rang ?? '')
  element.title = point.libelle ?? ''
  return element
}

function situes() {
  return proprietes.points.filter(
    (point) => Number.isFinite(point.lat) && Number.isFinite(point.lon),
  )
}

function poser() {
  if (!carte) return
  marqueurs.forEach((marqueur) => marqueur.remove())
  marqueurs = situes().map((point) => {
    const marqueur = new maplibre.Marker({ element: pastille(point) })
      .setLngLat([point.lon, point.lat])
    if (point.libelle) {
      marqueur.setPopup(new maplibre.Popup({ offset: 14 }).setText(point.libelle))
    }
    return marqueur.addTo(carte as maplibre.Map)
  })

  const limites = cadre(situes())
  if (limites) {
    carte.fitBounds(limites, { padding: 56, maxZoom: 15, duration: 0 })
  }
}

/**
 * Le tracé, demandé au serveur.
 *
 * Un tracé estimé — ligne droite entre les points — est dessiné en
 * **pointillés**, un tracé routier réel en trait plein. Faire passer l'un pour
 * l'autre serait exactement le genre de détail qui trahit un travail bâclé.
 */
async function tracer() {
  if (!carte || !proprietes.itineraire || situes().length < 2) return
  try {
    const trajet = await api.post<{
      distance_km: number
      duree_minutes: number
      trace: [number, number][]
      simule: boolean
    }>('/itineraire', {
      points: situes().map((point) => ({ lat: point.lat, lon: point.lon })),
      profil: proprietes.profil,
    })
    resume.value = trajet

    const donnees = {
      type: 'Feature' as const,
      properties: {},
      geometry: { type: 'LineString' as const, coordinates: trajet.trace },
    }
    const source = carte.getSource('trajet') as maplibre.GeoJSONSource | undefined
    if (source) {
      source.setData(donnees)
    } else {
      carte.addSource('trajet', { type: 'geojson', data: donnees })
      carte.addLayer({
        id: 'trajet',
        type: 'line',
        source: 'trajet',
        layout: { 'line-cap': 'round', 'line-join': 'round' },
        paint: {
          'line-color': getComputedStyle(document.documentElement)
            .getPropertyValue('--accent').trim() || '#2563eb',
          'line-width': 4,
          'line-opacity': 0.85,
        },
      })
    }
    // Pointillés pour une estimation, trait plein pour un itinéraire réel.
    carte.setPaintProperty('trajet', 'line-dasharray', trajet.simule ? [2, 1.6] : [1, 0])
  } catch {
    // Une carte sans tracé reste utile : les pastilles disent déjà où aller.
    erreur.value = 'Tracé indisponible.'
  }
}

onMounted(() => {
  if (!conteneur.value) return
  const premier = situes()[0]
  carte = new maplibre.Map({
    container: conteneur.value,
    style: styleDeCarte(),
    center: premier ? [premier.lon, premier.lat] : CENTRE_PAR_DEFAUT,
    zoom: 12,
    // Les commandes du clavier restent, celles de la molette partent : une
    // carte qui capture le défilement au milieu d'une page longue est
    // l'irritant le plus commun des cartes intégrées.
    scrollZoom: false,
    attributionControl: { compact: true },
  })
  carte.addControl(new maplibre.NavigationControl({ showCompass: false }), 'top-right')
  carte.on('load', () => {
    poser()
    tracer()
  })
})

watch(() => proprietes.points, () => {
  poser()
  tracer()
}, { deep: true })

onBeforeUnmount(() => {
  carte?.remove()
  carte = null
})
</script>

<template>
  <div class="overflow-hidden rounded-2xl border border-trait">
    <div ref="conteneur" :style="{ height: hauteur }" class="w-full" />
    <div
      v-if="resume || erreur"
      class="flex items-center justify-between gap-3 border-t border-trait bg-atelier
             px-3.5 py-2 text-[12px] text-encre-douce"
    >
      <span v-if="resume">
        <b class="text-encre">{{ resume.distance_km }} km</b> ·
        environ {{ resume.duree_minutes }} min
      </span>
      <span v-else>{{ erreur }}</span>
      <!-- La carte dit ce qu'elle montre. Un trace estime annonce en toutes
           lettres qu'il est estime. -->
      <span v-if="resume" class="text-[11px]">
        {{ resume.simule ? 'trajet estimé (vol d’oiseau majoré)' : 'itinéraire routier réel' }}
      </span>
    </div>
  </div>
</template>

<style>
/* Non `scoped` : les pastilles sont créées en JavaScript, donc hors du
   périmètre que Vue sait marquer. */
.pastille-carte {
  width: 26px;
  height: 26px;
  border-radius: 50%;
  background: var(--accent);
  color: #fff;
  display: grid;
  place-items: center;
  font-size: 12px;
  font-weight: 800;
  border: 2px solid #fff;
  box-shadow: 0 2px 6px rgb(15 20 32 / 0.28);
  cursor: pointer;
}
.pastille-carte.depart {
  width: 16px;
  height: 16px;
  background: var(--encre, #0f1420);
}
</style>
