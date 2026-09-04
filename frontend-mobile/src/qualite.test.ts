// Les gardes du mobile — écrites après le bloc N-6.
//
// Trois défauts avaient traversé toutes les relectures, et aucun ne se voyait
// à l'écran :
//
//   · un commutateur `:checked="true"` **sans gestionnaire** dans le profil.
//     Il glissait, il revenait, et il n'enregistrait rien ;
//   · le bouton « Passer commande » du panier qui **naviguait** vers la liste
//     des commandes au lieu de commander ;
//   · des écrans référencés par le routeur qui auraient pu ne pas exister.
//
// Le point commun : ce sont des **manques**, et un manque ne produit aucune
// erreur. Un test qui monte l'écran ne les attrape pas non plus — il faut
// regarder la source. C'est ce que fait ce fichier.
import { readFileSync, readdirSync, statSync } from 'node:fs'
import { dirname, join, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

import { describe, expect, it } from 'vitest'

const SOURCE = resolve(dirname(fileURLToPath(import.meta.url)))

function fichiersVue(dossier: string): string[] {
  return readdirSync(dossier).flatMap((nom) => {
    const chemin = join(dossier, nom)
    if (statSync(chemin).isDirectory()) return fichiersVue(chemin)
    return nom.endsWith('.vue') ? [chemin] : []
  })
}

const ECRANS = fichiersVue(join(SOURCE, 'vues')).map((chemin) => ({
  chemin,
  nom: chemin.slice(SOURCE.length + 1).replace(/\\/g, '/'),
  source: readFileSync(chemin, 'utf8'),
}))

describe('aucun réglage décoratif', () => {
  // Un commutateur qui ne parle à personne ment sur son propre état : on le
  // pousse, il bascule, on revient, il est revenu comme avant.
  it.each(ECRANS.filter((e) => e.source.includes('<IonToggle')))(
    '$nom — chaque IonToggle enregistre quelque part',
    ({ source }) => {
      const commutateurs = source.match(/<IonToggle[\s\S]*?\/>/g) ?? []
      for (const commutateur of commutateurs) {
        expect(
          commutateur.includes('@ion-change') || commutateur.includes('v-model'),
          `IonToggle sans gestionnaire :\n${commutateur}`,
        ).toBe(true)
      }
    },
  )
})

describe('le parcours du client va jusqu’au bout', () => {
  const panier = ECRANS.find((e) => e.nom.endsWith('Panier.vue'))!
  const commander = ECRANS.find((e) => e.nom.endsWith('Commander.vue'))!
  const commandes = ECRANS.find((e) => e.nom.endsWith('Commandes.vue'))!

  it('le panier mène à l’écran de commande, pas à la liste des commandes', () => {
    // Le défaut d'origine : `routeur.push('/commandes')`. On remplissait un
    // panier et on atterrissait sur une liste vide, sans rien avoir commandé.
    expect(panier.source).toContain("'/commander'")
  })

  it('commander crée la commande ET la paie', () => {
    expect(commander.source).toContain("post<Commande[]>('/commandes'")
    expect(commander.source).toContain('/paiement')
    expect(commander.source).toContain("'/paiements/confirmation'")
  })

  it('commander choisit une adresse : elle décide des boutiques Express', () => {
    expect(commander.source).toContain("'/moi/adresses'")
    expect(commander.source).toContain('id_adresse')
  })

  it('une commande livrée peut être notée et contestée', () => {
    expect(commandes.source).toContain('/avis')
    expect(commandes.source).toContain('/litiges')
    // Et pas n'importe quand : on ne note que ce qu'on a reçu.
    expect(commandes.source).toContain("'LIVREE'")
    expect(commandes.source).toContain("'ECHEC_LIVRAISON'")
  })

  it('une commande payée montre son reçu', () => {
    expect(commandes.source).toContain('/facture')
  })
})

describe('le profil fait ce que ses libellés annoncent', () => {
  const profil = ECRANS.find((e) => e.nom.endsWith('Profil.vue'))!

  it.each([
    ['les préférences', '/moi/parametres'],
    ['les notifications', '/moi/notifications'],
    ['le mot de passe', '/moi/mot-de-passe'],
  ])('%s parlent à l’API (%s)', (_libelle, chemin) => {
    expect(profil.source).toContain(chemin)
  })
})

describe('le livreur a ses quatre gestes', () => {
  const magasin = readFileSync(join(SOURCE, 'magasins', 'livreur.ts'), 'utf8')

  it.each(['accepter', 'recuperer', 'livrer', 'absence'])('%s', (geste) => {
    expect(magasin).toContain(`/${geste}\``)
  })
})

describe('la carte ne porte aucun secret', () => {
  const carte = readFileSync(join(SOURCE, 'composants', 'Carte.vue'), 'utf8')

  it('le tracé est demandé à notre API, pas au fournisseur', () => {
    // La clé d'itinéraire est un vrai secret. Dans une application qu'on
    // installe, tout ce qui est écrit dans le paquet est lisible.
    expect(carte).toContain("'/itineraire'")
    expect(carte).not.toContain('openrouteservice')
    expect(carte).not.toContain('CLE_ITINERAIRE')
  })

  it('le fond de carte est choisi une seule fois, dans le paquet partagé', () => {
    expect(carte).toContain("from '@partage/carte'")
  })

  it('un tracé estimé se présente comme estimé', () => {
    // Faire passer une ligne droite pour un itinéraire routier tromperait le
    // livreur sur la durée de son trajet.
    expect(carte).toContain('simule')
    expect(carte).toContain('line-dasharray')
  })
})

describe('le moteur de cartographie ne se télécharge pas pour rien', () => {
  const ecrans = ECRANS.filter((e) => e.source.includes('<Carte'))

  it('au moins trois écrans du livreur montrent une carte', () => {
    expect(ecrans.length).toBeGreaterThanOrEqual(3)
  })

  it.each(ecrans)('$nom charge la carte paresseusement', ({ source }) => {
    // MapLibre pèse près d'un mégaoctet : un livreur en 4G ne doit pas le
    // télécharger pour consulter ses gains.
    expect(source).toContain('defineAsyncComponent')
    expect(source).not.toMatch(/^import Carte from/m)
  })
})

describe('le routeur ne pointe sur rien d’absent', () => {
  const routeur = readFileSync(join(SOURCE, 'routeur.ts'), 'utf8')
  const cibles = [...routeur.matchAll(/import\('\.\/(vues\/[^']+)'\)/g)].map((m) => m[1])

  it('au moins une douzaine d’écrans sont routés', () => {
    expect(cibles.length).toBeGreaterThanOrEqual(12)
  })

  it.each(cibles)('%s existe', (cible) => {
    expect(() => statSync(join(SOURCE, cible))).not.toThrow()
  })
})
