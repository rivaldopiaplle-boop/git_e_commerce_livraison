import { api, appelerComplet } from './client'

const BASE = import.meta.env.VITE_API_URL ?? 'http://localhost:8000/api/v1'

export type Photo = { id: number; url: string; ordre: number; texte_alternatif: string }

/** Ce que le vendeur voit de SON produit — plus que la vignette du client.
 *
 *  Le catalogue vendeur recevait la meme charge utile que le catalogue
 *  public : ni le stock exact, ni le seuil d'alerte, ni `est_visible`. Il ne
 *  pouvait donc pas proposer de remettre en vente un produit masque : il ne
 *  savait meme pas qu'il l'etait.
 */
export type ProduitCatalogue = {
  id: number
  nom: string
  prix_centimes: number
  image: string
  disponible: boolean
  distance_km: number | null
  boutique: { id: number; nom: string; type_service: string; ville: string }
  categorie: { id: number; nom: string; slug: string } | null
  est_visible: boolean
  stock_disponible: number
  stock_reserve: number
  stock_commandable: number
  est_en_rupture: boolean
  seuil_alerte: number
  poids_grammes: number | null
  nombre_photos: number
  date_ajout: string
}

export type ProduitVendeur = {
  id: number
  nom: string
  description: string
  prix_unitaire_centimes: number
  categorie: number | null
  poids_grammes: number | null
  stock_disponible: number
  seuil_alerte: number
  est_visible: boolean
  image_principale_url: string
}

export type Mouvement = {
  id: number
  type: string
  libelle_type: string
  quantite: number
  motif: string
  stock_apres: number
  date_mouvement: string
  auteur: string
}

export type ResultatStock = {
  stock_disponible: number
  stock_commandable: number
  mouvement: Mouvement
}

let jetonCourant: string | null = null
export function poserJetonVendeur(jeton: string | null) {
  jetonCourant = jeton
}

/** Le televersement passe par `fetch` brut : un envoi multipart ne doit pas
 *  porter d'en-tete Content-Type fixe, le navigateur ecrit lui-meme la
 *  frontiere entre les fichiers. */
async function televerser(chemin: string, fichiers: File[]) {
  const corps = new FormData()
  for (const fichier of fichiers) corps.append('photos', fichier)

  const reponse = await fetch(`${BASE}${chemin}`, {
    method: 'POST',
    headers: jetonCourant ? { Authorization: `Bearer ${jetonCourant}` } : {},
    body: corps,
  })
  const donnees = await reponse.json().catch(() => null)
  if (!reponse.ok) {
    throw new Error(donnees?.erreur?.message ?? "Le televersement a echoue.")
  }
  return donnees.data as Photo[]
}

export const vendeur = {
  mesProduits: () => api.get<ProduitCatalogue[]>('/vendeurs/produits'),
  stockBas: () => api.get<ProduitCatalogue[]>('/vendeurs/stock-bas'),
  detail: (id: number | string) => appelerComplet<{ data: never }>(`/produits/${id}`),
  creer: (donnees: Partial<ProduitVendeur>) => api.post<never>('/vendeurs/produits', donnees),
  modifier: (id: number, donnees: Partial<ProduitVendeur>) =>
    api.patch<never>(`/vendeurs/produits/${id}`, donnees),

  /** Retirer de la vente, et l'inverse.
   *
   *  L'ecran ne savait que masquer : une fois le produit retire, plus aucun
   *  bouton ne permettait de le remettre en vente. Une action sans retour
   *  n'est pas une action, c'est un piege.
   */
  masquer: (id: number) => api.patch<never>(`/vendeurs/produits/${id}`, { est_visible: false }),
  remettreEnVente: (id: number) =>
    api.patch<never>(`/vendeurs/produits/${id}`, { est_visible: true }),

  photos: {
    ajouter: (id: number, fichiers: File[]) => televerser(`/produits/${id}/photos`, fichiers),
    ordonner: (id: number, ordre: number[]) =>
      api.patch<Photo[]>(`/produits/${id}/photos/ordre`, { ordre }),
    retirer: (id: number, idPhoto: number) =>
      api.supprimer<Photo[]>(`/produits/${id}/photos/${idPhoto}`),
  },

  stock: {
    /** Le stock reellement compte sur l'etagere, pas l'ecart a calculer de tete.
     *
     *  La maquette demande « Nouvelle quantite » : c'est ainsi qu'on fait un
     *  inventaire. Le serveur accepte les deux formes et deduit l'ecart.
     */
    definir: (id: number, nouvelleQuantite: number, type: string, motif: string) =>
      api.patch<ResultatStock>(`/produits/${id}/stock`, {
        nouvelle_quantite: nouvelleQuantite,
        type,
        motif,
      }),
    ajuster: (id: number, quantite: number, type: string, motif: string) =>
      api.patch<ResultatStock>(`/produits/${id}/stock`, { quantite, type, motif }),
    mouvements: (id: number) => api.get<Mouvement[]>(`/produits/${id}/mouvements`),
  },
}
