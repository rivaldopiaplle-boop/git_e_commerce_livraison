import { api } from './client'

export type ApercuCommande = {
  type_service: string
  boutiques: string[]
  articles: number
  montant_produits_centimes: number
  montant_livraison_centimes: number
}

export type LigneCommande = {
  id: number
  nom_produit_capture: string
  prix_unitaire_centimes: number
  quantite: number
  sous_total_centimes: number
  image: string
}

export type SousCommande = {
  id: number
  boutique: string
  statut_preparation: string
  libelle_statut: string
  montant_vendeur_centimes: number
  montant_commission_centimes: number
  lignes: LigneCommande[]
  numero_commande?: string
  type_service?: string
  date_commande?: string
  suites_possibles?: string[]
  /** Ou part le colis (D-74). Le vendeur n'a droit qu'a la ville et au code
   *  postal : il prepare un colis, il n'a pas a connaitre l'etage de
   *  quelqu'un. Le livreur, lui, recoit l'adresse complete. */
  destination?: { ville: string; code_postal: string } | null
  /** Qui a fait avancer cette commande, et quand (D-80). Le vendeur et son
   *  personnel travaillaient sur la meme file sans jamais savoir lequel des
   *  deux avait deja agi. */
  dernier_acte?: { qui: string; quand: string; statut: string } | null
  /** Les mots du circuit pour chaque suite possible (D-81). Un restaurant
   *  « signale prête », un expéditeur « expédie vers l'entrepôt » : même
   *  statut technique, deux gestes différents. Le serveur les donne, l'écran
   *  ne les devine pas. */
  libelles_suites?: Record<string, string>
  /** Depuis combien de temps cette part attend, et si le délai annoncé au
   *  client est dépassé (D-81). `minutes` est nul aux étapes terminées :
   *  compter le temps d'attente d'une commande expédiée n'a pas de sens. */
  attente?: {
    minutes: number | null
    en_retard: boolean
    delai_minutes: number | null
  }
  /** Rendu par l'annulation seule (D-144). */
  montant_rembourse_centimes?: number
}

export type Commande = {
  id: number
  numero_commande: string
  type_service: string
  statut_actuel: string
  libelle_statut: string
  montant_produits_centimes: number
  montant_livraison_centimes: number
  montant_total_centimes: number
  date_commande: string
  date_livraison_estimee: string | null
  adresse: string
  boutiques: string[]
  sous_commandes: SousCommande[]
}

export const commandes = {
  apercu: () =>
    api.get<{
      commandes: ApercuCommande[]
      total_centimes: number
      // Les lignes qu'on ne peut pas commander, nommement. Sans elles,
      // l'ecran ne pouvait qu'echouer sans dire quoi retirer.
      lignes_bloquantes: {
        id_ligne: number
        id_produit: number
        nom: string
        quantite: number
        code: string
        message: string
        disponible?: number
      }[]
    }>('/panier/apercu-commandes'),
  creer: (corps: object) => api.post<Commande[]>('/commandes', corps),
  miennes: () => api.get<Commande[]>('/mes-commandes'),
  recues: () => api.get<SousCommande[]>('/vendeurs/commandes'),
  /**
   * Faire avancer une part de commande d'un cran.
   *
   * `details` ne sert qu'à l'annulation, qui exige un motif classé et une
   * explication (D-07, D-144). Le reste des transitions n'a rien à porter.
   */
  avancer: (id: number, statut: string, details?: { motif: string; explication: string }) =>
    api.patch<SousCommande>(`/vendeurs/sous-commandes/${id}`, { statut, ...details }),
}
