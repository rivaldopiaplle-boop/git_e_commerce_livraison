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
  Scale, Store, Truck, UserRound, Users, Wallet, Warehouse,
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
  /**
   * Le titre de section sous lequel l'entree se range.
   *
   * Neuf entrees a plat ne se lisent pas : l'oeil parcourt la liste entiere a
   * chaque fois. Trois groupes de trois se balayent d'un coup. La regle du
   * regroupement est toujours la meme : **ce qu'on fait**, puis **ce qu'on
   * consulte**, puis **son compte** — ce dernier toujours en bas, ou tout le
   * monde le cherche.
   */
  groupe?: string
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
      { libelle: 'Catalogue', icone: ShoppingBag, route: 'vitrine', groupe: 'Acheter' },
      { libelle: 'Boutiques', icone: Store, route: 'boutiques', groupe: 'Acheter' },
      { libelle: 'Vendre ou livrer', icone: Users, route: 'rejoindre', groupe: 'Acheter' },
    ],
  },
  CLIENT: {
    espace: 'Espace client',
    accent: '#16a34a',
    accentDoux: '#e8f8ee',
    plateforme: 'web+mobile',
    panneau: 'panier',
    navigation: [
      { libelle: 'Catalogue', icone: ShoppingBag, route: 'vitrine', groupe: 'Acheter' },
      { libelle: 'Boutiques', icone: Store, route: 'boutiques', groupe: 'Acheter' },
      { libelle: 'Mes commandes', icone: Receipt, route: 'mes-commandes', groupe: 'Mes achats' },
      { libelle: 'Mes adresses', icone: MapPin, route: 'mes-adresses', groupe: 'Mes achats' },
      { libelle: 'Mon compte', icone: LayoutDashboard, route: 'espace', groupe: 'Mon compte' },
      { libelle: 'Mon profil', icone: UserRound, route: 'profil', groupe: 'Mon compte' },
      { libelle: 'Paramètres', icone: Settings, route: 'parametres', groupe: 'Mon compte' },
    ],
  },
  VENDEUR: {
    espace: 'Espace vendeur',
    accent: '#2563eb',
    accentDoux: '#eaf0ff',
    plateforme: 'web',
    panneau: 'activite',
    navigation: [
      { libelle: 'Tableau de bord', icone: LayoutDashboard, route: 'espace',
        groupe: 'Ma boutique' },
      { libelle: 'Statistiques', icone: BarChart3, route: 'vendeur-statistiques',
        groupe: 'Ma boutique' },
      { libelle: 'Mon personnel', icone: Users, route: 'vendeur-personnel',
        groupe: 'Ma boutique' },

      { libelle: 'Commandes reçues', icone: ClipboardList, route: 'vendeur-commandes',
        groupe: 'Vendre' },
      // Catalogue et stock ne font qu'un ecran (D-79) : ce sont deux vues du
      // meme objet, et les separer obligeait a garder deux boutons de
      // correction du stock pour la meme action.
      { libelle: 'Mon catalogue', icone: Package, route: 'vendeur-catalogue',
        groupe: 'Vendre' },
      // Un vendeur doit pouvoir repondre a ce qu'on lui reproche (D-94) : une
      // place de marche qui condamne sans entendre est une place de marche
      // qu'on quitte.
      { libelle: 'Litiges', icone: Scale, route: 'vendeur-litiges', groupe: 'Vendre' },

      { libelle: 'Mon profil', icone: UserRound, route: 'profil', groupe: 'Mon compte' },
      { libelle: 'Paramètres', icone: Settings, route: 'parametres', groupe: 'Mon compte' },
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
      { libelle: 'À préparer', icone: ClipboardList, route: 'vendeur-commandes', groupe: 'Mon travail' },
      { libelle: 'Stock', icone: Boxes, route: 'vendeur-catalogue', groupe: 'Mon travail' },
      { libelle: "Vue d'ensemble", icone: LayoutDashboard, route: 'espace', groupe: 'Mon travail' },
      // Grisee, exactement comme dans la maquette : l'entree existe pour que
      // l'employe sache que la donnee existe et qu'elle ne lui est pas due.
      { libelle: "Chiffre d'affaires", icone: Wallet, interdite: true, groupe: 'Mon travail' },
      { libelle: 'Mon profil', icone: UserRound, route: 'profil', groupe: 'Mon compte' },
      { libelle: 'Paramètres', icone: Settings, route: 'parametres', groupe: 'Mon compte' },
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
      { libelle: "Vue d'ensemble", icone: LayoutDashboard, route: 'espace', groupe: 'Mon travail' },
      { libelle: 'Colis reçus', icone: Warehouse, route: 'entrepot-colis', groupe: "L'entrepôt" },
      { libelle: 'Tournées', icone: Route, route: 'entrepot-tournees', groupe: "L'entrepôt" },
      { libelle: 'Mon profil', icone: UserRound, route: 'profil', groupe: 'Mon compte' },
      { libelle: 'Paramètres', icone: Settings, route: 'parametres', groupe: 'Mon compte' },
    ],
  },
  LIVREUR: {
    espace: 'Espace livreur',
    accent: '#7c3aed',
    accentDoux: '#f3edff',
    plateforme: 'mobile',
    panneau: 'activite',
    navigation: [
      { libelle: "Vue d'ensemble", icone: LayoutDashboard, route: 'espace', groupe: 'Mon travail' },
      { libelle: 'Mes courses', icone: Bike, route: 'livreur-courses', groupe: 'Livrer' },
      { libelle: 'Ma tournée', icone: Truck, route: 'livreur-courses', groupe: 'Livrer' },
      { libelle: 'Mes gains', icone: Wallet, route: 'livreur-courses', groupe: 'Livrer' },
      { libelle: 'Mon profil', icone: UserRound, route: 'profil', groupe: 'Mon compte' },
      { libelle: 'Paramètres', icone: Settings, route: 'parametres', groupe: 'Mon compte' },
    ],
  },
  ADMIN: {
    espace: 'Administration',
    accent: '#b91c1c',
    accentDoux: '#fdebe9',
    plateforme: 'web',
    panneau: 'activite',
    navigation: [
      { libelle: 'Tableau de bord', icone: LayoutDashboard, route: 'espace',
        groupe: 'La plateforme' },
      { libelle: 'Boutiques', icone: Store, route: 'admin-boutiques',
        groupe: 'La plateforme' },
      { libelle: 'Utilisateurs', icone: Users, route: 'admin-utilisateurs',
        groupe: 'La plateforme' },
      { libelle: "Journal d'audit", icone: ScrollText, route: 'admin-journal',
        groupe: 'La plateforme' },

      { libelle: 'Validations', icone: ShieldCheck, route: 'admin-validations',
        groupe: 'À traiter' },
      { libelle: 'Litiges', icone: Scale, route: 'admin-litiges', groupe: 'À traiter' },
      { libelle: "Demandes d'identité", icone: BadgeCheck, route: 'admin-demandes',
        groupe: 'À traiter' },

      { libelle: 'Mon profil', icone: UserRound, route: 'profil', groupe: 'Mon compte' },
      { libelle: 'Paramètres', icone: Settings, route: 'parametres', groupe: 'Mon compte' },
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
