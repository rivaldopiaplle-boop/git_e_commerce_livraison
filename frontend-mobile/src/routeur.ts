// Le routeur mobile.
//
// Il ne ressemble pas à celui du web, et c'est voulu : cinq onglets en bas
// contre une barre latérale (règle d'or n°7 — *« ce qui change, c'est la
// disposition »*). Ce qui reste identique, c'est la **règle d'accès** : un
// écran privé renvoie à la connexion, et y ramène après.
import { createRouter, createWebHistory } from '@ionic/vue-router'
import type { RouteRecordRaw } from 'vue-router'

import { useSession } from './magasins/session'

const routes: RouteRecordRaw[] = [
  { path: '/', redirect: '/accueil' },

  {
    path: '/connexion',
    name: 'connexion',
    component: () => import('./vues/Connexion.vue'),
    meta: { public: true },
  },

  // ── Le client ───────────────────────────────────────────────────────
  { path: '/accueil', name: 'accueil', component: () => import('./vues/Accueil.vue') },
  { path: '/recherche', name: 'recherche', component: () => import('./vues/Recherche.vue'),
    meta: { public: true } },
  { path: '/panier', name: 'panier', component: () => import('./vues/Panier.vue'),
    meta: { public: true } },
  // Commander ET payer, en un seul ecran (N-6). Le bouton du panier ne faisait
  // que naviguer vers la liste : on ne pouvait pas commander depuis le mobile.
  { path: '/commander', name: 'commander', component: () => import('./vues/Commander.vue') },
  { path: '/commandes', name: 'commandes', component: () => import('./vues/Commandes.vue') },
  { path: '/produit/:id', name: 'produit', component: () => import('./vues/Produit.vue'),
    meta: { public: true } },
  { path: '/adresses', name: 'adresses', component: () => import('./vues/Adresses.vue') },
  { path: '/boutiques', name: 'boutiques', component: () => import('./vues/Recherche.vue'),
    meta: { public: true } },

  // ── Le livreur ──────────────────────────────────────────────────────
  { path: '/courses', name: 'courses', component: () => import('./vues/livreur/Courses.vue') },
  { path: '/tournee', name: 'tournee', component: () => import('./vues/livreur/Tournee.vue') },
  { path: '/arret', name: 'arret', component: () => import('./vues/livreur/ProchainArret.vue') },
  { path: '/proximite', name: 'proximite',
    component: () => import('./vues/livreur/Proximite.vue') },
  { path: '/gains', name: 'gains', component: () => import('./vues/livreur/Gains.vue') },
  { path: '/historique', name: 'historique',
    component: () => import('./vues/livreur/Historique.vue') },

  // ── Commun ──────────────────────────────────────────────────────────
  { path: '/profil', name: 'profil', component: () => import('./vues/Profil.vue') },
  { path: '/aide', name: 'aide', component: () => import('./vues/Aide.vue'),
    meta: { public: true } },

  { path: '/:reste(.*)*', redirect: '/accueil' },
]

export const routeur = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
})

routeur.beforeEach((vers) => {
  const session = useSession()
  if (vers.meta.public || session.estConnecte) return true
  if (vers.name === 'connexion') return true
  // On garde la destination : après connexion, on y revient au lieu de
  // renvoyer à l'accueil, ce qui obligerait à refaire son chemin (D-66).
  return { name: 'connexion', query: { suite: vers.fullPath } }
})
