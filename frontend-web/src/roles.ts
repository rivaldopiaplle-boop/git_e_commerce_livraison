// Ce que chaque role voit, de quelle couleur, et sur quel support.
//
// Deux regles apprises a mes depens :
//   · un espace de travail ne renvoie PAS au catalogue public. Aucun
//     back-office marchand ne le fait : ce sont deux mondes, et melanger les
//     deux donne l'impression d'un site amateur ;
//   · le gestionnaire n'est pas un vendeur au rabais. Il prepare, il compte,
//     il ne voit ni les prix ni le chiffre d'affaires (D-04).
import {
  Bell, Bike, Boxes, ClipboardList, FileClock, LayoutDashboard, MapPin, Package,
  Receipt, ScrollText, ShieldCheck, ShoppingBag, Store, Truck, Users, Warehouse,
} from '@lucide/vue'
import type { Component } from 'vue'

import type { Role } from './stores/authentification'

export type EntreeNavigation = {
  libelle: string
  icone: Component
  route?: string
  prochainement?: boolean
}

/** Un visiteur sans compte est un futur client : il en porte les couleurs. */
export type RoleAffiche = Role | 'VISITEUR'

type DescriptionRole = {
  espace: string
  accent: string
  accentDoux: string
  /** Ou ce role travaille reellement (D-40). */
  plateforme: 'web' | 'mobile' | 'web+mobile'
  /** Le panneau droit : le panier n'a de sens que pour qui achete. */
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
      { libelle: 'Mon compte', icone: LayoutDashboard, route: 'espace' },
      { libelle: 'Mes adresses', icone: MapPin, prochainement: true },
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
      { libelle: 'Mon catalogue', icone: Package, route: 'vendeur-catalogue' },
      { libelle: 'Stock', icone: Boxes, route: 'vendeur-stock' },
      { libelle: 'Mon personnel', icone: Users, prochainement: true },
    ],
  },
  GESTIONNAIRE: {
    espace: 'Espace gestion',
    accent: '#0d9488',
    accentDoux: '#e6f7f4',
    plateforme: 'web',
    panneau: 'activite',
    // Le gestionnaire prepare et compte. Ni tableau de bord commercial, ni
    // catalogue : ce ne sont pas ses decisions (D-04).
    navigation: [
      { libelle: 'A preparer', icone: ClipboardList, route: 'vendeur-commandes' },
      { libelle: 'Stock', icone: Boxes, route: 'vendeur-stock' },
      { libelle: 'Reception entrepot', icone: Warehouse, prochainement: true },
    ],
  },
  LIVREUR: {
    espace: 'Espace livreur',
    accent: '#7c3aed',
    accentDoux: '#f3edff',
    plateforme: 'mobile',
    panneau: 'activite',
    navigation: [
      { libelle: 'Tableau de bord', icone: LayoutDashboard, route: 'espace' },
      { libelle: 'Ma course', icone: Bike, prochainement: true },
      { libelle: 'Ma tournee', icone: Truck, prochainement: true },
      { libelle: 'Historique', icone: FileClock, prochainement: true },
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
      { libelle: 'Utilisateurs', icone: Users, prochainement: true },
      { libelle: 'Litiges', icone: Bell, prochainement: true },
      { libelle: "Journal d'audit", icone: ScrollText, prochainement: true },
    ],
  },
}

export function descriptionDuRole(role: Role | null) {
  return ROLES[(role ?? 'VISITEUR') as RoleAffiche] ?? ROLES.VISITEUR
}
