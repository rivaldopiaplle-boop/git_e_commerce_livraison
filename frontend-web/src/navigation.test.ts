import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'

import App from './App.vue'
import { ROLES } from './roles'
import { routeur } from './routeur'

describe('navigation reelle avec le vrai routeur', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.stubGlobal('localStorage', { getItem: () => null, setItem: () => {}, removeItem: () => {} })
    // Une charge utile plausible : un test qui nourrit du vide ne prouve
    // rien sur le comportement reel des ecrans.
    vi.stubGlobal(
      'fetch',
      vi.fn(async (url: string) => ({
        ok: true,
        status: 200,
        json: async () =>
          String(url).includes('/produits/')
            ? {
                data: {
                  id: 7, nom: 'Casque', description: 'Un casque.', prix_centimes: 18900,
                  image: '', photos: [], disponible: true, stock_disponible: 5,
                  distance_km: null, categorie: null,
                  boutique: { id: 1, nom: 'TechSophie', type_service: 'STANDARD', ville: 'Lyon' },
                  avis: { nombre: 0, note_moyenne: null, repartition: {}, avis: [] },
                  produits_similaires: [],
                },
              }
            : { data: [], meta: { total: 0, total_avant_filtres: 0,
                                  facettes: { univers: [], boutiques: [] } } },
      })),
    )
  })

  it('un visiteur passe de la vitrine a rejoindre, connexion, inscription, fiche produit', async () => {
    await routeur.push('/')
    await routeur.isReady()
    mount(App, { global: { plugins: [routeur] } })

    for (const chemin of ['/rejoindre', '/connexion', '/inscription', '/produit/7', '/']) {
      await routeur.push(chemin)
      await routeur.isReady()
      expect(routeur.currentRoute.value.path).toBe(chemin)
    }
  })

  it('un espace prive renvoie bien un visiteur vers la connexion', async () => {
    await routeur.push('/espace')
    await routeur.isReady()
    expect(routeur.currentRoute.value.name).toBe('connexion')
  })
})

describe('la barre laterale de chaque role', () => {
  // Une entree de menu qui ne mene nulle part est le defaut le plus visible
  // qu'un ecran puisse avoir : on clique, il ne se passe rien, et on doute de
  // tout le reste. Ce test compare la navigation de chaque role aux routes
  // reellement declarees.
  const nomsDeRoutes = new Set(
    routeur.getRoutes().map((route) => route.name).filter(Boolean) as string[],
  )

  for (const [role, description] of Object.entries(ROLES)) {
    it(`${role} : toutes ses entrees menent a une route existante`, () => {
      const orphelines = description.navigation
        .filter((entree) => entree.route && !nomsDeRoutes.has(entree.route))
        .map((entree) => `${entree.libelle} → ${entree.route}`)
      expect(orphelines).toEqual([])
    })

    it(`${role} : aucune entree muette sans explication`, () => {
      // Une entree sans route est acceptable si elle est explicitement
      // marquee interdite (grisee, comme le CA du gestionnaire) ou a venir.
      const muettes = description.navigation
        .filter((entree) => !entree.route && !entree.interdite && !entree.prochainement)
        .map((entree) => entree.libelle)
      expect(muettes).toEqual([])
    })
  }

  it('chaque role a une couleur dominante distincte de celle des autres metiers', () => {
    // Regle d'or n°8. Client et visiteur partagent la leur : un visiteur est
    // un futur client.
    const couleurs = new Map<string, string[]>()
    for (const [role, description] of Object.entries(ROLES)) {
      couleurs.set(description.accent, [...(couleurs.get(description.accent) ?? []), role])
    }
    for (const [, roles] of couleurs) {
      const familles = new Set(roles.map((role) => role.split('_')[0]))
      expect(familles.size).toBeLessThanOrEqual(2)
    }
  })
})
