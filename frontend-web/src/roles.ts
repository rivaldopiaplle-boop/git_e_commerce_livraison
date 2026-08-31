// Ce que chaque role voit, de quelle couleur, et sur quel support.
//
// La barre laterale suit **entree par entree** celle de la maquette
// (`04-maquettes/maquettes.html`), et les couleurs viennent de la regle d'or
// n°8 : une couleur dominante par role, jamais sur les couleurs de sens.
//
// Trois regles apprises a mes depens :
//   · un espace de travail ne renvoie PAS au catalogue public. Aucun
//     back-office marchand ne le fait ;
//   · le gestionnaire n'est pas un vendeur au rabais : il prepare, il compte,
//     il ne voit ni les prix ni le chiffre d'affaires (D-04) ;
//   · « gestionnaire » recouvre deux metiers, et il faut le dire dans le menu :
//     le staff d'un vendeur prepare des commandes, celui d'un entrepot charge
//     des tournees (D-05).
import {
  BadgeCheck, BarChart3, Bike, Boxes, ClipboardList, LayoutDashboard, MapPin,
  Package, Receipt, Route, ScrollText, Settings, ShieldCheck, ShoppingBag,
  Star, Store, Truck, UserRound, Users, Wallet, Warehouse,
} from '@lucide/vue'
import type { Component } from 'vue'

import type { Role } from './stores/authentification'

export type EntreeNavigation = {
  libelle: string
  icone: Component
  route?: string
  /** Grisee dans la maquette : l'entree existe, l'acces est refuse. */
  interdite?: boolean
  prochainement?: boolean
}

/** Un visiteur sans compte est un futur client : il en porte les couleurs. */
export type RoleAffiche = Role | 'VISITEUR' | 'GESTIONNAIRE_ENTREPOT'

type DescriptionRole = {
  espace: string
  accent: string
  accentDoux: string
  /** Ou ce role travaille reellement (D-40). */
  plateforme: 'web' | 'mobile' | 'web+mobile'
  /** Le panneau droit : le panier n'a de sens que pour qui achete (D-46). */
  panneau: 'panier' | 'activite'
  navigation: EntreeNavigation[]
}

