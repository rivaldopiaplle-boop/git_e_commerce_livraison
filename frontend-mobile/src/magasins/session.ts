// La session mobile.
//
// Elle ressemble à celle du web, mais elle ne la partage PAS : le stockage
// n'est pas le même (`localStorage` du navigateur contre le stockage de
// l'application installée), et un magasin qui suppose l'un casse dans
// l'autre. Ce qui est commun — le client d'API, les types — vient de
// `@partage`.
import { creerClient, type ClientApi } from '@partage/api'
import type { Role, Utilisateur } from '@partage/types'
import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

import { URL_API } from '@/config'

const CLE = 'rivdinde.mobile.session'

type Identite = {
  utilisateur: Utilisateur
  profil: Record<string, unknown> | null
  acces: string
  rafraichissement: string
}

export const useSession = defineStore('session', () => {
  const utilisateur = ref<Utilisateur | null>(null)
  const profil = ref<Record<string, unknown> | null>(null)
  const chargement = ref(false)
  const erreur = ref('')

  const client: ClientApi = creerClient({
    base: URL_API,
    // Un jeton expiré ne doit pas laisser l'application dans un état à moitié
    // connecté, où les écrans se vident sans explication.
    surSessionPerdue: () => deconnecter(),
  })

  const estConnecte = computed(() => utilisateur.value !== null)
  const role = computed<Role | null>(() => utilisateur.value?.role ?? null)
  const enAttenteDeValidation = computed(
    () => utilisateur.value?.statut_compte === 'EN_ATTENTE_VALIDATION',
  )
  /** Le mode du livreur décide de ses onglets (D-89) : jamais un réglage
   *  manuel qu'il doit penser à changer. */
  const modeLivraison = computed(
    () => (profil.value?.mode_livraison as string | undefined) ?? 'EXPRESS',
  )

  function memoriser(identite: Identite) {
    utilisateur.value = identite.utilisateur
    profil.value = identite.profil
    client.poserJeton(identite.acces)
    localStorage.setItem(CLE, JSON.stringify({ acces: identite.acces }))
  }

  async function restaurer() {
    const brut = localStorage.getItem(CLE)
    if (!brut) return
    try {
      const { acces } = JSON.parse(brut)
      client.poserJeton(acces)
      const donnees = await client.get<{ utilisateur: Utilisateur; profil: never }>('/moi')
      utilisateur.value = donnees.utilisateur
      profil.value = donnees.profil
    } catch {
      deconnecter()
    }
  }

  async function connecter(email: string, motDePasse: string) {
    chargement.value = true
    erreur.value = ''
    try {
      memoriser(await client.post<Identite>('/auth/connexion', {
        email,
        mot_de_passe: motDePasse,
      }))
    } catch (echec) {
      erreur.value = echec instanceof Error ? echec.message : 'Connexion impossible.'
      throw echec
    } finally {
      chargement.value = false
    }
  }

  function deconnecter() {
    utilisateur.value = null
    profil.value = null
    client.poserJeton(null)
    localStorage.removeItem(CLE)
  }

  return {
    utilisateur, profil, chargement, erreur, client,
    estConnecte, role, enAttenteDeValidation, modeLivraison,
    connecter, deconnecter, restaurer,
  }
})
