import { api } from './client'

/**
 * Le paiement, cote navigateur — D-12, D-18.
 *
 * Une seule chose est a comprendre ici : **le navigateur n'annonce jamais
 * qu'un paiement a reussi.** Il ouvre l'intention, laisse le fournisseur
 * faire son travail, puis demande au serveur ce qu'il en est. En production,
 * c'est le fournisseur qui previent le serveur ; le navigateur n'est qu'un
 * spectateur qui rafraichit.
 *
 * `confirmer` n'existe donc que parce que le mode simulation n'a personne
 * pour appeler le serveur a notre place. Le jour ou une cle Stripe arrive,
 * cette fonction disparait de l'ecran et rien d'autre ne bouge.
 */

export type Intention = {
  reference: string
  secret_client: string
  montant_centimes: number
  /** AUTORISE ou REFUSE — le simulateur refuse les montants finissant par 99 centimes. */
  statut: string
  simule: boolean
  reservation_expire_dans_minutes: number
  identifiant_paiement: number
}

export type ResultatPaiement = {
  statut: string
  commande?: string
  statut_commande?: string
  deja_traite?: boolean
}

export type LigneFacture = {
  boutique: string
  nom: string
  quantite: number
  prix_unitaire_centimes: number
  sous_total_centimes: number
}

export type Facture = {
  numero_facture: string | null
  numero_commande: string
  date: string
  adresse: string
  montant_produits_centimes: number
  montant_livraison_centimes: number
  montant_total_centimes: number
  montant_ht_centimes: number | null
  taux_tva: number
  lignes: LigneFacture[]
}

export const paiements = {
  ouvrir: (commande: number) =>
    api.post<Intention>(`/commandes/${commande}/paiement`, {}),
  abandonner: (commande: number) =>
    api.post<{ reservation_relachee: boolean }>(
      `/commandes/${commande}/paiement/abandonner`,
      {},
    ),
  confirmer: (reference: string) =>
    api.post<ResultatPaiement>('/paiements/confirmation', { reference }),
  facture: (commande: number) => api.get<Facture>(`/commandes/${commande}/facture`),
}
