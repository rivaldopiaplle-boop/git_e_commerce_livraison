// Ce que le livreur voit et fait, du côté mobile.
//
// C'est ici que le mobile va **plus loin que le web** : au web, l'espace
// livreur est en lecture (D-40) — accepter une course, confirmer une remise et
// signaler une absence se font une main sur le guidon, avec la position et
// l'appareil photo. Ces trois actions n'existent donc que dans ce magasin.
import type { Livraison, Tournee } from '@partage/types'
import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

import { useSession } from './session'

export type Gains = {
  courses_terminees: number
  total_centimes: number
  distance_km: number
  bloque_centimes?: number
}

export const useLivreur = defineStore('livreur', () => {
  const session = useSession()

  const enCours = ref<Livraison[]>([])
  const terminees = ref<Livraison[]>([])
  const disponibles = ref<Livraison[]>([])
  /** Pourquoi il n'y a rien à prendre : `course_en_cours`, `hors_ligne`,
   *  `mauvais_mode`, `hors_rayon`, `aucune`. Vide quand la liste est pleine. */
  const raisonVide = ref('')
  const rayonKm = ref(8)
  const tournee = ref<Tournee | null>(null)
  const gains = ref<Gains>({ courses_terminees: 0, total_centimes: 0, distance_km: 0 })
  const disponibilite = ref('HORS_LIGNE')
  const chargement = ref(false)
  const erreur = ref('')

  /** La course du moment. En Express il n'y en a qu'une : c'est une contrainte
   *  du métier, pas une limite d'affichage. */
  const courseActuelle = computed(() => enCours.value[0] ?? null)

  /** Le prochain arrêt d'une tournée : le premier qui reste à faire.
   *
   *  Un livreur n'a pas besoin de rouvrir sa tournée entière dix fois par jour
   *  pour savoir où il va maintenant (D-90). */
  /**
   * L'arrêt suivant : ce qui reste à faire, puis ce qui a été reporté.
   *
   * Un arrêt reporté — personne à l'adresse à la première tentative — repart
   * en fin de tournée (O-5). Sans cette seconde recherche, le livreur ne
   * repasserait jamais, et le colis partirait en retour sans deuxième chance.
   */
  const prochainArret = computed(() => {
    const arrets = tournee.value?.arrets ?? []
    return arrets.find((arret) => arret.statut === 'A_FAIRE')
      ?? arrets.find((arret) => arret.statut === 'REPORTE')
      ?? null
  })

  async function charger() {
    if (!session.estConnecte) return
    chargement.value = true
    erreur.value = ''
    try {
      const donnees = await session.client.get<{
        mode: string
        disponibilite: string
        en_cours: Livraison[]
        terminees: Livraison[]
        tournee: Tournee | null
        gains: Gains
      }>('/livreurs/mes-courses')
      enCours.value = donnees.en_cours
      terminees.value = donnees.terminees
      tournee.value = donnees.tournee
      gains.value = donnees.gains
      disponibilite.value = donnees.disponibilite
    } catch (echec) {
      erreur.value = echec instanceof Error ? echec.message : 'Chargement impossible.'
    } finally {
      chargement.value = false
    }
  }

  async function chargerDisponibles() {
    if (!session.estConnecte) return
    try {
      const reponse = await session.client.get<{
        livraisons: Livraison[]
        raison: string
        rayon_km: number
      }>('/livreurs/disponibles')
      disponibles.value = reponse.livraisons
      // POURQUOI la liste est vide. L'écran l'inventait : il proposait deux
      // explications au livreur en le laissant deviner laquelle était vraie
      // (O-5). Le serveur le sait, il le dit.
      raisonVide.value = reponse.raison
      rayonKm.value = reponse.rayon_km
    } catch {
      // Une liste vide vaut mieux qu'un écran en erreur : le livreur verra
      // l'état vide rédigé, qui lui dit quoi faire.
      disponibles.value = []
    }
  }

  async function basculerDisponibilite() {
    const cible = disponibilite.value === 'DISPONIBLE' ? 'HORS_LIGNE' : 'DISPONIBLE'
    const resultat = await session.client.post<{ statut_disponibilite: string }>(
      '/livreurs/disponibilite',
      { statut: cible },
    )
    disponibilite.value = resultat.statut_disponibilite
  }

  async function accepter(idLivraison: number) {
    await session.client.post(`/livreurs/livraisons/${idLivraison}/accepter`)
    await Promise.all([charger(), chargerDisponibles()])
  }

  /** Confirmer qu'on a le colis en main, et partir.
   *
   *  Cette étape existe parce que « en route » et « attribuée » ne sont pas la
   *  même chose pour le client : entre les deux, il attend que le restaurant
   *  finisse, pas que le livreur roule.
   */
  async function recupererColis(idLivraison: number) {
    await session.client.post(`/livreurs/livraisons/${idLivraison}/recuperer`)
    await charger()
  }

  /** Confirmer une remise avec le code donné par le client.
   *
   *  Le code est la preuve que le bon colis est arrivé à la bonne personne,
   *  sans photo ni signature — c'est ce que le modèle prévoit depuis le début
   *  (`code_confirmation`).
   */
  async function confirmerRemise(idLivraison: number, code: string, position?: {
    lat: number; lon: number
  }) {
    await session.client.post(`/livreurs/livraisons/${idLivraison}/livrer`, {
      code,
      position_lat: position?.lat,
      position_lon: position?.lon,
    })
    await charger()
  }

  /** Signaler une absence. Deux tentatives gratuites, puis retour (D-23). */
  async function signalerAbsence(idLivraison: number, commentaire: string) {
    // Le retour porte le NUMERO de tentative : l'écran doit pouvoir dire
    // lequel des deux cas s'est produit — on repasse, ou le colis repart (O-5).
    const retour = await session.client.post<{ tentative: number }>(
      `/livreurs/livraisons/${idLivraison}/absence`, { commentaire },
    )
    await charger()
    return retour
  }

  return {
    enCours, terminees, disponibles, tournee, gains, disponibilite, chargement, erreur,
    raisonVide, rayonKm,
    courseActuelle, prochainArret,
    charger, chargerDisponibles, basculerDisponibilite, accepter,
    recupererColis, confirmerRemise, signalerAbsence,
  }
})
