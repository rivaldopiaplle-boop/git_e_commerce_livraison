// Les types du domaine, partagés par le web et le mobile.
//
// Ils décrivent ce que l'API renvoie. Les dupliquer dans les deux fronts
// serait la garantie qu'ils divergent au troisième correctif — et une
// divergence de type ne se voit pas : elle se découvre en production, quand un
// écran affiche « undefined ».

export type Role = 'CLIENT' | 'VENDEUR' | 'GESTIONNAIRE' | 'LIVREUR' | 'ADMIN'
export type TypeService = 'EXPRESS' | 'STANDARD'

export type Utilisateur = {
  id: number
  email: string
  nom: string
  prenom: string
  telephone: string
  role: Role
  statut_compte: 'ACTIF' | 'EN_ATTENTE_VALIDATION' | 'SUSPENDU' | 'DESACTIVE'
}

export type Boutique = {
  id: number
  nom: string
  type_service: TypeService
  ville: string
}

export type Produit = {
  id: number
  nom: string
  prix_centimes: number
  image: string
  disponible: boolean
  distance_km: number | null
  boutique: Boutique
}

export type LignePanier = {
  id: number
  quantite: number
  prix_capture_centimes: number
  sous_total_centimes: number
  prix_a_change: boolean
  produit: Produit & { stock_commandable: number }
}

export type Panier = {
  id: number | null
  lignes: LignePanier[]
  nombre_articles: number
  total_centimes: number
  boutiques: string[]
}

export type StatutCommande =
  | 'EN_ATTENTE_PAIEMENT' | 'PAYEE' | 'EN_PREPARATION' | 'PRETE'
  | 'EXPEDIEE_ENTREPOT' | 'RECUE_ENTREPOT' | 'EN_TOURNEE' | 'EN_LIVRAISON'
  | 'LIVREE' | 'ANNULEE' | 'REMBOURSEE' | 'ECHEC_LIVRAISON'

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
  type_service?: TypeService
  date_commande?: string
  suites_possibles?: string[]
}

export type Commande = {
  id: number
  numero_commande: string
  type_service: TypeService
  statut_actuel: StatutCommande
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

export type StatutLivraison =
  | 'A_ATTRIBUER' | 'ATTRIBUEE' | 'RECUPEREE' | 'EN_ROUTE'
  | 'LIVREE' | 'ECHOUEE' | 'ANNULEE'

export type AdresseLivraison = {
  id: number
  libelle: string
  rue: string
  code_postal: string
  ville: string
  instructions: string
}

export type Livraison = {
  id: number
  numero_commande: string
  type_service: TypeService
  statut_livraison: StatutLivraison
  libelle_statut: string
  statut_commande: StatutCommande
  client: string
  adresse: AdresseLivraison | null
  boutiques: string[]
  distance_km: string | null
  remuneration_livreur_centimes: number
  code_confirmation: string
  date_estimee: string | null
  date_reelle: string | null
  nombre_tentatives: number
}

export type Arret = {
  id: number
  ordre: number
  statut: 'A_FAIRE' | 'LIVRE' | 'ECHOUE' | 'REPORTE'
  libelle_statut: string
  heure_estimee: string | null
  livraison: Livraison
}

export type Tournee = {
  id: number
  entrepot: string
  zone: string | null
  livreur: { id: number; nom: string; vehicule: string } | null
  statut: 'BROUILLON' | 'PRETE' | 'AFFECTEE' | 'EN_COURS' | 'TERMINEE'
  libelle_statut: string
  nombre_arrets: number
  distance_totale_km: string | null
  date_creation: string
  date_debut: string | null
  date_fin: string | null
  arrets: Arret[]
}

export type Notification = {
  id: number
  titre: string
  contenu: string
  lien: string
  date: string
  lue: boolean
}

/** L'enveloppe d'erreur de l'API — la même partout (contrat-api.md). */
export type ErreurApi = {
  code: string
  message: string
  details: Record<string, string[]>
}
