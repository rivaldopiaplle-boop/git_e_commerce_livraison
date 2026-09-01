import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import Connexion from './vues/Connexion.vue'
import Inscription from './vues/Inscription.vue'
import { routeur } from './routeur'
import { REGLES } from './validation'

// La validation des formulaires — D-26.
//
// `vee-validate` et `zod` étaient **déclarés et utilisés nulle part** : les
// formulaires validaient à la main, chacun à sa façon, et découvraient la
// moitié des erreurs en revenant du serveur. C'est exactement ce que tu m'as
// reproché au bloc K.
//
// Ce qui est vérifié ici : l'erreur apparaît **avant** l'envoi, un formulaire
// invalide ne part pas, et le message du serveur se pose sur le bon champ.

async function monter(composant: unknown, chemin: string) {
  await routeur.push(chemin)
  await routeur.isReady()
  return mount(composant as never, { global: { plugins: [routeur] } })
}

/** Remplir un champ et le quitter, comme une personne le ferait. */
async function saisir(ecran: ReturnType<typeof mount>, index: number, valeur: string) {
  const champ = ecran.findAll('input')[index]
  await champ.setValue(valeur)
  await champ.trigger('blur')
  await new Promise((suite) => setTimeout(suite, 10))
}

describe('les regles de saisie', () => {
  it('refuse une adresse e-mail qui n en est pas une', () => {
    expect(REGLES.courriel.safeParse('pas-une-adresse').success).toBe(false)
    expect(REGLES.courriel.safeParse('lea@exemple.fr').success).toBe(true)
  })

  it('exige dix caracteres pour un mot de passe, sans exiger de symbole', () => {
    // Les regles de composition poussent aux mots de passe du genre
    // « Passe1234! », que les gens reutilisent partout. La longueur protege
    // mieux, et c'est ce que recommandent l'ANSSI et le NIST.
    expect(REGLES.motDePasse.safeParse('court').success).toBe(false)
    expect(REGLES.motDePasse.safeParse('correcthorsebattery').success).toBe(true)
  })

  it('exige cinq chiffres pour un code postal francais', () => {
    expect(REGLES.codePostal.safeParse('6900').success).toBe(false)
    expect(REGLES.codePostal.safeParse('69002').success).toBe(true)
    expect(REGLES.codePostal.safeParse('69 002').success).toBe(false)
  })
})

describe('le formulaire de connexion', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.stubGlobal('localStorage', {
      getItem: () => null, setItem: () => {}, removeItem: () => {},
    })
    vi.stubGlobal('fetch', vi.fn(async () => ({
      ok: true, status: 200, json: async () => ({ data: {} }),
    })))
  })

  it('signale une adresse invalide des qu on quitte le champ', async () => {
    const ecran = await monter(Connexion, '/connexion')

    await saisir(ecran, 0, 'pas-une-adresse')

    // Avant l'envoi, pas apres : decouvrir l'erreur au retour du reseau est ce
    // qui fait abandonner.
    expect(ecran.text()).toContain('ne ressemble pas à une adresse valide')
  })

  it('n envoie rien tant que le formulaire est invalide', async () => {
    const appel = vi.fn(async () => ({
      ok: true, status: 200, json: async () => ({ data: {} }),
    }))
    vi.stubGlobal('fetch', appel)
    const ecran = await monter(Connexion, '/connexion')

    await saisir(ecran, 0, 'pas-une-adresse')
    await ecran.find('form').trigger('submit')
    await new Promise((suite) => setTimeout(suite, 20))

    expect(appel).not.toHaveBeenCalled()
  })

  it('remplit les deux champs quand on choisit un compte de demonstration', async () => {
    const ecran = await monter(Connexion, '/connexion')

    // Le bouton porte le role en libelle et l'adresse en infobulle.
    const bouton = ecran.findAll('button').find(
      (b) => b.attributes('title') === 'lea@exemple.fr',
    )
    await bouton!.trigger('click')
    await new Promise((suite) => setTimeout(suite, 10))

    const champs = ecran.findAll('input')
    expect((champs[0].element as HTMLInputElement).value).toBe('lea@exemple.fr')
    expect((champs[1].element as HTMLInputElement).value).toBe('Demonstration!2026')
  })

  it('ne reproche pas sa longueur au mot de passe a la connexion', async () => {
    const ecran = await monter(Connexion, '/connexion')

    await saisir(ecran, 1, 'court')

    // Le mot de passe existe deja : lui reprocher sa forme quand quelqu'un
    // essaie d'entrer est une facon de le perdre.
    expect(ecran.text()).not.toContain('Dix caractères')
  })
})

describe('le formulaire d inscription', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.stubGlobal('localStorage', {
      getItem: () => null, setItem: () => {}, removeItem: () => {},
    })
    vi.stubGlobal('fetch', vi.fn(async () => ({
      ok: true, status: 200, json: async () => ({ data: {} }),
    })))
  })

  it('exige dix caracteres pour le mot de passe, lui', async () => {
    const ecran = await monter(Inscription, '/inscription')

    const champs = ecran.findAll('input')
    const motDePasse = champs[champs.length - 1]
    await motDePasse.setValue('court')
    await motDePasse.trigger('blur')
    await new Promise((suite) => setTimeout(suite, 10))

    expect(ecran.text()).toContain('Dix caractères')
  })

  it('demande le nom de la boutique a un vendeur, et a lui seul', async () => {
    const ecran = await monter(Inscription, '/inscription?profil=client')
    expect(ecran.text()).not.toContain('Nom de la boutique')

    const onglet = ecran.findAll('button').find((b) => b.text().trim() === 'Vendeur')
    await onglet!.trigger('click')
    await new Promise((suite) => setTimeout(suite, 10))

    expect(ecran.text()).toContain('Nom de la boutique')
  })

  it('previent un vendeur qu il sera verifie, AVANT qu il remplisse', async () => {
    const ecran = await monter(Inscription, '/inscription?profil=vendeur')

    // Le dire apres l'envoi serait une mauvaise surprise (D-02).
    expect(ecran.text()).toContain('verifie par un administrateur')
  })
})
