// Le panier mobile.
//
// Il existe AVANT le compte (D-03) : on remplit son panier, et le compte n'est
// exigé qu'au moment de commander. La clé de session est engendrée par
// l'appareil et gardée localement — c'est elle qui identifie un panier sans
// compte, et elle disparaît à la fusion.
import type { Panier } from '@partage/types'
import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

import { useSession } from './session'

const CLE = 'rivdinde.mobile.panier'
const VIDE: Panier = {
  id: null, lignes: [], nombre_articles: 0, total_centimes: 0, boutiques: [],
}

function cleDeSession() {
  let cle = localStorage.getItem(CLE)
  if (!cle) {
    cle = crypto.randomUUID()
    localStorage.setItem(CLE, cle)
  }
  return cle
}

export const usePanier = defineStore('panier', () => {
  const session = useSession()
  const contenu = ref<Panier>({ ...VIDE })
  const occupe = ref(false)
  const erreur = ref('')

  session.client.poserCleSession(cleDeSession())

  const plusieursBoutiques = computed(() => contenu.value.boutiques.length > 1)

  async function charger() {
    try {
      contenu.value = await session.client.get<Panier>('/panier')
    } catch {
      contenu.value = { ...VIDE }
    }
  }

  async function ajouter(idProduit: number, quantite = 1) {
    occupe.value = true
    erreur.value = ''
    try {
      contenu.value = await session.client.post<Panier>('/panier/lignes', {
        produit: idProduit,
        quantite,
      })
    } catch (echec) {
      erreur.value = echec instanceof Error ? echec.message : 'Ajout impossible.'
    } finally {
      occupe.value = false
    }
  }

  async function changerQuantite(idLigne: number, quantite: number) {
    occupe.value = true
    try {
      contenu.value = await session.client.patch<Panier>(
        `/panier/lignes/${idLigne}`,
        { quantite },
      )
    } finally {
      occupe.value = false
    }
  }

  /** Repartir d'un panier vierge : à la déconnexion, comme au web (D-55). */
  function reinitialiser() {
    contenu.value = { ...VIDE, lignes: [] }
    localStorage.removeItem(CLE)
    session.client.poserCleSession(cleDeSession())
  }

  return { contenu, occupe, erreur, plusieursBoutiques,
           charger, ajouter, changerQuantite, reinitialiser }
})
