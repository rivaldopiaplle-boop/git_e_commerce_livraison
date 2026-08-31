// Le seul endroit du projet qui parle à l'API — web et mobile confondus.
//
// Tout y passe : le jeton, la clé de panier, le format d'erreur, l'URL de
// base. Le jour où l'un des quatre change, un seul fichier bouge, et aucun
// écran n'a besoin de savoir qu'un jeton existe.
//
// Il est écrit comme une **fabrique** plutôt qu'un module à état global,
// parce que le mobile n'a pas la même URL de base que le web (une application
// installée ne peut pas parler à `localhost`) et parce qu'un test doit pouvoir
// créer un client isolé sans polluer les autres.
import type { ErreurApi } from '../types'

export class EchecApi extends Error {
  constructor(
    public statut: number,
    public erreur: ErreurApi,
  ) {
    super(erreur.message)
    this.name = 'EchecApi'
  }
}

export type OptionsClient = {
  base: string
  /** Appelée quand le serveur répond 401 : le jeton a expiré ou été révoqué. */
  surSessionPerdue?: () => void
}

export function creerClient({ base, surSessionPerdue }: OptionsClient) {
  let jetonAcces: string | null = null
  let cleSession: string | null = null

  async function appeler<T>(chemin: string, options: RequestInit = {}): Promise<T> {
    let reponse: Response
    try {
      reponse = await fetch(`${base}${chemin}`, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          ...(jetonAcces ? { Authorization: `Bearer ${jetonAcces}` } : {}),
          // La clé qui identifie le panier d'un visiteur sans compte (D-34).
          ...(cleSession ? { 'X-Panier-Session': cleSession } : {}),
          ...options.headers,
        },
      })
    } catch {
      // Le serveur n'a pas répondu du tout : on le dit en français, pas par un
      // « TypeError: Failed to fetch » que personne ne peut interpréter.
      throw new EchecApi(0, {
        code: 'reseau',
        message: "L'API ne répond pas. Vérifiez votre connexion.",
        details: {},
      })
    }

    if (reponse.status === 204) return undefined as T

    const corps = await reponse.json().catch(() => null)

    if (!reponse.ok) {
      if (reponse.status === 401) surSessionPerdue?.()
      const erreur: ErreurApi = corps?.erreur ?? {
        code: 'inconnue',
        message: `Erreur ${reponse.status}.`,
        details: {},
      }
      throw new EchecApi(reponse.status, erreur)
    }

    // L'API enveloppe toujours ses réponses dans { data: … } (contrat-api.md).
    return (corps?.data ?? corps) as T
  }

  /** Le corps complet, quand on a besoin de `meta` en plus de `data`. */
  async function appelerComplet<T>(chemin: string): Promise<T> {
    const reponse = await fetch(`${base}${chemin}`, {
      headers: {
        ...(jetonAcces ? { Authorization: `Bearer ${jetonAcces}` } : {}),
        ...(cleSession ? { 'X-Panier-Session': cleSession } : {}),
      },
    }).catch(() => null)

    if (!reponse || !reponse.ok) {
      throw new EchecApi(reponse?.status ?? 0, {
        code: 'reseau',
        message: "L'API ne répond pas.",
        details: {},
      })
    }
    return (await reponse.json()) as T
  }

  /** Un envoi multipart ne doit PAS porter d'en-tête Content-Type fixe : le
   *  navigateur écrit lui-même la frontière entre les fichiers. */
  async function televerser<T>(chemin: string, champ: string, fichiers: File[]): Promise<T> {
    const corps = new FormData()
    for (const fichier of fichiers) corps.append(champ, fichier)

    const reponse = await fetch(`${base}${chemin}`, {
      method: 'POST',
      headers: jetonAcces ? { Authorization: `Bearer ${jetonAcces}` } : {},
      body: corps,
    })
    const donnees = await reponse.json().catch(() => null)
    if (!reponse.ok) {
      throw new EchecApi(reponse.status, donnees?.erreur ?? {
        code: 'televersement', message: "L'envoi a échoué.", details: {},
      })
    }
    return donnees.data as T
  }

  return {
    poserJeton(jeton: string | null) {
      jetonAcces = jeton
    },
    poserCleSession(cle: string | null) {
      cleSession = cle
    },
    get: <T>(chemin: string) => appeler<T>(chemin),
    post: <T>(chemin: string, corps?: unknown) =>
      appeler<T>(chemin, { method: 'POST', body: JSON.stringify(corps ?? {}) }),
    patch: <T>(chemin: string, corps: unknown) =>
      appeler<T>(chemin, { method: 'PATCH', body: JSON.stringify(corps) }),
    supprimer: <T>(chemin: string) => appeler<T>(chemin, { method: 'DELETE' }),
    appelerComplet,
    televerser,
  }
}

export type ClientApi = ReturnType<typeof creerClient>
