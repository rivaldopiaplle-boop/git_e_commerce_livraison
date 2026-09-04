// Les appels des ecrans que la maquette prevoit, un par role.
//
// Regroupes ici plutot qu'eparpilles dans les vues : le jour ou un chemin
// change, un seul fichier bouge — et on lit d'un coup d'oeil quelle donnee
// chaque role a le droit de demander.
import { api } from './client'

export type Adresse = {
  id: number
  libelle: string
  rue: string
  complement: string
  ville: string
  code_postal: string
  pays: string
  instructions_livraison: string
  est_principale: boolean
}

export type MembrePersonnel = {
  id: number
  utilisateur: { id: number; email: string; nom: string; prenom: string; role: string }
  date_embauche: string | null
  // Ce que l'employe a REELLEMENT fait (D-80). Le vendeur avait un employe et
  // aucun moyen de savoir ce qu'il faisait de ses journees.
  commandes_preparees?: number
  ajustements_stock?: number
  derniere_action?: string | null
}

export type Statistiques = {
  commandes: number
  revenu_centimes: number
  commission_centimes: number
  taux_commission: number
  panier_moyen_centimes: number
  par_jour: { jour: string; commandes: number; montant_centimes: number }[]
  meilleurs_produits: { nom_produit_capture: string; quantite: number; montant_centimes: number }[]
  note_moyenne: number
  nombre_avis: number
  derniers_avis: { note: number; commentaire: string; date: string; statut: string }[]
}

export type Livraison = {
  id: number
  numero_commande: string
  type_service: string
  statut_livraison: string
  libelle_statut: string
  statut_commande: string
  client: string
  adresse: { id: number; libelle: string; rue: string; code_postal: string; ville: string
             instructions: string
             latitude?: number | null; longitude?: number | null } | null
  boutiques: string[]
  distance_km: string | null
  remuneration_livreur_centimes: number
  code_confirmation: string
  date_estimee: string | null
  date_reelle: string | null
  nombre_tentatives: number
}

export type Arret = {
  id: number
  ordre: number
  statut: string
  libelle_statut: string
  heure_estimee: string | null
  livraison: Livraison
}

export type Tournee = {
  id: number
  entrepot: string
  zone: string | null
  livreur: { id: number; nom: string; vehicule: string } | null
  statut: string
  libelle_statut: string
  nombre_arrets: number
  distance_totale_km: string | null
  date_creation: string
  date_debut: string | null
  date_fin: string | null
  arrets: Arret[]
}

export type Colis = {
  entrepot: { id: number; nom: string } | null
  groupes: {
    vendeur: string
    ville: string
    colis: { id: number; numero_commande: string; destination: string; articles: number
             date_expedition: string | null }[]
  }[]
  total: number
}

export type Litige = {
  id: number
  motif: string
  libelle_motif: string
  description: string
  statut: string
  libelle_statut: string
  resolution: string
  montant_rembourse_centimes: number
  date_ouverture: string
  date_resolution: string | null
  client: string
  commande: string
  id_commande: number
  montant_commande_centimes: number
  boutiques: string[]
  // L'instruction contradictoire (D-94) : la version du vendeur, son delai,
  // et le fait de savoir si le dossier peut etre tranche.
  reponse_vendeur: string
  date_reponse_vendeur: string | null
  date_limite_reponse: string | null
  delai_expire: boolean
  arbitrable: boolean
  pour: string
}

export type CompteAdmin = {
  id: number
  email: string
  nom: string
  prenom: string
  role: string
  statut_compte: string
  date_inscription: string
  rattachement: string
}

export type Trace = {
  id: number
  type_objet: string
  id_objet: number
  statut_avant: string
  statut_apres: string
  commentaire: string
  date: string
  par: string
}

export type Notification = {
  id: number
  titre: string
  contenu: string
  lien: string
  date: string
  lue: boolean
}

