// Le paquet partage est-il vraiment lu par le front web ?
//
// Un alias mal configure echoue en silence a la compilation TypeScript quand
// le module n'est jamais importe : ce test l'importe pour de bon.
import { describe, expect, it } from 'vitest'

import { creerClient, EchecApi } from '@partage/api'
import { COULEURS_ROLE, ETAPES_SUIVI, actionSuivante, euros, tonDuStatut } from '@partage/metier'

describe('le paquet partage', () => {
  it('formate les montants en centimes, jamais en flottants', () => {
    // 18900 centimes, pas 189.0 : un flottant sur de l'argent finit toujours
    // par produire un total a 0,01 pres qui ne tombe pas juste.
    expect(euros(18900).replace(/\u202f|\u00a0/g, ' ')).toBe('189,00 €')
    expect(euros(0).replace(/\u202f|\u00a0/g, ' ')).toBe('0,00 €')
  })

  it('donne une couleur distincte a chaque metier', () => {
    expect(COULEURS_ROLE.CLIENT.accent).not.toBe(COULEURS_ROLE.VENDEUR.accent)
    expect(COULEURS_ROLE.ADMIN.accent).not.toBe(COULEURS_ROLE.LIVREUR.accent)
    // Un visiteur est un futur client : il porte les memes couleurs.
    expect(COULEURS_ROLE.VISITEUR.accent).toBe(COULEURS_ROLE.CLIENT.accent)
  })

  it('n a pas le meme vocabulaire de suivi selon le circuit', () => {
    // Le client d'un restaurant ne comprendrait pas « vers l'entrepot ».
    expect(ETAPES_SUIVI.EXPRESS).toContain('EN_LIVRAISON')
    expect(ETAPES_SUIVI.EXPRESS).not.toContain('EXPEDIEE_ENTREPOT')
    expect(ETAPES_SUIVI.STANDARD).toContain('EXPEDIEE_ENTREPOT')
  })

  it('nomme l action suivante dans les mots du metier', () => {
    expect(actionSuivante('EXPRESS', 'EN_PREPARATION')).toBe('Signaler prête')
    expect(actionSuivante('STANDARD', 'PRETE')).toBe("Expédier vers l'entrepôt")
  })

  it('classe les statuts par ton, une seule fois pour les deux fronts', () => {
    expect(tonDuStatut('LIVREE')).toBe('succes')
    expect(tonDuStatut('ANNULEE')).toBe('erreur')
    expect(tonDuStatut('EN_LIVRAISON')).toBe('cours')
    expect(tonDuStatut('CE_STATUT_N_EXISTE_PAS')).toBe('neutre')
  })

  it('traduit une panne reseau en francais, pas en TypeError', async () => {
    const client = creerClient({ base: 'http://127.0.0.1:1/introuvable' })
    await expect(client.get('/rien')).rejects.toBeInstanceOf(EchecApi)
    await expect(client.get('/rien')).rejects.toThrow(/ne répond pas/)
  })
})
