import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import PrimeVue from 'primevue/config'
import ToastService from 'primevue/toastservice'

import Facture from './vues/client/Facture.vue'
import Paiement from './vues/client/Paiement.vue'
import { routeur } from './routeur'

// L'ecran de paiement manquait, et son absence laissait les commandes en
// attente pour toujours en gardant leur stock reserve. Ces tests verifient ce
// qui compte a l'ecran : le client voit ce qu'il paie, il peut renoncer, et il
// apprend NOMMEMENT ce qui manque quand le stock est parti.
//
// **Depuis O-5, payer exige une carte.** Deux tests de ce fichier echouaient
// apres ce changement, et pour la bonne raison : ils validaient un paiement que
// personne n'avait autorise. Ils posent donc une carte, comme un vrai client.

/** Le carnet de cartes du serveur de test : une carte deja enregistree. */
const CARTE = {
  id: 1, marque: 'VISA', quatre_derniers: '4242', mois_expiration: 12,
  annee_expiration: 2030, par_defaut: true, expiree: false,
  libelle: 'VISA •••• 4242',
}

const CARNET = {
  cartes: [CARTE],
  cartes_d_essai: [{ numero: '4242424242424242', marque: 'VISA', effet: 'acceptée' }],
}

const COMMANDE = {
  id: 12,
  numero_commande: 'RD-260901-ABC123',
  type_service: 'EXPRESS',
  statut_actuel: 'EN_ATTENTE_PAIEMENT',
  libelle_statut: 'En attente de paiement',
  montant_produits_centimes: 2580,
  montant_livraison_centimes: 290,
  montant_total_centimes: 2870,
  date_commande: '2026-09-01T10:00:00Z',
  date_livraison_estimee: null,
  adresse: '8 rue Victor Hugo, 69002 Lyon',
  boutiques: ['Chez Karim'],
  sous_commandes: [
    {
      id: 1,
      boutique: 'Chez Karim',
      statut_preparation: 'A_PREPARER',
      libelle_statut: 'A preparer',
      montant_vendeur_centimes: 2193,
      montant_commission_centimes: 387,
      lignes: [
        {
          id: 1, nom_produit_capture: 'Ramen', prix_unitaire_centimes: 1290,
          quantite: 2, sous_total_centimes: 2580, image: '',
        },
      ],
    },
  ],
}

/** Un serveur de test : une reponse par chemin, et la trace de ce qu'on a appele. */
function serveur(reponses: Record<string, unknown>, appels: string[] = []) {
  return vi.fn(async (url: string, options?: { method?: string }) => {
    const chemin = String(url).replace(/^.*\/api\/v1/, '')
    appels.push(`${options?.method ?? 'GET'} ${chemin}`)
    const trouve = Object.entries(reponses).find(([cle]) => chemin.endsWith(cle))
    if (!trouve) return { ok: false, status: 404, json: async () => ({ erreur: {} }) }
    const corps = trouve[1]
    if (corps && typeof corps === 'object' && 'erreur' in corps) {
      return { ok: false, status: 409, json: async () => corps }
    }
    return { ok: true, status: 200, json: async () => ({ data: corps }) }
  })
}

function monter(composant: unknown, appels: string[] = []) {
  return mount(composant as never, {
    global: { plugins: [routeur, PrimeVue, ToastService], stubs: { Teleport: true } },
  })
}

async function poser() {
  await routeur.push('/paiement')
  await routeur.isReady()
}

