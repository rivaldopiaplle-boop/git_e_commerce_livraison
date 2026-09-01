/**
 * Les réglages communs à tous les graphiques — D-83.
 *
 * Ils étaient dessinés à la main, en `<div>` de hauteur variable. Ça marchait
 * pour trente barres et pour rien d'autre : ni axe, ni échelle lisible, ni
 * infobulle, ni adaptation à la largeur. Écrire cela soi-même est exactement
 * ce que la règle d'or n°5 interdit — `chart.js`, que PrimeVue enveloppe déjà,
 * fait le travail depuis dix ans.
 *
 * Ce fichier existe pour qu'un graphe ait la même tête partout : mêmes
 * couleurs, même grille, même infobulle. Trois graphiques réglés séparément
 * finissent toujours par se contredire.
 */

/** La couleur d'accent du rôle courant, lue sur le document. */
function accent() {
  if (typeof window === 'undefined') return '#2563eb'
  const valeur = getComputedStyle(document.documentElement)
    .getPropertyValue('--accent')
    .trim()
  return valeur || '#2563eb'
}

const ENCRE_DOUCE = '#5b6478'
const TRAIT = '#eef0f5'

export const euros = (centimes: number) =>
  (centimes / 100).toLocaleString('fr-FR', { style: 'currency', currency: 'EUR' })

/** Une date ISO en « 03/09 » : sur trente points, le jour et le mois suffisent. */
export const jourCourt = (jour: string) =>
  new Date(jour).toLocaleDateString('fr-FR', { day: '2-digit', month: '2-digit' })

/**
 * Les options d'un graphe de série temporelle.
 *
 * `maintainAspectRatio: false` est indispensable : sans lui, chart.js impose
 * sa propre hauteur et le graphe déborde de sa carte sur un écran étroit.
 */
export function optionsTemporelles(formatteur: (valeur: number) => string) {
  return {
    responsive: true,
    maintainAspectRatio: false,
    interaction: { mode: 'index' as const, intersect: false },
    plugins: {
      legend: {
        display: true,
        position: 'bottom' as const,
        labels: { usePointStyle: true, boxWidth: 8, color: ENCRE_DOUCE,
                  font: { size: 11 } },
      },
      tooltip: {
        // L'infobulle donne le montant en euros, pas en centimes : personne
        // ne lit « 2670 » comme « 26,70 € ».
        callbacks: {
          label: (contexte: { dataset: { label?: string }; parsed: { y: number } }) =>
            `${contexte.dataset.label} : ${formatteur(contexte.parsed.y)}`,
        },
      },
    },
    scales: {
      x: {
        grid: { display: false },
        ticks: { color: ENCRE_DOUCE, font: { size: 10 }, maxRotation: 0, autoSkip: true },
      },
      y: {
        beginAtZero: true,
        grid: { color: TRAIT },
        border: { display: false },
        ticks: { color: ENCRE_DOUCE, font: { size: 10 }, precision: 0 },
      },
    },
  }
}

/** Les options d'un anneau : ni axe ni grille, la légende porte tout. */
export function optionsAnneau(formatteur: (valeur: number) => string) {
  return {
    responsive: true,
    maintainAspectRatio: false,
    cutout: '62%',
    plugins: {
      legend: {
        position: 'right' as const,
        labels: { usePointStyle: true, boxWidth: 8, color: ENCRE_DOUCE,
                  font: { size: 11 } },
      },
      tooltip: {
        callbacks: {
          label: (contexte: { label: string; parsed: number }) =>
            `${contexte.label} : ${formatteur(contexte.parsed)}`,
        },
      },
    },
  }
}

/** Une série remplie sous la courbe, aux couleurs du rôle. */
export function serieAccent(libelle: string, valeurs: number[]) {
  const couleur = accent()
  return {
    label: libelle,
    data: valeurs,
    borderColor: couleur,
    backgroundColor: `color-mix(in srgb, ${couleur} 14%, transparent)`,
    fill: true,
    tension: 0.3,
    pointRadius: 2,
    pointHoverRadius: 5,
    borderWidth: 2,
  }
}

/** Une seconde série, discrète : elle accompagne, elle ne rivalise pas. */
export function serieSecondaire(libelle: string, valeurs: number[]) {
  return {
    label: libelle,
    data: valeurs,
    borderColor: ENCRE_DOUCE,
    backgroundColor: ENCRE_DOUCE,
    borderDash: [4, 3],
    fill: false,
    tension: 0.3,
    pointRadius: 2,
    borderWidth: 1.5,
    yAxisID: 'y2',
  }
}

/**
 * La palette des parts, dérivée de l'accent.
 *
 * Sept couleurs fixes : au-delà, un camembert ne se lit plus, et il vaut mieux
 * regrouper la queue sous « Autres » que d'inventer une huitième teinte.
 */
export function palette(): string[] {
  const couleur = accent()
  return [
    couleur,
    `color-mix(in srgb, ${couleur} 72%, white)`,
    `color-mix(in srgb, ${couleur} 50%, white)`,
    `color-mix(in srgb, ${couleur} 32%, white)`,
    '#93a0b5',
    '#c3cad6',
    '#e4e7ee',
  ]
}
