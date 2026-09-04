<script setup lang="ts">
// La carte, côté téléphone — D-142.
//
// Même moteur que le web (MapLibre GL JS) et même fond de carte, choisi une
// seule fois dans `@partage/carte`. Ce qui change est l'usage : sur un
// téléphone, la carte n'est pas une illustration à côté d'une liste, **c'est
// l'écran**. On la manipule au pouce, donc le défilement à un doigt reste
// actif — contrairement au web, où il volerait la molette à la page.
//
// Le tracé est demandé au serveur : la clé d'itinéraire n'a rien à faire dans
// une application qu'on installe, où elle serait lisible par n'importe qui.
import { CENTRE_PAR_DEFAUT, cadre, styleDeCarte, type Point } from '@partage/carte'
import * as maplibre from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'

import { useSession } from '@/magasins/session'

const proprietes = withDefaults(defineProps<{
  points: Point[]
  profil?: 'velo' | 'voiture' | 'pieton'
  itineraire?: boolean
  hauteur?: string
}>(), {
  profil: 'velo',
  itineraire: true,
  hauteur: '240px',
})

const session = useSession()
const conteneur = ref<HTMLElement | null>(null)
const resume = ref<{ distance_km: number; duree_minutes: number; simule: boolean } | null>(null)

let carte: maplibre.Map | null = null
let marqueurs: maplibre.Marker[] = []

function pastille(point: Point) {
  const element = document.createElement('div')
  element.className = 'pastille-carte'
  if (point.depart) element.classList.add('depart')
  element.textContent = point.depart ? '' : String(point.rang ?? '')
  return element
}

const situes = () => proprietes.points.filter(
  (point) => Number.isFinite(point.lat) && Number.isFinite(point.lon),
)

function poser() {
  if (!carte) return
  marqueurs.forEach((marqueur) => marqueur.remove())
  marqueurs = situes().map((point) =>
    new maplibre.Marker({ element: pastille(point) })
      .setLngLat([point.lon, point.lat])
      .addTo(carte as maplibre.Map),
  )
  const limites = cadre(situes())
  if (limites) carte.fitBounds(limites, { padding: 48, maxZoom: 15, duration: 0 })
}

async function tracer() {
  if (!carte || !proprietes.itineraire || situes().length < 2) return
  try {
    const trajet = await session.client.post<{
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
          'line-width': 5,
          'line-opacity': 0.9,
        },
      })
    }
    // Pointillés pour une estimation, trait plein pour un itinéraire réel :
    // un livreur doit savoir si le trajet affiché suit vraiment les rues.
    carte.setPaintProperty('trajet', 'line-dasharray', trajet.simule ? [2, 1.6] : [1, 0])
  } catch {
    // Une carte sans tracé reste utile : les pastilles disent où aller.
  }
}

onMounted(() => {
  if (!conteneur.value) return
  const premier = situes()[0]
  carte = new maplibre.Map({
    container: conteneur.value,
    style: styleDeCarte(),
    center: premier ? [premier.lon, premier.lat] : CENTRE_PAR_DEFAUT,
    zoom: 13,
    attributionControl: { compact: true },
  })
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
  <div class="cadre-carte">
    <div ref="conteneur" :style="{ height: hauteur }" />
    <div v-if="resume" class="bandeau">
      <b>{{ resume.distance_km }} km</b>
      <span>environ {{ resume.duree_minutes }} min</span>
      <span class="mention">{{ resume.simule ? 'estimé' : 'itinéraire réel' }}</span>
    </div>
  </div>
</template>

<style>
/* Non `scoped` : les pastilles sont créées en JavaScript. */
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
  box-shadow: 0 2px 6px rgb(15 20 32 / 0.3);
}
.pastille-carte.depart {
  width: 16px;
  height: 16px;
  background: #0f1420;
}
</style>

<style scoped>
.cadre-carte {
  overflow: hidden;
  border-radius: 14px;
  border: 1px solid var(--rd-trait);
  margin-bottom: 12px;
}
.bandeau {
  display: flex;
  align-items: baseline;
  gap: 8px;
  padding: 8px 12px;
  border-top: 1px solid var(--rd-trait);
  background: var(--rd-atelier, #fbfbfd);
  font-size: 12px;
  color: var(--rd-encre-douce);
}
.bandeau b {
  font-size: 13.5px;
  color: var(--ion-text-color);
}
.mention {
  margin-left: auto;
  font-size: 10.5px;
}
</style>