export const ROLES: Record<RoleAffiche, DescriptionRole> = {
  VISITEUR: {
    espace: 'Catalogue',
    accent: '#16a34a',
    accentDoux: '#e8f8ee',
    plateforme: 'web+mobile',
    panneau: 'panier',
    navigation: [
      { libelle: 'Catalogue', icone: ShoppingBag, route: 'vitrine' },
      { libelle: 'Boutiques', icone: Store, route: 'boutiques' },
      { libelle: 'Vendre ou livrer', icone: Users, route: 'rejoindre' },
    ],
  },
  CLIENT: {
    espace: 'Espace client',
    accent: '#16a34a',
    accentDoux: '#e8f8ee',
    plateforme: 'web+mobile',
    panneau: 'panier',
    navigation: [
      { libelle: 'Catalogue', icone: ShoppingBag, route: 'vitrine' },
      { libelle: 'Boutiques', icone: Store, route: 'boutiques' },
      { libelle: 'Mes commandes', icone: Receipt, route: 'mes-commandes' },
      { libelle: 'Mes adresses', icone: MapPin, route: 'mes-adresses' },
      { libelle: 'Mon compte', icone: LayoutDashboard, route: 'espace' },
      { libelle: 'Mon profil', icone: UserRound, route: 'profil' },
      { libelle: 'Parametres', icone: Settings, route: 'parametres' },
    ],
  },
  VENDEUR: {
    espace: 'Espace vendeur',
    accent: '#2563eb',
    accentDoux: '#eaf0ff',
    plateforme: 'web',
    panneau: 'activite',
    navigation: [
      { libelle: 'Tableau de bord', icone: LayoutDashboard, route: 'espace' },
      { libelle: 'Commandes recues', icone: ClipboardList, route: 'vendeur-commandes' },
      // Catalogue et stock ne font qu'un ecran (D-79) : ce sont deux vues
      // du meme objet, et les separer obligeait a garder deux boutons de
      // correction du stock pour la meme action.
      { libelle: 'Mon catalogue', icone: Package, route: 'vendeur-catalogue' },
      { libelle: 'Mon personnel', icone: Users, route: 'vendeur-personnel' },
      { libelle: 'Statistiques', icone: BarChart3, route: 'vendeur-statistiques' },
      { libelle: 'Mon profil', icone: UserRound, route: 'profil' },
      { libelle: 'Parametres', icone: Settings, route: 'parametres' },
    ],
  },
  // Staff d'un vendeur — Nadia. Elle prepare et elle compte.
  GESTIONNAIRE: {
    espace: 'Preparation',
    accent: '#0d9488',
    accentDoux: '#e6f7f4',
    plateforme: 'web',
    panneau: 'activite',
    navigation: [
      { libelle: 'A preparer', icone: ClipboardList, route: 'vendeur-commandes' },
      { libelle: 'Stock', icone: Boxes, route: 'vendeur-catalogue' },
      { libelle: 'Vue d ensemble', icone: LayoutDashboard, route: 'espace' },
      // Grisee, exactement comme dans la maquette : l'entree existe pour que
      // l'employe sache que la donnee existe et qu'elle ne lui est pas due.
      { libelle: 'Chiffre d affaires', icone: Wallet, interdite: true },
      { libelle: 'Mon profil', icone: UserRound, route: 'profil' },
      { libelle: 'Parametres', icone: Settings, route: 'parametres' },
    ],
  },
  // Staff d'un entrepot — Samir. Il recoit des colis et monte des tournees.
  GESTIONNAIRE_ENTREPOT: {
    espace: 'Entrepot',
    accent: '#0d9488',
    accentDoux: '#e6f7f4',
    plateforme: 'web',
    panneau: 'activite',
    navigation: [
      { libelle: 'Vue d ensemble', icone: LayoutDashboard, route: 'espace' },
      { libelle: 'Colis recus', icone: Warehouse, route: 'entrepot-colis' },
      { libelle: 'Tournees', icone: Route, route: 'entrepot-tournees' },
      { libelle: 'Mon profil', icone: UserRound, route: 'profil' },
      { libelle: 'Parametres', icone: Settings, route: 'parametres' },
    ],
  },
  LIVREUR: {
    espace: 'Espace livreur',
    accent: '#7c3aed',
    accentDoux: '#f3edff',
    plateforme: 'mobile',
    panneau: 'activite',
    navigation: [
      { libelle: 'Vue d ensemble', icone: LayoutDashboard, route: 'espace' },
      { libelle: 'Mes courses', icone: Bike, route: 'livreur-courses' },
      { libelle: 'Ma tournee', icone: Truck, route: 'livreur-courses' },
      { libelle: 'Mes gains', icone: Wallet, route: 'livreur-courses' },
      { libelle: 'Mon profil', icone: UserRound, route: 'profil' },
      { libelle: 'Parametres', icone: Settings, route: 'parametres' },
    ],
  },
  ADMIN: {
    espace: 'Administration',
    accent: '#b91c1c',
    accentDoux: '#fdebe9',
    plateforme: 'web',
    panneau: 'activite',
    navigation: [
      { libelle: 'Tableau de bord', icone: LayoutDashboard, route: 'espace' },
      { libelle: 'Validations', icone: ShieldCheck, route: 'admin-validations' },
      { libelle: 'Boutiques', icone: Store, route: 'admin-boutiques' },
      { libelle: 'Utilisateurs', icone: Users, route: 'admin-utilisateurs' },
      { libelle: 'Litiges', icone: Star, route: 'admin-litiges' },
      { libelle: 'Demandes d identite', icone: BadgeCheck, route: 'admin-demandes' },
      { libelle: "Journal d'audit", icone: ScrollText, route: 'admin-journal' },
      { libelle: 'Mon profil', icone: UserRound, route: 'profil' },
      { libelle: 'Parametres', icone: Settings, route: 'parametres' },
    ],
  },
}

/** Le role d'affichage : il tient compte du sous-type du gestionnaire. */
export function descriptionDuRole(role: Role | null, sousRole?: string | null) {
  if (role === 'GESTIONNAIRE' && sousRole === 'STAFF_ENTREPOT') {
    return ROLES.GESTIONNAIRE_ENTREPOT
  }
  return ROLES[(role ?? 'VISITEUR') as RoleAffiche] ?? ROLES.VISITEUR
}
