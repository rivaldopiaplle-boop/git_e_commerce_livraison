import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import PrimeVue from 'primevue/config'

import Accueil from './vues/Accueil.vue'
import Statistiques from './vues/vendeur/Statistiques.vue'
import { routeur } from './routeur'
import { useAuthentification } from './stores/authentification'

// Le tableau de bord — L-2, L-3.
//
// **Ta remarque, répétée deux fois** : *« la dashboard n'est pas cliquable,
// n'est pas jolie »*. Un KPI qui ne mène nulle part est un élément mort qui
// trompe l'œil : si quelque chose a l'air interactif, il doit l'être.
//
// Et *« il n'y a pas assez de graphe statistique »* : la courbe était dessinée
// à la main en `<div>` de hauteur variable. Elle passe sur `Chart` de PrimeVue.

const TABLEAU_VENDEUR = {
  a_preparer: 3,
  produits_en_ligne: 12,
  stock_bas: 2,
  ruptures: 1,
  revenu_centimes: 128_400,
  produits_stock_bas: [],
}

const STATISTIQUES = {
  commandes: 8,
  revenu_centimes: 128_400,
  commission_centimes: 22_600,
  taux_commission: 0.15,
  panier_moyen_centimes: 16_050,
  par_jour: [
    { jour: '2026-08-28', commandes: 2, montant_centimes: 3200 },
    { jour: '2026-08-29', commandes: 5, montant_centimes: 8400 },
    { jour: '2026-08-30', commandes: 1, montant_centimes: 1900 },
  ],
  meilleurs_produits: [
    { nom_produit_capture: 'Ramen', quantite: 12, montant_centimes: 15_480 },
    { nom_produit_capture: 'Gyoza', quantite: 7, montant_centimes: 5_600 },
  ],
  note_moyenne: 4.2,
  nombre_avis: 5,
  derniers_avis: [
    { note: 5, commentaire: 'Parfait.', statut: 'PUBLIE' },
    { note: 4, commentaire: '', statut: 'PUBLIE' },
    { note: 1, commentaire: 'Froid.', statut: 'SIGNALE' },
  ],
}

function serveur(donnees: unknown) {
  return vi.fn(async () => ({ ok: true, status: 200, json: async () => ({ data: donnees }) }))
}

/**
 * Un faux `Chart` qui DECLARE ses props.
 *
 * `stubs: { Chart: true }` en fabrique un sans props : `props('data')` rend
 * alors `undefined`, et le test verifie du vide en croyant verifier un
 * graphe. Le vrai composant a besoin d'un canvas, que jsdom n'a pas.
 */
const FauxGraphe = {
  name: 'Chart',
  props: ['type', 'data', 'options'],
  template: '<div class="faux-graphe"></div>',
}

function enVendeur() {
  const session = useAuthentification()
  session.utilisateur = {
    id: 1, email: 'karim@exemple.fr', nom: 'Benali', prenom: 'Karim',
    role: 'VENDEUR', statut_compte: 'ACTIF',
  } as never
}

async function monter(composant: unknown, donnees: unknown) {
  vi.stubGlobal('fetch', serveur(donnees))
  enVendeur()
  await routeur.push('/espace')
  await routeur.isReady()
  const ecran = mount(composant as never, {
    global: { plugins: [routeur, PrimeVue], stubs: { Teleport: true, Chart: FauxGraphe } },
  })
  await new Promise((suite) => setTimeout(suite, 20))
  return ecran
}