export const espaces = {
  client: {
    adresses: () => api.get<Adresse[]>('/moi/adresses'),
    ajouterAdresse: (donnees: Partial<Adresse>) => api.post<Adresse[]>('/moi/adresses', donnees),
    modifierAdresse: (id: number, donnees: Partial<Adresse>) =>
      api.patch<Adresse[]>(`/moi/adresses/${id}`, donnees),
    retirerAdresse: (id: number) => api.supprimer<Adresse[]>(`/moi/adresses/${id}`),
    litiges: () => api.get<Litige[]>('/mes-litiges'),
    ouvrirLitige: (commande: number, corps: { motif: string; description: string }) =>
      api.post<Litige>(`/commandes/${commande}/litiges`, corps),
  },

  vendeur: {
    personnel: () =>
      api.get<{ personnel: MembrePersonnel[]; acces: { libelle: string; autorise: boolean }[] }>(
        '/vendeurs/personnel',
      ),
    creerGestionnaire: (donnees: object) => api.post<never>('/vendeurs/gestionnaires', donnees),
    statistiques: () => api.get<Statistiques>('/vendeurs/statistiques'),
    avis: () => api.get<unknown[]>('/vendeurs/avis'),
    litiges: () => api.get<Litige[]>('/vendeurs/litiges'),
    repondreLitige: (id: number, reponse: string) =>
      api.post<Litige>(`/litiges/${id}/reponse`, { reponse }),
  },

  entrepot: {
    tableauDeBord: () => api.get<Record<string, number | string>>('/entrepots/tableau-de-bord'),
    colis: () => api.get<Colis>('/entrepots/colis'),
    tournees: () =>
      api.get<{ tournees: Tournee[]; a_affecter: number; en_attente: number }>(
        '/entrepots/tournees',
      ),
  },

  livreur: {
    tableauDeBord: () => api.get<Record<string, number | string>>('/livreurs/tableau-de-bord'),
    mesCourses: () =>
      api.get<{
        mode: string
        disponibilite: string
        en_cours: Livraison[]
        terminees: Livraison[]
        tournee: Tournee | null
        gains: { courses_terminees: number; total_centimes: number; distance_km: number }
      }>('/livreurs/mes-courses'),
  },

  admin: {
    utilisateurs: (filtres: Record<string, string> = {}) => {
      const parametres = new URLSearchParams(
        Object.entries(filtres).filter(([, valeur]) => valeur),
      )
      const suffixe = parametres.toString() ? `?${parametres}` : ''
      return api.get<{
        utilisateurs: CompteAdmin[]
        repartition: { role: string; nombre: number }[]
        total: number
      }>(`/admin/utilisateurs${suffixe}`)
    },
    /** Suspendre ou reactiver un compte. Suspendre exige un motif : la
     *  personne doit savoir ce qu'on lui reproche (D-93). */
    basculerCompte: (id: number, motif = '') =>
      api.post<{ id: number; statut_compte: string }>(`/admin/comptes/${id}/basculer`, { motif }),

    /** Les cinq decisions possibles sur une boutique, en une seule route :
     *  valider, refuser, suspendre, reactiver, revalider. */
    deciderVendeur: (id: number, decision: string, motif = '') =>
      api.post<Record<string, unknown>>(`/admin/vendeurs/${id}/decision`, { decision, motif }),
    deciderLivreur: (id: number, decision: string, motif = '', idEntrepot?: number) =>
      api.post<Record<string, unknown>>(`/admin/livreurs/${id}/decision`, {
        decision, motif, id_entrepot: idEntrepot,
      }),
    validations: () =>
      api.get<{ vendeurs: Record<string, unknown>[]; livreurs: Record<string, unknown>[] }>(
        '/admin/validations',
      ),
    boutiques: () => api.get<Record<string, unknown>[]>('/admin/boutiques'),
    livreurs: () => api.get<Record<string, unknown>[]>('/admin/livreurs'),
    litiges: () =>
      api.get<{
        litiges: Litige[]
        ouverts: number
        en_cours: number
        resolus: number
        // Ce qui attend vraiment une decision : le vendeur a parle, ou son
        // delai est passe. Le reste attend encore la seconde version.
        a_arbitrer: number
      }>('/admin/litiges'),
    arbitrer: (id: number, corps: { decision: string; motivation: string;
                                    montant_centimes?: number }) =>
      api.post<Litige>(`/admin/litiges/${id}/arbitrer`, corps),
    journal: () => api.get<Trace[]>('/admin/journal'),
  },

  notifications: {
    lire: () =>
      api.get<{ notifications: Notification[]; non_lues: number }>('/moi/notifications'),
    marquerLues: () => api.post<{ non_lues: number }>('/moi/notifications/lues'),
  },
}

// ── Profil et paramètres (D-76, D-77) ─────────────────────────────────────

export type ChampDemande = {
  champ: string
  libelle: string
  valeur_actuelle: string
  valeur_demandee: string
}

export type Demande = {
  id: number
  statut: string
  libelle_statut: string
  motif: string
  commentaire_decision: string
  date_demande: string
  date_decision: string | null
  demandeur: { id: number; nom: string; email: string; role: string }
  champs: ChampDemande[]
}

export type Profil = {
  identite: {
    nom: string
    prenom: string
    role: string
    libelle_role: string
    statut_compte: string
    date_inscription: string
  }
  coordonnees: { email: string; telephone: string }
  champs_geles: { champ: string; libelle: string }[]
  demandes: Demande[]
  demandes_en_attente: number
}

export type Parametres = {
  notifications_email: boolean
  notifications_push: boolean
  courriels_promotionnels: boolean
  densite: 'COMPACTE' | 'NORMALE'
  masquer_montants: boolean
  canal_in_app_toujours_actif: boolean
}

export const profil = {
  lire: () => api.get<Profil>('/moi/profil'),
  modifierCoordonnees: (donnees: { email?: string; telephone?: string }) =>
    api.patch<Profil>('/moi/profil', donnees),
  demanderModification: (champs: Record<string, string>, motif: string) =>
    api.post<Demande>('/moi/demandes-modification', { champs, motif }),
  changerMotDePasse: (ancien: string, nouveau: string) =>
    api.post<{ change: boolean }>('/moi/mot-de-passe', { ancien, nouveau }),

  parametres: () => api.get<Parametres>('/moi/parametres'),
  modifierParametres: (donnees: Partial<Parametres>) =>
    api.patch<Parametres>('/moi/parametres', donnees),

  // Côté administration
  demandesAArbitrer: () =>
    api.get<{ demandes: Demande[]; en_attente: number }>('/admin/demandes-modification'),
  arbitrer: (id: number, accepter: boolean, commentaire: string) =>
    api.post<Demande>(`/admin/demandes-modification/${id}`, { accepter, commentaire }),
}
