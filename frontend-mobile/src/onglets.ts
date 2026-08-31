// Les cinq onglets du bas, et le « + » au milieu (règle d'or n°10, D-89).
//
// La règle, posée dès le bloc A : *« les 5 onglets de gauche à droite du plus
// important au moins important, et le troisième est le "+" qui cache les
// boutons de priorité moyenne, qui se déplie vers le bas »*.
//
// Ce qui compte autant que la liste elle-même : **même position, même fonction
// logique** dans les deux modes du livreur. La position 2 est toujours « mon
// travail actuel », la 4 toujours « ce qui vient ». C'est ce qui permet de
// passer d'un mode à l'autre sans réapprendre l'interface.
import {
  bagHandleOutline, bicycleOutline, homeOutline, listOutline, locationOutline,
  navigateOutline, personOutline, receiptOutline, searchOutline, walletOutline,
} from 'ionicons/icons'

export type Onglet = {
  cle: string
  libelle: string
  icone: string
  route: string
  /** Le troisième emplacement : il déplie les actions de priorité moyenne. */
  estLePlus?: boolean
}

export type ActionDepliee = {
  libelle: string
  icone: string
  route: string
  aide: string
}

/** Le client — le seul rôle présent sur les deux supports (D-40). */
export const ONGLETS_CLIENT: Onglet[] = [
  { cle: 'accueil', libelle: 'Accueil', icone: homeOutline, route: '/accueil' },
  { cle: 'recherche', libelle: 'Recherche', icone: searchOutline, route: '/recherche' },
  { cle: 'plus', libelle: '', icone: bagHandleOutline, route: '', estLePlus: true },
  { cle: 'commandes', libelle: 'Commandes', icone: receiptOutline, route: '/commandes' },
  { cle: 'profil', libelle: 'Profil', icone: personOutline, route: '/profil' },
]

export const PLUS_CLIENT: ActionDepliee[] = [
  { libelle: 'Mon panier', icone: bagHandleOutline, route: '/panier',
    aide: 'Ce que vous vous apprêtez à commander' },
  { libelle: 'Mes adresses', icone: locationOutline, route: '/adresses',
    aide: "C'est elle qui décide des boutiques Express visibles" },
  { libelle: 'Boutiques', icone: listOutline, route: '/boutiques',
    aide: 'Naviguer par vendeur plutôt que par produit' },
]

/** Le livreur Express : une course à la fois. */
export const ONGLETS_LIVREUR_EXPRESS: Onglet[] = [
  { cle: 'accueil', libelle: 'Aujourd’hui', icone: homeOutline, route: '/accueil' },
  { cle: 'courses', libelle: 'Ma course', icone: bicycleOutline, route: '/courses' },
  { cle: 'plus', libelle: '', icone: walletOutline, route: '', estLePlus: true },
  { cle: 'proximite', libelle: 'À proximité', icone: locationOutline, route: '/proximite' },
  { cle: 'profil', libelle: 'Profil', icone: personOutline, route: '/profil' },
]

/** Le livreur Standard : une tournée, des arrêts ordonnés. */
export const ONGLETS_LIVREUR_STANDARD: Onglet[] = [
  { cle: 'accueil', libelle: 'Aujourd’hui', icone: homeOutline, route: '/accueil' },
  { cle: 'tournee', libelle: 'Ma tournée', icone: listOutline, route: '/tournee' },
  { cle: 'plus', libelle: '', icone: walletOutline, route: '', estLePlus: true },
  { cle: 'arret', libelle: 'Prochain arrêt', icone: navigateOutline, route: '/arret' },
  { cle: 'profil', libelle: 'Profil', icone: personOutline, route: '/profil' },
]

export const PLUS_LIVREUR: ActionDepliee[] = [
  { libelle: 'Mes gains', icone: walletOutline, route: '/gains',
    aide: 'Détail par course, et ce qui est bloqué par un litige' },
  { libelle: 'Historique', icone: receiptOutline, route: '/historique',
    aide: 'Toutes vos livraisons passées' },
  { libelle: 'Aide et support', icone: personOutline, route: '/aide',
    aide: 'Signaler un problème sur une livraison' },
]

export function ongletsDuRole(role: string | null, mode: string): Onglet[] {
  if (role === 'LIVREUR') {
    return mode === 'STANDARD' ? ONGLETS_LIVREUR_STANDARD : ONGLETS_LIVREUR_EXPRESS
  }
  return ONGLETS_CLIENT
}

export function actionsDepliees(role: string | null): ActionDepliee[] {
  return role === 'LIVREUR' ? PLUS_LIVREUR : PLUS_CLIENT
}