describe('le tableau de bord', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.stubGlobal('localStorage', {
      getItem: () => null, setItem: () => {}, removeItem: () => {},
    })
  })

  it('fait de chaque indicateur un lien, jamais un bloc mort', async () => {
    const ecran = await monter(Accueil, TABLEAU_VENDEUR)

    const indicateurs = ecran.findAll('.kpi')
    expect(indicateurs.length).toBe(5)
    // Le point de la remarque : aucun ne doit rester un simple <div>.
    for (const indicateur of indicateurs) {
      expect(indicateur.element.tagName).toBe('A')
      expect(indicateur.attributes('href')).toBeTruthy()
    }
  })

  it('envoie chaque indicateur sur l ecran qui le detaille', async () => {
    const ecran = await monter(Accueil, TABLEAU_VENDEUR)

    const liens = ecran.findAll('.kpi').map((element) => element.attributes('href'))
    expect(liens).toContain('/espace/commandes')
    expect(liens).toContain('/espace/catalogue')
    expect(liens).toContain('/espace/statistiques')
  })

  it('emmene les alertes sur le bon onglet, pas juste sur le bon ecran', async () => {
    const ecran = await monter(Accueil, TABLEAU_VENDEUR)

    // « 2 produits sous le seuil » doit ouvrir la liste DES ALERTES, pas le
    // catalogue entier ou il faudrait les rechercher.
    const alerte = ecran.findAll('.kpi').find(
      (element) => element.text().includes('seuil d alerte'),
    )
    expect(alerte?.attributes('href')).toContain('onglet=alertes')
  })

  it('signale visuellement qu un indicateur se clique', async () => {
    const ecran = await monter(Accueil, TABLEAU_VENDEUR)

    // Curseur, elevation au survol, fleche revelee : sans cela, le lien
    // existe mais rien ne le laisse deviner.
    expect(ecran.find('.kpi').classes()).toContain('kpi-cliquable')
  })

  it('met en avant ce qui depasse un seuil', async () => {
    const ecran = await monter(Accueil, TABLEAU_VENDEUR)

    const alertes = ecran.findAll('.kpi-alerte')
    expect(alertes.length).toBe(2)
  })
})

describe('les statistiques du vendeur', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.stubGlobal('localStorage', {
      getItem: () => null, setItem: () => {}, removeItem: () => {},
    })
  })

  it('dessine trois graphiques avec la bibliotheque, pas a la main', async () => {
    const ecran = await monter(Statistiques, STATISTIQUES)

    // La courbe etait faite en <div> de hauteur variable : ca marchait pour
    // trente barres et pour rien d'autre.
    const graphiques = ecran.findAllComponents({ name: 'Chart' })
    expect(graphiques.length).toBe(3)
  })

  it('donne au graphe des ventes deux series : le montant ET les commandes', async () => {
    const ecran = await monter(Statistiques, STATISTIQUES)

    // Un montant qui monte parce qu'on a vendu un article cher ne veut pas
    // dire la meme chose qu'un montant qui monte parce qu'on a vendu dix fois
    // plus.
    const courbe = ecran.findAllComponents({ name: 'Chart' })[0]
    const donnees = courbe.props('data') as { datasets: { label: string }[] }
    expect(donnees.datasets.map((serie) => serie.label))
      .toEqual(['Encaissé', 'Commandes'])
  })

  it('repartit les notes au lieu de se contenter de la moyenne', async () => {
    const ecran = await monter(Statistiques, STATISTIQUES)

    // 4/5 de moyenne avec dix 5 et deux 1, ce n'est pas 4/5 partout.
    const notes = ecran.findAllComponents({ name: 'Chart' })[2]
    const donnees = notes.props('data') as { labels: string[]; datasets: { data: number[] }[] }
    expect(donnees.labels[0]).toBe('5 étoiles')
    expect(donnees.datasets[0].data).toEqual([1, 1, 0, 0, 1])
  })

  it('garde le classement chiffre a cote de l anneau', async () => {
    const ecran = await monter(Statistiques, STATISTIQUES)

    // Un anneau donne la proportion, pas le chiffre exact ni la quantite.
    expect(ecran.text()).toContain('Ramen')
    expect(ecran.text()).toContain('12 vendu(s)')
    expect(ecran.text()).toContain('154,80')
  })

  it('affiche un etat vide redige quand il n y a rien a montrer', async () => {
    const ecran = await monter(Statistiques, {
      ...STATISTIQUES, par_jour: [], meilleurs_produits: [], derniers_avis: [],
    })

    expect(ecran.text()).toContain('Aucune vente sur la période')
    expect(ecran.findAllComponents({ name: 'Chart' }).length).toBe(0)
  })
})
