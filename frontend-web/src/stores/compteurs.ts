import { defineStore } from 'pinia'
import { ref } from 'vue'

import { api } from '../api/client'

/**
 * Ce qui attend la personne connectée, entrée de menu par entrée de menu.
 *
 * La barre latérale listait des noms d'écrans, et rien de plus : il fallait
 * ouvrir chacun pour découvrir qu'il y avait trois commandes à préparer et
 * deux litiges en souffrance (L-3).
 *
 * Le serveur renvoie un dictionnaire **indexé par nom de route**, ce qui garde
 * la barre latérale bête : elle affiche `compteurs[entree.route]` sans rien
 * savoir des métiers. Un écran de plus dans le menu ne demande rien ici tant
 * qu'il n'a rien à compter.
 */
export const useCompteurs = defineStore('compteurs', () => {
  const valeurs = ref<Record<string, number>>({})
  const dernierAppel = ref(0)

  /**
   * Rafraîchir, au plus une fois toutes les vingt secondes.
   *
   * Sans ce garde-fou, chaque navigation déclencherait un appel : un back-office
   * où l'on passe d'un écran à l'autre en tapant en ferait dix par minute, pour
   * des chiffres qui ne bougent pas si vite.
   */
  async function rafraichir(force = false) {
    const maintenant = Date.now()
    if (!force && maintenant - dernierAppel.value < 20_000) return
    dernierAppel.value = maintenant
    try {
      valeurs.value = await api.get<Record<string, number>>('/moi/compteurs')
    } catch {
      // Une pastille absente vaut mieux qu'un écran cassé : c'est un
      // agrément, pas une donnée dont dépend la navigation.
      valeurs.value = {}
    }
  }

  /** À la déconnexion : sinon le compte suivant hériterait des pastilles. */
  function reinitialiser() {
    valeurs.value = {}
    dernierAppel.value = 0
  }

  return { valeurs, rafraichir, reinitialiser }
})
