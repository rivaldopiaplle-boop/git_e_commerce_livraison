import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'

import { describe, expect, it } from 'vitest'

// Deux pièges de dépendances que ce projet s'est pris en pleine figure, et que
// rien ne signalait. Ces tests sont là pour qu'ils ne reviennent pas.

const RACINE = resolve(__dirname, '..')

function paquet(chemin: string) {
  return JSON.parse(readFileSync(resolve(RACINE, chemin), 'utf-8'))
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
