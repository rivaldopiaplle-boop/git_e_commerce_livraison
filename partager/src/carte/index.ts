// Le fond de carte, choisi une seule fois pour les deux fronts — D-142.
//
// **Aucune clé n'est nécessaire pour que la carte s'affiche.** C'est la règle
// D-18 appliquée au fond de carte : le projet se démontre entièrement sans
// compte chez qui que ce soit, et une clé n'améliore que le rendu.
//
// Par défaut : **OpenFreeMap**, qui sert des tuiles vectorielles OpenStreetMap
// sans clé, sans quota et sans inscription. C'est le seul fournisseur sérieux
// dans ce cas — les autres exigent tous une clé, et la plupart une carte
// bancaire pour la délivrer.
//
// Avec `VITE_STYLE_CARTE`, on passe à un style plus soigné — MapTiler Streets,
// Stadia Maps, ou n'importe quelle URL de style MapLibre. Le rendu est plus
// beau, les libellés mieux placés, le relief présent. Rien d'autre ne change.

/** Le style par défaut, sans clé. Le rendu est correct, pas somptueux. */
export const STYLE_PAR_DEFAUT = 'https://tiles.openfreemap.org/styles/liberty'

/**
 * L'URL du style à passer à MapLibre.
 *
 * `VITE_STYLE_CARTE` contient une URL complète, clé comprise — et c'est
 * volontaire : une clé de tuiles est **publique par nature**, puisqu'elle part
 * dans chaque requête du navigateur. Elle se protège par la liste des domaines
 * autorisés chez le fournisseur, jamais par le secret. Une clé de tuiles n'est
 * donc pas un secret, contrairement à `CLE_ITINERAIRE`, qui reste côté serveur.
 */
export function styleDeCarte(): string {
  const configure = (import.meta as { env?: Record<string, string> }).env?.VITE_STYLE_CARTE
  return (configure || '').trim() || STYLE_PAR_DEFAUT
}

/** Lyon, centre de la démonstration. Utilisé quand aucun point n'est situé. */
export const CENTRE_PAR_DEFAUT: [number, number] = [4.8357, 45.764]

export type Point = {
  /** L'ordre GeoJSON : longitude d'abord. Inverser est LA erreur des cartes. */
  lon: number
  lat: number
  libelle?: string
  /** Un numéro d'arrêt, ou rien pour une pastille simple. */
  rang?: number
  /** La pastille de départ se distingue des arrêts. */
  depart?: boolean
}

/**
 * Le cadre qui contient tous les points, avec une marge.
 *
 * Sans cela, une carte centrée sur le premier point laisse les autres hors de
 * l'écran, et on croit qu'ils manquent.
 */
export function cadre(points: Point[]): [[number, number], [number, number]] | null {
  const situes = points.filter((point) => Number.isFinite(point.lat) && Number.isFinite(point.lon))
  if (!situes.length) return null

  const lons = situes.map((point) => point.lon)
  const lats = situes.map((point) => point.lat)
  return [
    [Math.min(...lons), Math.min(...lats)],
    [Math.max(...lons), Math.max(...lats)],
  ]
}
