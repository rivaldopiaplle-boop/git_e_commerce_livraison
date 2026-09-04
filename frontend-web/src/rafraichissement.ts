// Les écrans de travail ne restent pas figés — O-5.
//
// Le pendant web de `frontend-mobile/src/rafraichissement.ts`. Le défaut n'y
// est pas le même, et il est plus discret : sur le web, changer de page
// remonte le composant, donc les données se rechargent. **Mais on ne change
// pas de page.**
//
// Un vendeur laisse « Commandes reçues » ouvert toute la journée dans un
// onglet. Un gestionnaire d'entrepôt garde ses colis à l'écran. Un livreur
// suit sa course. Aucun des trois ne voit rien arriver tant qu'il ne
// rafraîchit pas à la main — et rien à l'écran ne lui dit que ce qu'il regarde
// date de deux heures.
//
// Deux moments, donc :
//
//   1. **au retour sur l'onglet** — on revient de sa boîte mail, et la file a
//      bougé pendant ce temps ;
//   2. **en fond, à intervalle**, et uniquement quand l'onglet est visible.
//      Un onglet en arrière-plan qui appelle l'API toutes les vingt secondes
//      pendant huit heures est du gaspillage pur.
import { onBeforeUnmount, onMounted } from 'vue'

/** Assez court pour qu'une commande apparaisse « toute seule », assez long
 *  pour ne pas marteler l'API. */
export const PERIODE_MS = 20_000

type Options = {
  /** Recharger en fond tant que l'onglet est visible. */
  periodique?: boolean
  periode?: number
}

/**
 * Recharger `charger` au retour sur l'onglet, et éventuellement en fond.
 *
 * Elle fait aussi le premier chargement : elle remplace `onMounted(charger)`,
 * elle ne s'y ajoute pas.
 */
export function useRafraichissement(
  charger: () => unknown | Promise<unknown>,
  options: Options = {},
) {
  const periode = options.periode ?? PERIODE_MS
  let minuterie: ReturnType<typeof setInterval> | null = null

  // Un rechargement déjà en vol ne se relance pas : sur un réseau lent, le
  // minuteur empilerait les appels et une réponse ancienne pourrait écraser
  // une plus récente — la liste se remettrait à jour à l'envers.
  let enCours = false
  async function relancer() {
    if (enCours || document.visibilityState !== 'visible') return
    enCours = true
    try {
      await charger()
    } finally {
      enCours = false
    }
  }

  function demarrer() {
    if (!options.periodique || minuterie) return
    minuterie = setInterval(relancer, periode)
  }

  function arreter() {
    if (minuterie) clearInterval(minuterie)
    minuterie = null
  }

  function surVisibilite() {
    if (document.visibilityState === 'visible') {
      relancer()
      demarrer()
    } else {
      arreter()
    }
  }

  onMounted(() => {
    relancer()
    demarrer()
    document.addEventListener('visibilitychange', surVisibilite)
  })

  onBeforeUnmount(() => {
    arreter()
    document.removeEventListener('visibilitychange', surVisibilite)
  })

  return { relancer }
}
