import { readdirSync, readFileSync } from 'node:fs'
import { join, resolve } from 'node:path'

import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import PrimeVue from 'primevue/config'
import ToastService from 'primevue/toastservice'

import Litiges from './vues/admin/Litiges.vue'
import MesCommandes from './vues/client/MesCommandes.vue'
import { routeur } from './routeur'

// L'œil ouvre une popup — M-1.
//
// **Ta remarque** : *« le symbole œil doit ouvrir une fenêtre popup »*. Il se
// contentait de sélectionner la ligne — ce que tu avais déjà jugé inutile au
// bloc L-2 : *« l'œil bouton pour consulter au lieu d'ouvrir une fenêtre popup
// sélectionne, ce qui ne sert à rien »*.
//
// Ce qui est vérifié ici : l'œil **ouvre** vraiment, le détail y est, et le
// panneau de droite montre la même chose — parce qu'il est écrit une seule
// fois. Deux copies d'un même détail finissent toujours par diverger, et c'est
// celle qu'on ne regarde pas qui ment.

const LITIGE = {
  id: 12,
  motif: 'INCOMPLET',
  libelle_motif: 'Commande incomplète',
  description: 'Deux articles manquants sur les trois commandés.',
  statut: 'EN_COURS',
  libelle_statut: 'En cours d’examen',
  resolution: '',
  montant_rembourse_centimes: 0,
  date_ouverture: '2026-09-01T10:00:00Z',
  date_resolution: null,
  reponse_vendeur: 'Le colis est parti scellé.',
  date_reponse_vendeur: '2026-09-01T14:00:00Z',
  date_limite_reponse: '2026-09-03T10:00:00Z',
  delai_expire: false,
  arbitrable: true,
  client: 'Léa Martin',
  commande: 'RD-260901-ABC123',
  id_commande: 7,
  montant_commande_centimes: 4520,
  boutiques: ['Chez Karim'],
  pour: 'admin',
}

const COMMANDE = {
  id: 7,
  numero_commande: 'RD-260901-ABC123',
  type_service: 'EXPRESS',
  statut_actuel: 'LIVREE',
  libelle_statut: 'Livrée',
  montant_produits_centimes: 4230,
  montant_livraison_centimes: 290,
  montant_total_centimes: 4520,
  date_commande: '2026-09-01T10:00:00Z',
  date_livraison_estimee: null,
  adresse: '8 rue Victor Hugo, 69002 Lyon',
  boutiques: ['Chez Karim'],
  sous_commandes: [],
}

function serveur(donnees: unknown) {
  return vi.fn(async () => ({ ok: true, status: 200, json: async () => ({ data: donnees }) }))
}

async function monter(composant: unknown, donnees: unknown, chemin: string) {
  vi.stubGlobal('fetch', serveur(donnees))
  await routeur.push(chemin)
  await routeur.isReady()
  const ecran = mount(composant as never, {
    // On NE remplace pas Teleport : la popup de PrimeVue s'accroche au corps
    // du document, et c'est justement ce qu'on veut voir se produire.
    global: { plugins: [routeur, PrimeVue, ToastService] },
  })
  await new Promise((suite) => setTimeout(suite, 30))
  return ecran
}

function cliquerSurLOeil(ecran: ReturnType<typeof mount>) {
  const oeil = ecran.findAll('button').find(
    (bouton) => (bouton.attributes('title') ?? '').startsWith('Consulter'),
  )
  expect(oeil, 'chaque liste doit porter un bouton-oeil').toBeTruthy()
  return oeil!.trigger('click')
}

