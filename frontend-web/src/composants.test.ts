import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { Eye } from '@lucide/vue'
import PrimeVue from 'primevue/config'

import ActionLigne from './composants/ActionLigne.vue'
import CarteProduit from './composants/CarteProduit.vue'
import CoquilleApp from './composants/CoquilleApp.vue'
import Liste from './composants/Liste.vue'
import type { Colonne } from './composants/liste'
import { routeur } from './routeur'

// On monte avec le VRAI routeur : un routeur de test allege laisserait passer
// un lien qui pointe vers une route inexistante — exactement le bug qu'on
// cherche a attraper.
describe('la navigation existe vraiment', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.stubGlobal('localStorage', {
      getItem: () => null, setItem: () => {}, removeItem: () => {},
    })
    vi.stubGlobal('fetch', vi.fn(async () => ({
      ok: true, status: 200,
      json: async () => ({ data: [], meta: { total: 0, total_avant_filtres: 0,
                                             facettes: { univers: [], boutiques: [] } } }),
    })))
  })

  it('la coquille porte des liens cliquables vers des routes existantes', async () => {
    await routeur.push('/')
    await routeur.isReady()

    const composant = mount(CoquilleApp, { global: { plugins: [routeur] } })
    const liens = composant.findAll('a').map((a) => a.attributes('href'))

    // Un visiteur doit pouvoir regarder le catalogue, decouvrir comment
    // rejoindre la plateforme, et entrer.
    expect(liens).toContain('/')
    expect(liens).toContain('/boutiques')
    expect(liens).toContain('/rejoindre')
    expect(liens).toContain('/connexion')
    expect(liens).toContain('/inscription')
  })

  it('la carte produit entiere mene a la fiche', async () => {
    await routeur.push('/')
    await routeur.isReady()

    const composant = mount(CarteProduit, {
      global: { plugins: [routeur] },
      props: {
        produit: {
          id: 7, nom: 'Casque', prix_centimes: 18900, image: '/media/x.webp',
          disponible: true, distance_km: null,
          boutique: { id: 1, nom: 'TechSophie', type_service: 'STANDARD', ville: 'Lyon' },
        },
      },
    })

    expect(composant.find('a').attributes('href')).toBe('/produit/7')
  })
})

describe('les listes du projet', () => {
  // Le bloc K a redit ce que la regle d'or n°9 disait depuis le bloc A :
  // « dans les listes d'affichage, des boutons en forme de symbole pour
  // consulter et gerer les donnees ». Ces tests verifient que ces boutons
  // existent, qu'ils sont nommes, et surtout QU'ILS CLIQUENT — un bouton qui
  // ne fait pas son travail est le defaut le plus visible d'un ecran.
  // `mount` ne transporte pas le generique du composant : on reste donc sur
  // le type de la contrainte, ce qui suffit largement ici.
  type Ligne = Record<string, unknown>
  const LIGNES: Ligne[] = [
    { id: 1, nom: 'Alpha', quantite: 3 },
    { id: 2, nom: 'Beta', quantite: 1 },
  ]
  const COLONNES: Colonne<Ligne>[] = [
    { cle: 'nom', titre: 'Nom' },
    { cle: 'quantite', titre: 'Quantite', champTri: 'quantite' },
  ]
  const cleLigne = (ligne: Ligne) => Number(ligne.id)

  it('affiche ses lignes et le libelle de ses colonnes', () => {
    const vue = mount(Liste, {
      props: { colonnes: COLONNES, lignes: LIGNES, cleLigne },
      slots: { 'col-nom': '<span>{{ params.ligne.nom }}</span>' },
      global: { plugins: [PrimeVue] },
    })
    expect(vue.text()).toContain('Nom')
    expect(vue.text()).toContain('Alpha')
    expect(vue.text()).toContain('Beta')
  })

  it('affiche un etat vide redige plutot qu un tableau muet', () => {
    const vue = mount(Liste, {
      props: { colonnes: COLONNES, lignes: [], cleLigne },
      global: { plugins: [PrimeVue] },
    })
    expect(vue.text()).toContain('Aucun résultat')
  })

  it('le tri par en-tete reordonne vraiment les lignes', async () => {
    // Ce test existe a cause d'une vraie erreur : la premiere version passait
    // un comparateur a `sortFunction`, une option qui n'existe pas dans
    // PrimeVue 5. L'attribut partait dans le DOM et le tri ne faisait RIEN,
    // sans le moindre signal. Un tri qui ne trie pas ressemble a un tri.
    const vue = mount(Liste, {
      props: { colonnes: COLONNES, lignes: LIGNES, cleLigne },
      slots: { 'col-nom': '<span>{{ params.ligne.nom }}</span>' },
      global: { plugins: [PrimeVue] },
    })

    const ordre = () =>
      vue.findAll('tbody tr').map((ligne) => ligne.text().replace(/\s+/g, ' ').trim())

    expect(ordre()[0]).toContain('Alpha')

    // Alpha vaut 3, Beta vaut 1 : trier par quantite croissante met Beta devant.
    await vue.findAll('thead th')[1].trigger('click')
    expect(ordre()[0]).toContain('Beta')

    // Et le second clic inverse le sens.
    await vue.findAll('thead th')[1].trigger('click')
    expect(ordre()[0]).toContain('Alpha')
  })

  it('la ligne entiere est cliquable, pas seulement son bouton', async () => {
    // « Ce n'est pas cliquable, c'est bizarre » : seul le petit bouton en bout
    // de ligne reagissait.
    const vue = mount(Liste, {
      props: { colonnes: COLONNES, lignes: LIGNES, cleLigne },
      slots: { 'col-nom': '<span>{{ params.ligne.nom }}</span>' },
      global: { plugins: [PrimeVue] },
    })

    await vue.findAll('tbody tr')[1].trigger('click')
    const emis = vue.emitted('ligne-cliquee')
    expect(emis).toHaveLength(1)
    expect((emis![0][0] as Ligne).nom).toBe('Beta')
  })

  it('le bouton-symbole porte une infobulle et un libelle accessible', () => {
    const vue = mount(ActionLigne, { props: { titre: 'Consulter', icone: Eye } })
    const bouton = vue.get('button')
    expect(bouton.attributes('title')).toBe('Consulter')
    expect(vue.find('.sr-only').text()).toBe('Consulter')
  })

  it('le bouton-symbole transmet bien le clic a l ecran', async () => {
    // C'est LE test qui compte : un bouton-symbole muet ressemble a un bouton
    // qui marche, et personne ne s'en apercoit avant la demonstration.
    let clics = 0
    const vue = mount(ActionLigne, {
      props: { titre: 'Consulter', icone: Eye, onClick: () => { clics += 1 } },
    })
    await vue.get('button').trigger('click')
    expect(clics).toBe(1)
  })

  it('un bouton-symbole desactive ne declenche rien', async () => {
    let clics = 0
    const vue = mount(ActionLigne, {
      props: { titre: 'Retirer', icone: Eye, desactive: true, onClick: () => { clics += 1 } },
    })
    await vue.get('button').trigger('click')
    expect(clics).toBe(0)
  })
})
