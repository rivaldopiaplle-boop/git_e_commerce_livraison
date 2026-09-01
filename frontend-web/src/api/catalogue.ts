import type { Produit } from '../composants/CarteProduit.vue'
import type { BoutiqueFacette, Univers } from '../stores/catalogue'
import { api, appelerComplet } from './client'

export type Boutique = {
  id: number
  nom: string
  type_service: string
  description: string
  ville: string
  note_moyenne: string | null
  nombre_produits: number
  distance_km: number | null
}
export type AvisPublic = {
  id: number
  note: number
  commentaire: string
  date: string
  auteur: string
  porte_sur: string
}

export type ProduitDetail = Produit & {
  description: string
  stock_disponible: number
  poids_grammes: number | null
  photos: { id: number; url: string; texte_alternatif: string }[]
  /** L'apercu anime, quand le vendeur en a un. `genre` dit s'il faut un
   *  `<video>` ou une simple image : deviner depuis l'extension marcherait
   *  aujourd'hui et casserait le jour ou une URL Cloudinary arrive sans. */
  apercu: { url: string; genre: 'video' | 'image' } | null
  categorie: { id: number; nom: string; slug: string } | null
  // Ce qu'un acheteur lit avant d'acheter (D-71).
  avis: {
    nombre: number
    note_moyenne: number | null
    repartition: Record<string, number>
    avis: AvisPublic[]
  }
  produits_similaires: {
    id: number
    nom: string
    prix_centimes: number
    image: string
    disponible: boolean
  }[]
}
export type ReponseCatalogue = {
  data: Produit[]
  meta: {
    total: number
    total_avant_filtres: number
    facettes: { univers: Univers[]; boutiques: BoutiqueFacette[] }
  }
}

function avec(position: string, extra: Record<string, string | undefined> = {}) {
  const morceaux = [
    position,
    ...Object.entries(extra)
      .filter(([, v]) => v)
      .map(([c, v]) => `${c}=${encodeURIComponent(v as string)}`),
  ]
  const requete = morceaux.filter(Boolean).join('&')
  return requete ? `?${requete}` : ''
}

export const catalogue = {
  // On demande le corps complet ici : les facettes vivent dans `meta`.
  produits: (position: string, filtres: Record<string, string | undefined> = {}) =>
    appelerComplet<ReponseCatalogue>(`/produits${avec(position, filtres)}`),
  produit: (id: number | string, position: string) =>
    api.get<ProduitDetail>(`/produits/${id}${avec(position)}`),
  boutiques: (position: string) => api.get<Boutique[]>(`/boutiques${avec(position)}`),
}
