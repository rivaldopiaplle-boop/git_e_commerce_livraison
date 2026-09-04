// Ce qui rend l'application vivante — O-5, O-7.
//
// **Ton reproche, et il était le bon** : *« surtout, surtout, surtout, surtout
// rien n'est synchronisé et dynamique »*, et *« les comptes mobile et web du
// client ne sont pas synchronisés »*.
//
// L'API, elle, l'était : le même compte voit le même panier, les mêmes
// adresses et les mêmes réglages depuis le web et depuis le téléphone. Le
// défaut était **entièrement côté écran**, et il tenait en une ligne : chaque
// vue chargeait ses données dans `onMounted`, et jamais plus.
//
// Or Ionic **ne démonte pas les vues** : il les garde en vie pour que le retour
// arrière soit instantané. `onMounted` ne se déclenche donc qu'une seule fois,
// à la première visite. On ajoutait un article depuis le web, on revenait sur
// l'onglet Panier du téléphone, et il affichait l'état d'il y a dix minutes.
// Rien ne le disait — c'est ce qui donne l'impression que « rien ne marche ».
//
// Trois moments de rafraîchissement, et chacun répond à une situation réelle :
//
//   1. **à l'entrée dans l'écran** (`ionViewWillEnter`) — on revient d'un
//      autre onglet, ou d'un écran de détail ;
//   2. **au retour dans l'application** (`visibilitychange`, `resume`) — le
//      téléphone était en veille, ou on était dans une autre application ;
//   3. **en fond, à intervalle**, uniquement quand l'écran est visible — c'est
//      ce qui fait avancer un suivi de commande sous les yeux du client, et
//      apparaître une course chez un livreur disponible.
//
// Le troisième est bridé volontairement : un appel toutes les vingt secondes
// sur un écran qui n'est pas regardé, c'est de la batterie et du forfait
// dépensés pour rien.
import { onIonViewDidLeave, onIonViewWillEnter } from '@ionic/vue'
import { onBeforeUnmount, onMounted } from 'vue'

/** L'intervalle par défaut. Assez court pour qu'un suivi bouge à l'œil,
 *  assez long pour ne pas marteler l'API. */
export const PERIODE_MS = 20_000

type Options = {
  /** Rafraîchir en fond tant que l'écran est visible. */
  periodique?: boolean
  /** L'intervalle, en millisecondes. */
  periode?: number
}

/**
 * Recharger `charger` aux trois moments qui comptent.
 *
 * À appeler à la place de `onMounted(charger)` dans une vue mobile.
 * Elle fait aussi le premier chargement : il n'y a rien à ajouter à côté.
 */
export function useRafraichissement(
  charger: () => unknown | Promise<unknown>,
  options: Options = {},
) {
  const periode = options.periode ?? PERIODE_MS
  let minuterie: ReturnType<typeof setInterval> | null = null
  let visible = true

  // Un rechargement déjà en vol ne se relance pas : sur un réseau lent, le
  // minuteur empilerait les appels et le dernier arrivé écraserait le plus
  // récent — l'écran clignoterait en arrière.
  let enCours = false
  async function relancer() {
    if (enCours || !visible) return
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
    visible = document.visibilityState === 'visible'
    if (visible) {
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
    // Capacitor émet `resume` quand l'application revient au premier plan.
    // Dans un navigateur, l'événement n'existe pas : `visibilitychange` suffit.
    document.addEventListener('resume', relancer)
  })

  // Ionic garde les vues en vie : c'est CET événement, et non `onMounted`, qui
  // marque un retour sur l'écran.
  onIonViewWillEnter(() => {
    visible = true
    relancer()
    demarrer()
  })

  onIonViewDidLeave(arreter)

  onBeforeUnmount(() => {
    arreter()
    document.removeEventListener('visibilitychange', surVisibilite)
    document.removeEventListener('resume', relancer)
  })

  return { relancer }
}