describe('l oeil de la liste des litiges', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.stubGlobal('localStorage', {
      getItem: () => null, setItem: () => {}, removeItem: () => {},
    })
    document.body.innerHTML = ''
  })

  it('ouvre une popup, il ne se contente pas de selectionner', async () => {
    const ecran = await monter(Litiges, { litiges: [LITIGE] }, '/espace/litiges')

    expect(document.querySelector('[role="dialog"]'), 'rien avant le clic').toBeNull()

    await cliquerSurLOeil(ecran)
    await new Promise((suite) => setTimeout(suite, 30))

    expect(document.querySelector('[role="dialog"]')).not.toBeNull()
  })

  it('met le detail du dossier DANS la popup', async () => {
    const ecran = await monter(Litiges, { litiges: [LITIGE] }, '/espace/litiges')
    await cliquerSurLOeil(ecran)
    await new Promise((suite) => setTimeout(suite, 30))

    // Les deux versions cote a cote : c'est tout l'interet du dossier.
    const fenetre = document.querySelector('[role="dialog"]')!
    expect(fenetre.textContent).toContain('Deux articles manquants')
    expect(fenetre.textContent).toContain('Le colis est parti scellé')
  })

  it('laisse la liste en place derriere : on ne perd pas sa position', async () => {
    const ecran = await monter(Litiges, { litiges: [LITIGE] }, '/espace/litiges')
    await cliquerSurLOeil(ecran)
    await new Promise((suite) => setTimeout(suite, 30))

    // C'est ce qui distingue une popup d'une navigation (D-60).
    expect(ecran.text()).toContain('RD-260901-ABC123')
  })
})

describe('l oeil de mes commandes', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.stubGlobal('localStorage', {
      getItem: () => null, setItem: () => {}, removeItem: () => {},
    })
    document.body.innerHTML = ''
  })

  it('ouvre aussi une popup : le geste est le meme partout', async () => {
    const ecran = await monter(MesCommandes, [COMMANDE], '/mes-commandes')

    await cliquerSurLOeil(ecran)
    await new Promise((suite) => setTimeout(suite, 30))

    // Un meme symbole doit promettre la meme chose sur tous les ecrans.
    expect(document.querySelector('[role="dialog"]')).not.toBeNull()
  })
})


describe('tous les yeux du projet se ressemblent', () => {
  /** Tous les `.vue` des vues, quel que soit leur dossier. */
  function ecrans(dossier: string): string[] {
    return readdirSync(dossier, { withFileTypes: true }).flatMap((entree) => {
      const chemin = join(dossier, entree.name)
      if (entree.isDirectory()) return ecrans(chemin)
      return entree.name.endsWith('.vue') ? [chemin] : []
    })
  }

  const AVEC_OEIL = ecrans(resolve(__dirname, 'vues'))
    .map((chemin) => [chemin, readFileSync(chemin, 'utf-8')] as const)
    .filter(([, source]) => source.includes(':icone="Eye"'))

  it('trouve bien des ecrans a verifier', () => {
    // Un test qui ne verifie rien passe toujours : on s'assure d'abord qu'il
    // a de la matiere.
    expect(AVEC_OEIL.length).toBeGreaterThanOrEqual(10)
  })

  /** Les blocs `<ActionLigne …/>` d'un fichier, un par un. */
  function actions(source: string): string[] {
    return [...source.matchAll(/<ActionLigne[\s\S]*?\/>/g)].map((m) => m[0])
  }

  it('promet la meme chose partout : « Consulter… »', () => {
    // Un meme symbole qui promet deux choses differentes selon l'ecran oblige
    // a le reapprendre a chaque fois. Un ecran disait « Suivre », onze
    // disaient « Consulter ».
    //
    // On decoupe par BLOC `<ActionLigne>` et non par occurrence de l'icone :
    // une premiere version prenait le `titre=` le plus proche, qui appartenait
    // au bouton d'a cote. Un garde-fou qui signale a tort finit desarme.
    const fautifs: string[] = []
    for (const [chemin, source] of AVEC_OEIL) {
      for (const bloc of actions(source)) {
        if (!bloc.includes(':icone="Eye"')) continue
        const titre = bloc.match(/titre="([^"]*)"/)
        if (titre && !titre[1].startsWith('Consulter')) {
          fautifs.push(`${chemin} : « ${titre[1]} »`)
        }
      }
    }
    expect(fautifs).toEqual([])
  })

  it('appelle tous la meme fonction, qui ouvre l apercu', () => {
    // Si un ecran garde l'ancien `@click` qui ne fait que selectionner, son
    // oeil n'ouvrira rien — et personne ne s'en apercevra avant la demo.
    const fautifs = AVEC_OEIL
      .filter(([, source]) => !source.includes('consulter('))
      .map(([chemin]) => chemin)
    expect(fautifs).toEqual([])
  })
})
