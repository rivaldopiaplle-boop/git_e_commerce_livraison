import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createRouter, createWebHistory } from 'vue-router'

import EntetePublic from './composants/EntetePublic.vue'
import CarteProduit from './composants/CarteProduit.vue'

const routeur = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'vitrine', component: { template: '<div/>' } },
    { path: '/produit/:id', name: 'produit', component: { template: '<div/>' } },
    { path: '/rejoindre', name: 'rejoindre', component: { template: '<div/>' } },
    { path: '/connexion', name: 'connexion', component: { template: '<div/>' } },
    { path: '/inscription', name: 'inscription', component: { template: '<div/>' } },
    { path: '/espace', name: 'espace', component: { template: '<div/>' } },
  ],
})

describe('les liens de navigation existent vraiment', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.stubGlobal('localStorage', {
      getItem: () => null, setItem: () => {}, removeItem: () => {},
    })
  })

  it('en-tete : les liens existent et pointent quelque part', async () => {
    routeur.push('/')
    await routeur.isReady()
    const composant = mount(EntetePublic, { global: { plugins: [routeur] } })
    const liens = composant.findAll('a').map((a) => a.attributes('href'))
    expect(liens).toContain('/rejoindre')
    expect(liens).toContain('/connexion')
    expect(liens).toContain('/inscription')
  })

  it('carte produit : la carte entiere est un lien vers la fiche', async () => {
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
