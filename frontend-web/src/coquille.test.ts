import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import PrimeVue from 'primevue/config'

import CoquilleApp from './composants/CoquilleApp.vue'
import { routeur } from './routeur'
import { useAuthentification } from './stores/authentification'
import { useCompteurs } from './stores/compteurs'

// La barre latérale et la barre haute — L-3.
//
// Elles listaient des noms d'écrans, et rien de plus : il fallait ouvrir
// chacun pour découvrir qu'il y avait trois commandes à préparer et deux
// litiges en souffrance. Ce qui est vérifié ici :
//
//   · les entrées sont **groupées en sections** — neuf entrées à plat ne se
//     lisent pas ;
//   · une **pastille** dit ce qui attend, et elle survit au repli de la barre ;
//   · la barre haute porte un **fil d'Ariane**, pas seulement le nom d'espace.

function serveur() {
  return vi.fn(async (url: string) => {
    const chemin = String(url)
    if (chemin.includes('/moi/compteurs')) {
      return {
        ok: true,
        status: 200,
        json: async () => ({
          data: { 'vendeur-commandes': 3, 'vendeur-litiges': 1 },
        }),
      }
    }
    return {
      ok: true,
      status: 200,
      json: async () => ({ data: { notifications: [], non_lues: 0 } }),
    }
  })
}

async function monterEnVendeur(chemin = '/espace/commandes') {
  const session = useAuthentification()
  session.utilisateur = {
    id: 1, email: 'karim@exemple.fr', nom: 'Benali', prenom: 'Karim',
    role: 'VENDEUR', statut_compte: 'ACTIF',
  } as never
  // `estConnecte` se deduit de l'utilisateur : poser le jeton serait inutile.

  await routeur.push(chemin)
  await routeur.isReady()
  const coquille = mount(CoquilleApp, {
    global: { plugins: [routeur, PrimeVue], stubs: { Teleport: true } },
  })
  await useCompteurs().rafraichir(true)
  await new Promise((suite) => setTimeout(suite, 20))
  return coquille
}

describe('la barre laterale', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.stubGlobal('localStorage', {
      getItem: () => null, setItem: () => {}, removeItem: () => {},
    })
    vi.stubGlobal('fetch', serveur())
  })

  it('groupe les entrees en sections nommees', async () => {
    const coquille = await monterEnVendeur()

    // Un vendeur a neuf entrees : sans sections, l'oeil parcourt la liste
    // entiere a chaque fois.
    const texte = coquille.text()
    expect(texte).toContain('Ma boutique')
    expect(texte).toContain('Vendre')
    expect(texte).toContain('Mon compte')
  })

  it('affiche une pastille sur ce qui attend une action', async () => {
    const coquille = await monterEnVendeur()

    // Trois commandes a preparer, un litige sans reponse : les deux chiffres
    // doivent se lire sans ouvrir l'ecran.
    const pastilles = coquille.findAll('span').filter(
      (element) => ['3', '1'].includes(element.text().trim())
        && element.classes().some((classe) => classe.startsWith('rounded-full')),
    )
    expect(pastilles.length).toBeGreaterThanOrEqual(2)
  })

  it('nomme le nombre en attente dans l infobulle', async () => {
    const coquille = await monterEnVendeur()

    // Une pastille sans explication laisse deviner ce qu'elle compte.
    const lien = coquille.findAll('a').find(
      (element) => element.attributes('title')?.includes('Commandes reçues'),
    )
    expect(lien?.attributes('title')).toContain('3 en attente')
  })

  it('garde une trace des pastilles une fois repliee', async () => {
    const coquille = await monterEnVendeur()

    const reduire = coquille.findAll('button').find((b) => b.text().includes('Reduire'))
    await reduire!.trigger('click')

    // Replier ne doit pas rendre aveugle : le nombre ne tient plus, mais le
    // point reste.
    const points = coquille.findAll('span.absolute.-top-1')
    expect(points.length).toBeGreaterThanOrEqual(2)
  })

  it('ne demande rien au serveur pour un visiteur', async () => {
    const appel = serveur()
    vi.stubGlobal('fetch', appel)

    await routeur.push('/')
    await routeur.isReady()
    mount(CoquilleApp, {
      global: { plugins: [routeur, PrimeVue], stubs: { Teleport: true } },
    })
    await new Promise((suite) => setTimeout(suite, 20))

    // Un visiteur n'a rien en attente : l'appel n'est meme pas tente.
    const chemins = appel.mock.calls.map((appelle) => String(appelle[0]))
    expect(chemins.some((chemin) => chemin.includes('/moi/compteurs'))).toBe(false)
  })
})

describe('la barre haute', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.stubGlobal('localStorage', {
      getItem: () => null, setItem: () => {}, removeItem: () => {},
    })
    vi.stubGlobal('fetch', serveur())
  })

  it('porte un fil d Ariane, pas seulement le nom de l espace', async () => {
    const coquille = await monterEnVendeur()

    // « Espace vendeur » tout seul ne disait pas OU on se trouvait dedans.
    const entete = coquille.find('header')
    expect(entete.text()).toContain('Espace vendeur')
    expect(entete.text()).toContain('Vendre')
  })

  it('annonce le raccourci de recherche', async () => {
    const coquille = await monterEnVendeur()

    // Un raccourci que personne ne connait n'existe pas.
    expect(coquille.find('kbd').text()).toBe('/')
  })
})
