// Le panier, disponible AVANT toute inscription (D-03).
//
// Un visiteur anonyme est identifie par une cle qu'il engendre lui-meme et
// garde dans son navigateur. A la connexion, le serveur fusionne ce panier
// avec celui du compte : sans cela, un visiteur qui remplit son panier puis se
// connecte le retrouve vide, et il ne revient pas.
import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

import { api, poserCleSession } from '../api/client'

export type LignePanier = {
  id: number
  quantite: number
  prix_capture_centimes: number
  sous_total_centimes: number
  prix_a_change: boolean
  produit: {
    id: number
    nom: string
    prix_centimes: number
    image: string
    stock_commandable: number
    boutique: { id: number; nom: string; type_service: string }
  }
}

export type Panier = {
  id: number | null
  lignes: LignePanier[]
  nombre_articles: number
  total_centimes: number
  boutiques: string[]
}

const CLE = 'rivdinde.panier.session'
const VIDE: Panier = { id: null, lignes: [], nombre_articles: 0, total_centimes: 0, boutiques: [] }

function cleDeSession() {
  let cle = localStorage.getItem(CLE)
  if (!cle) {
    cle = crypto.randomUUID()
    localStorage.setItem(CLE, cle)
  }
  return cle
}

export const usePanier = defineStore('panier', () => {
  const contenu = ref<Panier>({ ...VIDE })
  const ouvert = ref(false)
  const occupe = ref(false)
  const erreur = ref('')

  const nombreArticles = computed(() => contenu.value.nombre_articles)
  const total = computed(() =>
    (contenu.value.total_centimes / 100).toLocaleString('fr-FR', {
      style: 'currency',
      currency: 'EUR',
    }),
  )
  // Plusieurs boutiques dans un panier donneront plusieurs commandes (D-10).
  // Autant le dire des le panier plutot qu'a la surprise du paiement.
  const plusieursBoutiques = computed(() => contenu.value.boutiques.length > 1)

  function demarrer() {
    poserCleSession(cleDeSession())
    return charger()
  }

  async function charger() {
    try {
      contenu.value = await api.get<Panier>('/panier')
    } catch {
      contenu.value = { ...VIDE }
    }
  }

  async function ajouter(idProduit: number, quantite = 1) {
    occupe.value = true
    erreur.value = ''
    try {
      contenu.value = await api.post<Panier>('/panier/lignes', {
        produit: idProduit,
        quantite,
      })
      ouvert.value = true
    } catch (echec) {
      erreur.value = echec instanceof Error ? echec.message : 'Ajout impossible.'
    } finally {
      occupe.value = false
    }
  }

  async function changerQuantite(idLigne: number, quantite: number) {
    occupe.value = true
    erreur.value = ''
    try {
      contenu.value = await api.patch<Panier>(`/panier/lignes/${idLigne}`, { quantite })
    } catch (echec) {
      erreur.value = echec instanceof Error ? echec.message : 'Modification impossible.'
    } finally {
      occupe.value = false
    }
  }

  async function retirer(idLigne: number) {
    occupe.value = true
    try {
      contenu.value = await api.supprimer<Panier>(`/panier/lignes/${idLigne}`)
    } finally {
      occupe.value = false
    }
  }

  /** Retire d'un geste tout ce qui n'est plus commandable. */
  async function nettoyer() {
    occupe.value = true
    erreur.value = ''
    try {
      const resultat = await api.post<Panier & { retirees: { nom: string }[] }>(
        '/panier/nettoyer',
      )
      contenu.value = resultat
      return resultat.retirees ?? []
    } finally {
      occupe.value = false
    }
  }

  /** Repartir d'un panier vierge, avec une nouvelle cle de navigateur.
   *
   *  Appele a la deconnexion. Sans cela, le panier du compte qui vient de
   *  partir restait affiche a la personne suivante devant la machine : les
   *  articles etaient encore a l'ecran alors que le serveur, lui, renvoyait
   *  bien un panier vide.
   */
  function reinitialiser() {
    contenu.value = { ...VIDE, lignes: [] }
    ouvert.value = false
    erreur.value = ''
    localStorage.removeItem(CLE)
    poserCleSession(cleDeSession())
  }

  return {
    contenu, ouvert, occupe, erreur,
    nombreArticles, total, plusieursBoutiques,
    demarrer, charger, ajouter, changerQuantite, retirer, nettoyer, reinitialiser,
  }
})
