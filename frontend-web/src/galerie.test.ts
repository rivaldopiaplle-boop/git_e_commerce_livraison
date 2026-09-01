import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import PrimeVue from 'primevue/config'
import ToastService from 'primevue/toastservice'

import FicheProduit from './vues/publiques/FicheProduit.vue'
import { routeur } from './routeur'

// La galerie d'une fiche produit. Une seule photo par produit, c'est ce qui
// distingue un catalogue d'exercice d'une vraie boutique — et l'aperçu animé
// répond à « à quoi ça ressemble vraiment ».
//
// Ce qui est vérifié ici : les vues sont toutes accessibles, l'aperçu est
// reconnaissable au premier coup d'œil, et la galerie se pilote AU CLAVIER.
// Une galerie qui ne répond qu'à la souris exclut.

const PHOTOS = [
  { id: 1, url: '/media/produits/ramen.webp', texte_alternatif: 'Ramen — Chez Karim' },
  { id: 2, url: '/media/produits/ramen-detail.webp', texte_alternatif: 'Ramen — detail' },
  { id: 3, url: '/media/produits/ramen-matiere.webp', texte_alternatif: 'Ramen — matiere' },
  { id: 4, url: '/media/produits/ramen-situation.webp', texte_alternatif: 'Ramen — situation' },
]

function produit(surcharge: Record<string, unknown> = {}) {
  return {
    id: 7,
    nom: 'Bol de ramen maison',
    description: 'Bouillon mijoté douze heures.',
    prix_centimes: 1290,
    image: '/media/produits/ramen.webp',
    photos: PHOTOS,
    apercu: { url: '/media/produits/ramen-apercu.webp', genre: 'image' },
    categorie: { id: 1, nom: 'Plats', slug: 'plats' },
    disponible: true,
    stock_disponible: 12,
    poids_grammes: 400,
    distance_km: 1.2,
    boutique: { id: 1, nom: 'Chez Karim', type_service: 'EXPRESS', ville: 'Lyon' },
    avis: { nombre: 0, note_moyenne: null, repartition: {}, avis: [] },
    produits_similaires: [],
    ...surcharge,
  }
}

function serveur(donnees: unknown) {
  return vi.fn(async () => ({
    ok: true,
    status: 200,
    json: async () => ({ data: donnees }),
  }))
}

async function monter(donnees: unknown) {
  vi.stubGlobal('fetch', serveur(donnees))
  await routeur.push('/produit/7')
  await routeur.isReady()
  const ecran = mount(FicheProduit, {
    global: { plugins: [routeur, PrimeVue, ToastService], stubs: { Teleport: true } },
  })
  await new Promise((suite) => setTimeout(suite, 20))
  return ecran
}

describe('la galerie de la fiche produit', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.stubGlobal('localStorage', {
      getItem: () => null, setItem: () => {}, removeItem: () => {},
    })
  })

  it('montre toutes les vues, plus l aperçu animé', async () => {
    const ecran = await monter(produit())

    // Quatre photos et l'aperçu : cinq vignettes.
    const vignettes = ecran.findAll('button[title]').filter(
      (bouton) => bouton.find('img').exists(),
    )
    expect(vignettes).toHaveLength(5)
    expect(ecran.text()).toContain('1 / 5')
  })

  it('met l aperçu animé en DERNIER, jamais en premier', async () => {
    const ecran = await monter(produit())

    // On regarde d'abord le produit, on l'anime ensuite : c'est l'ordre de
    // toutes les fiches produit des vraies places de marché.
    const grande = ecran.find('img.aspect-4\\/3')
    expect(grande.attributes('src')).toBe('/media/produits/ramen.webp')
  })

  it('signale l aperçu par un symbole de lecture sur sa vignette', async () => {
    const ecran = await monter(produit())

    // Sans ce symbole, la dernière vignette ressemble aux autres et personne
    // ne clique dessus.
    const apercu = ecran.findAll('button[title="Apercu anime"]')
    expect(apercu).toHaveLength(1)
  })

  it('se pilote au clavier, pas seulement à la souris', async () => {
    const ecran = await monter(produit())
    const cadre = ecran.find('[tabindex="0"]')

    await cadre.trigger('keydown.right')
    expect(ecran.text()).toContain('2 / 5')

    await cadre.trigger('keydown.left')
    expect(ecran.text()).toContain('1 / 5')

    // Vers l'arrière depuis la première : on revient à la dernière, on ne
    // reste pas bloqué.
    await cadre.trigger('keydown.left')
    expect(ecran.text()).toContain('5 / 5')
  })

  it('joue une vraie vidéo avec une balise vidéo, pas avec une image', async () => {
    const ecran = await monter(
      produit({ apercu: { url: '/media/produits/ramen.mp4', genre: 'video' } }),
    )

    const cadre = ecran.find('[tabindex="0"]')
    await cadre.trigger('keydown.left')

    // Le serveur dit lequel des deux ; l'écran ne le devine pas depuis
    // l'extension, qui manquerait sur une URL Cloudinary.
    expect(ecran.find('video').exists()).toBe(true)
    expect(ecran.find('video').attributes('src')).toBe('/media/produits/ramen.mp4')
  })

  it('se contente de la photo principale quand il n y a rien d autre', async () => {
    const ecran = await monter(produit({ photos: [], apercu: null }))

    // Une charge utile plus pauvre doit dégrader l'écran, pas le casser.
    expect(ecran.find('img.aspect-4\\/3').attributes('src'))
      .toBe('/media/produits/ramen.webp')
    expect(ecran.text()).not.toContain('1 / 1')
  })

  it('affiche un badge lisible pour le mode de livraison', async () => {
    const ecran = await monter(produit())

    // Le badge était écrit en amber-300 sur un fond amber-500/15 : du clair
    // sur du clair, exactement la maladie du bloc J. Il passe par les jetons.
    const badge = ecran.find('.badge')
    expect(badge.exists()).toBe(true)
    expect(badge.classes()).toContain('badge-attente')
    expect(badge.text()).toContain('Express')
  })
})
