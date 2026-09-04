import { readFileSync, readdirSync, statSync } from 'node:fs'
import { dirname, join, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

import { describe, expect, it } from 'vitest'

// Deux pièges de dépendances que ce projet s'est pris en pleine figure, et que
// rien ne signalait. Ces tests sont là pour qu'ils ne reviennent pas.

const RACINE = resolve(__dirname, '..')

function paquet(chemin: string) {
  return JSON.parse(readFileSync(resolve(RACINE, chemin), 'utf-8'))
}

function fichiersVue(dossier: string): string[] {
  return readdirSync(dossier).flatMap((nom) => {
    const chemin = join(dossier, nom)
    return statSync(chemin).isDirectory()
      ? fichiersVue(chemin)
      : nom.endsWith('.vue') ? [chemin] : []
  })
}

const NOTRE_PAQUET = paquet('package.json')
const DEPENDANCES: Record<string, string> = NOTRE_PAQUET.dependencies

describe('la licence de la bibliotheque de composants', () => {
  it('reste sur PrimeVue 4, qui est sous licence MIT', () => {
    // PrimeVue **5** exige une clé de licence. Sans elle, il injecte lui-même
    // dans la page un bandeau rouge « Invalid PrimeUI License », en position
    // fixe en bas à droite, sur TOUS les écrans — y compris dans le build de
    // production. Pour un projet montré à des recruteurs, c'est rédhibitoire.
    //
    // La version 4 offre exactement les mêmes composants (DataTable, Dialog,
    // Chart, Toast, Rating) sous licence MIT, sans clé et sans expiration.
    // D-26 demandait « l'équivalent de MUI » : la 4 le remplit entièrement.
    const version = DEPENDANCES.primevue
    expect(version, 'primevue doit rester en version 4 (MIT)').toMatch(/^\^?4\./)
    expect(DEPENDANCES['@primevue/themes']).toMatch(/^\^?4\./)
  })

  it('n a pas gardé le paquet de themes de la version 5', () => {
    // `@primeuix/themes` est le paquet de thèmes de PrimeVue 5. Le laisser
    // installé réintroduirait la vérification de licence par la bande.
    expect(DEPENDANCES['@primeuix/themes']).toBeUndefined()
  })

  it('ne contient pas le code du bandeau de licence', () => {
    // La vraie garantie : le message n'est nulle part dans la bibliothèque
    // installée. Une version qui changerait de nom de paquet passerait les
    // deux tests ci-dessus, pas celui-ci.
    const source = readFileSync(
      resolve(RACINE, 'node_modules/primevue/umd/primevue.min.js'),
      'utf-8',
    )
    expect(source).not.toContain('Invalid PrimeUI License')
  })
})

describe('la coherence des versions', () => {
  it('accorde zod avec l adaptateur qui le consomme', () => {
    // `@vee-validate/zod` exige zod 3. Le projet avait zod 4 : l'installation
    // marchait — le fichier de verrou datait d'avant — mais **tout `npm
    // install` d'un nouveau paquet échouait** avec ERESOLVE. On ne s'en
    // aperçoit que le jour où on veut ajouter une dépendance, et on croit
    // alors que c'est la nouvelle qui pose problème.
    const adaptateur = paquet('node_modules/@vee-validate/zod/package.json')
    const exige = adaptateur.peerDependencies?.zod as string

    expect(exige).toBeTruthy()
    const majeurExige = exige.replace(/[^0-9.]/g, '').split('.')[0]
    const majeurInstalle = paquet('node_modules/zod/package.json').version.split('.')[0]
    expect(majeurInstalle).toBe(majeurExige)
  })

  it('installe chart.js, dont le composant Chart a besoin', () => {
    // `Chart` de PrimeVue n'embarque pas chart.js : c'est une dépendance de
    // pair. Sans elle, le composant se monte et ne dessine rien — en silence.
    expect(DEPENDANCES['chart.js']).toBeTruthy()
  })
})

// ── Les écrans de travail ne restent pas figés — O-5 ─────────────────────
//
// « Surtout, surtout, surtout, surtout rien n'est synchronisé et dynamique. »
// Le reproche portait d'abord sur le mobile, mais le web avait sa version du
// défaut : un vendeur laisse « Commandes reçues » ouvert toute la journée, et
// ne voit rien arriver tant qu'il ne rafraîchit pas à la main.
describe('les ecrans qu on laisse ouverts se rafraichissent', () => {
  const ECRANS = fichiersVue(resolve(dirname(fileURLToPath(import.meta.url)), 'vues'))
    .map((chemin) => ({ nom: chemin, source: readFileSync(chemin, 'utf8') }))

  const FILES_VIVANTES = [
    'CommandesRecues.vue', 'Colis.vue', 'Tournees.vue', 'MesCourses.vue',
    'MesCommandes.vue', 'Litiges.vue', 'LitigesVendeur.vue',
  ]

  it.each(FILES_VIVANTES)('%s se recharge en fond', (nom) => {
    const ecran = ECRANS.find((e) => e.nom.endsWith(nom))!
    expect(ecran.source).toContain('useRafraichissement')
    expect(ecran.source).toContain('periodique: true')
  })

  it('un rafraichissement de fond ne vole pas la selection', () => {
    // Rouvrir d'office la premiere ligne a chaque passage ferait sauter le
    // volet de droite toutes les vingt secondes, sous les yeux de la personne.
    for (const nom of ['MesCommandes.vue', 'CommandesRecues.vue', 'MesCourses.vue',
                       'Tournees.vue']) {
      const ecran = ECRANS.find((e) => e.nom.endsWith(nom))!
      expect(ecran.source, nom).toContain('premierChargement')
    }
  })
})