describe('l ecran de paiement', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.stubGlobal('localStorage', {
      getItem: () => null, setItem: () => {}, removeItem: () => {},
    })
  })

  it('ouvre une intention par commande en attente et affiche le total', async () => {
    const appels: string[] = []
    vi.stubGlobal('fetch', serveur({
      '/mes-commandes': [COMMANDE],
      '/moi/cartes': CARNET,
      '/paiement': {
        reference: 'pi_sim_abc', secret_client: 'pi_sim_abc_secret',
        montant_centimes: 2870, statut: 'AUTORISE', simule: true,
        reservation_expire_dans_minutes: 10, identifiant_paiement: 5,
      },
    }, appels))

    await poser()
    const ecran = monter(Paiement, appels)
    await new Promise((suite) => setTimeout(suite, 20))

    expect(appels.some((a) => a === 'POST /commandes/12/paiement')).toBe(true)
    // Le total, en toutes lettres : c'est la seule chose que le client verifie.
    expect(ecran.text()).toContain('28,70')
    expect(ecran.text()).toContain('RD-260901-ABC123')
  })

  it('annonce franchement que le paiement est simule', async () => {
    vi.stubGlobal('fetch', serveur({
      '/mes-commandes': [COMMANDE],
      '/moi/cartes': CARNET,
      '/paiement': {
        reference: 'pi_sim_abc', secret_client: 'x', montant_centimes: 2870,
        statut: 'AUTORISE', simule: true, reservation_expire_dans_minutes: 10,
        identifiant_paiement: 5,
      },
    }))

    await poser()
    const ecran = monter(Paiement)
    await new Promise((suite) => setTimeout(suite, 20))

    // La carte est reellement demandee (O-5), mais la simulation reste
    // annoncee et seules les cartes d'essai sont acceptees. Un formulaire qui
    // accepterait tout serait impressionnant trente secondes et malhonnete
    // ensuite.
    expect(ecran.text()).toContain('simulation')
    expect(ecran.text()).toContain('Moyen de paiement')
    expect(ecran.text()).toContain('VISA •••• 4242')
  })

  it('nomme ce qui manque quand le stock est parti', async () => {
    vi.stubGlobal('fetch', serveur({
      '/mes-commandes': [COMMANDE],
      '/moi/cartes': CARNET,
      '/paiement': {
        erreur: {
          code: 'stock_insuffisant',
          message: 'Le stock a change pendant que vous prepariez votre commande.',
          details: { produits: [{ produit: 'Ramen', demande: 2, disponible: 0 }] },
        },
      },
    }))

    await poser()
    const ecran = monter(Paiement)
    await new Promise((suite) => setTimeout(suite, 20))

    // « Stock insuffisant » tout court laisserait le client sans rien a faire.
    expect(ecran.text()).toContain('Ramen')
    expect(ecran.text()).toContain('2 demandes')
  })

  it('offre un vrai bouton pour renoncer', async () => {
    const appels: string[] = []
    vi.stubGlobal('fetch', serveur({
      '/mes-commandes': [COMMANDE],
      '/moi/cartes': CARNET,
      '/paiement/abandonner': { reservation_relachee: true },
      '/paiement': {
        reference: 'pi_sim_abc', secret_client: 'x', montant_centimes: 2870,
        statut: 'AUTORISE', simule: true, reservation_expire_dans_minutes: 10,
        identifiant_paiement: 5,
      },
    }, appels))

    await poser()
    const ecran = monter(Paiement, appels)
    await new Promise((suite) => setTimeout(suite, 20))

    const renoncer = ecran.findAll('button').find((b) => b.text().includes('Renoncer'))
    expect(renoncer, 'le bouton « Renoncer » doit exister').toBeTruthy()
    await renoncer!.trigger('click')
    await new Promise((suite) => setTimeout(suite, 20))

    // Sans cet appel, le stock resterait immobilise dix minutes apres le
    // depart du client (D-100).
    expect(appels).toContain('POST /commandes/12/paiement/abandonner')
  })

  it('n ouvre aucune intention tant qu aucune carte n est choisie', async () => {
    // Le defaut d'origine : « payer est valide sans carte, pas de demande de
    // carte meme la premiere fois ». Sans carte, on ne tente meme pas — le
    // serveur refuserait, et un bandeau rouge a l'ouverture n'aide personne.
    const appels: string[] = []
    vi.stubGlobal('fetch', serveur({
      '/mes-commandes': [COMMANDE],
      '/moi/cartes': { cartes: [], cartes_d_essai: CARNET.cartes_d_essai },
    }, appels))

    await poser()
    monter(Paiement, appels)
    await new Promise((suite) => setTimeout(suite, 30))

    expect(appels.some((a) => a === 'POST /commandes/12/paiement')).toBe(false)
  })

  it('demande une reconfirmation qui dit le montant ET la carte', async () => {
    // « L'argent est paye sans reconfirmation. » Un bouton qui ne dit ni
    // combien ni avec quoi n'est pas une confirmation, c'est un raccourci.
    const appels: string[] = []
    vi.stubGlobal('fetch', serveur({
      '/mes-commandes': [COMMANDE],
      '/moi/cartes': CARNET,
      '/paiement': {
        reference: 'pi_sim_abc', secret_client: 'x', montant_centimes: 2870,
        statut: 'AUTORISE', simule: true, reservation_expire_dans_minutes: 10,
        identifiant_paiement: 5, carte: CARTE,
      },
      '/paiements/confirmation': { statut: 'CAPTURE' },
    }, appels))

    await poser()
    const ecran = monter(Paiement, appels)
    await new Promise((suite) => setTimeout(suite, 30))

    const payer = ecran.findAll('button').find((b) => b.text().includes('Payer 28,70'))
    await payer!.trigger('click')
    await new Promise((suite) => setTimeout(suite, 20))

    // Cliquer n'a PAS paye : il a ouvert la reconfirmation.
    expect(appels.some((a) => a.includes('/paiements/confirmation'))).toBe(false)
    expect(ecran.text()).toContain('Confirmer le paiement')
    expect(ecran.text()).toContain('VISA •••• 4242')
  })

  it('ne montre rien a payer quand tout est regle', async () => {
    vi.stubGlobal('fetch', serveur({
      '/mes-commandes': [{ ...COMMANDE, statut_actuel: 'PAYEE' }],
      '/moi/cartes': CARNET,
    }))

    await poser()
    const ecran = monter(Paiement)
    await new Promise((suite) => setTimeout(suite, 20))

    expect(ecran.text()).toContain('Rien a payer')
  })
})

