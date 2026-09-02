import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'

import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import PrimeVue from 'primevue/config'

import CoquilleApp from './composants/CoquilleApp.vue'
import { ROLES } from './roles'
import { routeur } from './routeur'
import { useAuthentification } from './stores/authentification'

// La couleur d'accent, et le bouton invisible — M-2.
//
// **Ta remarque** : *« dans les fenêtres popups, le bouton à côté de "Annuler"
// ou parfois "Garder" est écrit blanc sur blanc, donc invisible »*.
//
// La cause : PrimeVue accroche ses popups et ses toasts à `<body>`, donc **en
// dehors** du div qui portait `--accent`. Dans une popup,
// `background: var(--accent)` ne résolvait rien : le bouton principal perdait
// son fond et restait en `text-white` sur le fond blanc de la fenêtre.
//
// C'était la maladie du bloc J revenue par la bande — sauf que cette fois elle
// ne venait pas d'un jeton supprimé, mais d'une variable hors de portée.

const STYLE = readFileSync(resolve(__dirname, 'style.css'), 'utf-8')

describe('la couleur d accent ne peut plus manquer', () => {
  it('a une valeur par defaut sur la racine du document', () => {
    // Le garde-fou : même hors de la coquille — connexion, inscription — un
    // `var(--accent)` doit résoudre quelque chose.
    const racine = STYLE.match(/:root\s*\{[^}]*\}/)
    expect(racine, ':root doit exister dans style.css').toBeTruthy()
    expect(racine![0]).toContain('--accent:')
    expect(racine![0]).toContain('--accent-doux:')
  })

  it('n utilise jamais var(--accent) sans que la variable soit definie', () => {
    // Toute utilisation dans la feuille elle-même doit être couverte par le
    // `:root`. Une classe qui pointe vers une variable inexistante ne produit
    // aucun style — c'est ainsi qu'un bouton devient invisible.
    const utilise = STYLE.includes('var(--accent)')
    const definie = /:root\s*\{[^}]*--accent:/.test(STYLE)
    expect(utilise && definie).toBe(true)
  })
})

describe('la coquille propage la couleur du role', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.stubGlobal('localStorage', {
      getItem: () => null, setItem: () => {}, removeItem: () => {},
    })
    vi.stubGlobal('fetch', vi.fn(async () => ({
      ok: true, status: 200, json: async () => ({ data: { notifications: [], non_lues: 0 } }),
    })))
    document.documentElement.style.removeProperty('--accent')
  })

  async function monterEn(role: 'VENDEUR' | 'ADMIN') {
    const session = useAuthentification()
    session.utilisateur = {
      id: 1, email: 'test@exemple.fr', nom: 'Test', prenom: 'Test',
      role, statut_compte: 'ACTIF',
    } as never
    await routeur.push('/espace')
    await routeur.isReady()
    mount(CoquilleApp, {
      global: { plugins: [routeur, PrimeVue], stubs: { Teleport: true } },
    })
    await new Promise((suite) => setTimeout(suite, 20))
  }

  it('pose la couleur sur la RACINE, pas seulement sur son propre div', async () => {
    await monterEn('VENDEUR')

    // Sans cela, une popup — accrochée à `<body>` — n'héritait de rien.
    expect(document.documentElement.style.getPropertyValue('--accent'))
      .toBe(ROLES.VENDEUR.accent)
    expect(document.documentElement.style.getPropertyValue('--accent-doux'))
      .toBe(ROLES.VENDEUR.accentDoux)
  })

  it('suit le changement de role, sans garder la couleur du precedent', async () => {
    await monterEn('VENDEUR')
    expect(document.documentElement.style.getPropertyValue('--accent'))
      .toBe(ROLES.VENDEUR.accent)

    setActivePinia(createPinia())
    await monterEn('ADMIN')

    // Un administrateur avec le bleu du vendeur serait pire qu'une couleur
    // absente : il croirait être dans le mauvais espace.
    expect(document.documentElement.style.getPropertyValue('--accent'))
      .toBe(ROLES.ADMIN.accent)
  })
})
