// Un seul endroit decrit ce que chaque role voit et de quelle couleur.
//
// Les cinq accents viennent de plan-organisation/04-maquettes/design-system.md
// § 2. Le gestionnaire est sarcelle et non orange depuis que l'orange est la
// couleur de la marque : deux oranges voisins s'annulent.
import {
  Bell, Bike, Boxes, ClipboardList, FileClock, LayoutDashboard, MapPin,
  Package, Receipt, ScrollText, Settings, ShieldCheck, ShoppingBag, Store,
  Truck, Users,
} from '@lucide/vue'
import type { Component } from 'vue'

import type { Role } from './stores/authentification'

export type EntreeNavigation = {
  libelle: string
  icone: Component
  route?: string
  prochainement?: boolean
}

type DescriptionRole = {
  espace: string
  accent: string
  accentDoux: string
  navigation: EntreeNavigation[]
}

export const ROLES: Record<Role, DescriptionRole> = {
  CLIENT: {
    espace: 'Espace client',
    accent: '#16a34a',
    accentDoux: '#e8f8ee',
    navigation: [
      { libelle: 'Accueil', icone: LayoutDashboard, route: 'espace' },
      { libelle: 'Catalogue', icone: ShoppingBag, route: 'vitrine' },
      { libelle: 'Mes commandes', icone: Receipt, prochainement: true },
      { libelle: 'Mes adresses', icone: MapPin, prochainement: true },
      { libelle: 'Notifications', icone: Bell, prochainement: true },
    ],
  },
  VENDEUR: {
    espace: 'Espace vendeur',
    accent: '#2563eb',
    accentDoux: '#eaf0ff',
    navigation: [
      { libelle: 'Tableau de bord', icone: LayoutDashboard, route: 'espace' },
      { libelle: 'Catalogue', icone: Package, route: 'vendeur-catalogue' },
      { libelle: 'Commandes', icone: ClipboardList, prochainement: true },
      { libelle: 'Stock', icone: Boxes, route: 'vendeur-catalogue' },
      { libelle: 'Personnel', icone: Users, prochainement: true },
      { libelle: 'Ma boutique', icone: Store, prochainement: true },
    ],
  },
  GESTIONNAIRE: {
    espace: 'Espace gestion',
    accent: '#0d9488',
    accentDoux: '#e6f7f4',
    navigation: [
      { libelle: 'Accueil', icone: LayoutDashboard },
      { libelle: 'A preparer', icone: ClipboardList, prochainement: true },
      { libelle: 'Stock', icone: Boxes, prochainement: true },
    ],
  },
  LIVREUR: {
    espace: 'Espace livreur',
    accent: '#7c3aed',
    accentDoux: '#f3edff',
    navigation: [
      { libelle: 'Accueil', icone: LayoutDashboard },
      { libelle: 'Ma course', icone: Bike, prochainement: true },
      { libelle: 'Tournee', icone: Truck, prochainement: true },
      { libelle: 'Historique', icone: FileClock, prochainement: true },
    ],
  },
  ADMIN: {
    espace: 'Administration',
    accent: '#b91c1c',
    accentDoux: '#fdebe9',
    navigation: [
      { libelle: 'Tableau de bord', icone: LayoutDashboard },
      { libelle: 'Validations', icone: ShieldCheck, prochainement: true },
      { libelle: 'Utilisateurs', icone: Users, prochainement: true },
      { libelle: "Journal d'audit", icone: ScrollText, prochainement: true },
      { libelle: 'Parametres', icone: Settings, prochainement: true },
    ],
  },
}

export function descriptionDuRole(role: Role | null) {
  return ROLES[role ?? 'CLIENT'] ?? ROLES.CLIENT
}