describe('la facture imprimable', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.stubGlobal('localStorage', {
      getItem: () => null, setItem: () => {}, removeItem: () => {},
    })
    vi.stubGlobal('fetch', serveur({
      '/facture': {
        numero_facture: 'F-RD-260901-ABC123',
        numero_commande: 'RD-260901-ABC123',
        date: '2026-09-01T10:00:00Z',
        adresse: '8 rue Victor Hugo, 69002 Lyon',
        montant_produits_centimes: 2580,
        montant_livraison_centimes: 290,
        montant_total_centimes: 2870,
        montant_ht_centimes: 2392,
        taux_tva: 0.2,
        lignes: [{
          boutique: 'Chez Karim', nom: 'Ramen', quantite: 2,
          prix_unitaire_centimes: 1290, sous_total_centimes: 2580,
        }],
      },
    }))
  })

  it('reprend les lignes, le total et la TVA', async () => {
    await routeur.push('/mes-commandes/12/facture')
    await routeur.isReady()

    const ecran = monter(Facture)
    await new Promise((suite) => setTimeout(suite, 20))

    expect(ecran.text()).toContain('F-RD-260901-ABC123')
    expect(ecran.text()).toContain('Ramen')
    expect(ecran.text()).toContain('28,70')
    expect(ecran.text()).toContain('20 %')
  })

  it('marque ce qui doit disparaitre a l impression', async () => {
    await routeur.push('/mes-commandes/12/facture')
    await routeur.isReady()

    const ecran = monter(Facture)
    await new Promise((suite) => setTimeout(suite, 20))

    // Une facture imprimee avec un bouton « Imprimer » dessus trahit un
    // travail bacle (D-102).
    expect(ecran.find('.sans-impression').exists()).toBe(true)
    expect(ecran.find('.feuille').exists()).toBe(true)
    const bouton = ecran.findAll('button').find((b) => b.text().includes('Imprimer'))
    expect(bouton!.element.closest('.sans-impression')).not.toBeNull()
  })
})
