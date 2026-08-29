// Le test qui empeche l'ecran blanc sur blanc de revenir.
//
// Deux fois de suite, un renommage dans `style.css` a laisse des ecrans sans
// aucun style : une classe Tailwind qui pointe vers un jeton inexistant ne
// produit RIEN — pas d'erreur, pas d'avertissement, juste du texte blanc sur
// fond blanc que seul un oeil humain remarque.
//
// Ce test lit le theme, lit tous les ecrans, et refuse toute classe de
// couleur ou toute classe de composant qui n'existe pas.
import { readFileSync, readdirSync, statSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'
import { describe, expect, it } from 'vitest'

const SOURCE = dirname(fileURLToPath(import.meta.url))

function fichiers(dossier: string, extensions: string[]): string[] {
  return readdirSync(dossier).flatMap((entree: string) => {
    const chemin = join(dossier, entree)
    if (statSync(chemin).isDirectory()) return fichiers(chemin, extensions)
    return extensions.some((extension) => entree.endsWith(extension)) ? [chemin] : []
  })
}

const feuille = readFileSync(join(SOURCE, 'style.css'), 'utf8')

/** Les noms declares dans `@theme` : `--color-encre` donne `encre`. */
const jetons = new Set(
  [...feuille.matchAll(/--color-([a-z0-9-]+):/g)].map((trouve) => trouve[1]),
)

/** Les classes definies dans `@layer components` : `.carte` donne `carte`. */
const composants = new Set(
  [...feuille.matchAll(/^\s{2}\.([a-z0-9-]+)\s*\{/gm)].map((trouve) => trouve[1]),
)

const PREFIXES = [
  'bg', 'text', 'border', 'ring', 'fill', 'stroke', 'divide', 'outline',
  'placeholder', 'from', 'to', 'via', 'shadow', 'accent', 'caret', 'decoration',
]

// Les familles de couleurs livrees par Tailwind : elles existent sans etre
// declarees dans `@theme`, et rien ne sert de les signaler.
const TAILWIND = new Set([
  'white', 'black', 'transparent', 'current', 'inherit', 'slate', 'gray', 'zinc',
  'neutral', 'stone', 'red', 'orange', 'amber', 'yellow', 'lime', 'green',
  'emerald', 'teal', 'cyan', 'sky', 'blue', 'indigo', 'violet', 'purple',
  'fuchsia', 'pink', 'rose',
])

const ecrans = fichiers(SOURCE, ['.vue'])

describe('les jetons de couleur', () => {
  it('sont tous declares dans le theme', () => {
    const motif = new RegExp(
      String.raw`(?:^|[\s"'\`:{[(])(?:hover:|focus:|focus-visible:|active:|disabled:|group-hover:|last:|first:|sm:|md:|lg:|xl:|2xl:|dark:|!)*(` +
        PREFIXES.join('|') +
        String.raw`)-([a-z][a-z0-9]*(?:-[a-z0-9]+)*)(?:\/\d+)?(?=[\s"'\`\]}]|$)`,
      'gm',
    )

    const fautifs: string[] = []
    for (const chemin of ecrans) {
      const contenu = readFileSync(chemin, 'utf8')
      for (const trouve of contenu.matchAll(motif)) {
        const valeur = trouve[2]
        const racine = valeur.split('-')[0]
        if (TAILWIND.has(racine) || TAILWIND.has(valeur)) continue
        // Un jeton peut etre compose : `marque-clair` comme `marque`.
        if (jetons.has(valeur)) continue
        // Certaines classes Tailwind ne sont pas des couleurs : `text-left`,
        // `border-dashed`, `bg-cover`. On ne garde que ce qui ressemble a un
        // jeton de ce projet, c'est-a-dire un nom deja connu a sa racine.
        if (!jetons.has(racine)) continue
        fautifs.push(`${chemin.split(/[\\/]/).pop()} : ${trouve[1]}-${valeur}`)
      }
    }

    expect(fautifs).toEqual([])
  })

  it('couvre les classes de composants utilisees dans les ecrans', () => {
    // `carte-sombre`, `champ-marque` et `bouton-discret` ont disparu du CSS
    // sans que leurs usages suivent. Le meme oubli ne doit plus passer.
    const connues = new Set([...composants])
    const fautifs: string[] = []

    for (const chemin of ecrans) {
      const contenu = readFileSync(chemin, 'utf8')
      for (const trouve of contenu.matchAll(/\bclass="([^"]*)"/g)) {
        for (const classe of trouve[1].split(/\s+/)) {
          if (!/^(carte|ligne|badge|kpi|champ|puce|bouton|bandeau|vide|etiquette)(-[a-z]+)*$/
            .test(classe)) {
            continue
          }
          if (!connues.has(classe)) fautifs.push(`${chemin.split(/[\\/]/).pop()} : .${classe}`)
        }
      }
    }

    expect(fautifs).toEqual([])
  })
})
