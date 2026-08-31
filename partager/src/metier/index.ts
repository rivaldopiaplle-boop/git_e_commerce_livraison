// Les règles d'affichage communes aux deux fronts.
//
// Un statut ne doit pas s'appeler « Prête » au web et « Prêt » au mobile, et
// le vert du client ne doit pas être un vert différent d'un écran à l'autre.
// Ce sont des règles, pas de la présentation : elles vivent donc ici, et les
// deux interfaces les lisent.
import type { Role, StatutCommande, TypeService } from '../types'

/** Un montant en centimes, écrit comme on l'écrit en France.
 *
 *  Tous les montants du projet sont des ENTIERS EN CENTIMES : un flottant sur
 *  de l'argent finit toujours par produire un total à 0,01 près qui ne tombe
 *  pas juste.
 */
export function euros(centimes: number): string {
  return (centimes / 100).toLocaleString('fr-FR', { style: 'currency', currency: 'EUR' })
}

/** Une date courte, pour une liste. */
export function jour(date: string | null | undefined): string {
  return date ? new Date(date).toLocaleDateString('fr-FR') : '—'
}

/** Une date avec l'heure, pour un historique. */
export function jourEtHeure(date: string | null | undefined): string {
  return date
    ? new Date(date).toLocaleString('fr-FR', {
        day: '2-digit', month: '2-digit', year: '2-digit',
        hour: '2-digit', minute: '2-digit',
      })
    : '—'
}

/** « il y a deux heures » — ce qu'un vendeur veut lire sur une file d'attente.
 *
 *  Une heure absolue oblige à faire la soustraction de tête ; c'est justement
 *  ce qu'on ne fait pas quand on est pressé.
 */
export function depuis(date: string | null | undefined): string {
  if (!date) return '—'
  const minutes = Math.round((Date.now() - new Date(date).getTime()) / 60000)
  if (minutes < 1) return "à l'instant"
  if (minutes < 60) return `il y a ${minutes} min`
  const heures = Math.round(minutes / 60)
  if (heures < 24) return `il y a ${heures} h`
  const jours = Math.round(heures / 24)
  return jours === 1 ? 'hier' : `il y a ${jours} jours`
}

/** Une couleur dominante par rôle, et rien d'autre (règle d'or n°8).
 *
 *  Elles ne teintent que l'accent — barre active, boutons primaires, badges —
 *  jamais les couleurs de sens : un rouge d'erreur qui devient bleu chez
 *  l'admin n'est plus une erreur.
 */
export const COULEURS_ROLE: Record<Role | 'VISITEUR', { accent: string; doux: string }> = {
  VISITEUR: { accent: '#16a34a', doux: '#e8f8ee' },
  CLIENT: { accent: '#16a34a', doux: '#e8f8ee' },
  VENDEUR: { accent: '#2563eb', doux: '#eaf0ff' },
  GESTIONNAIRE: { accent: '#0d9488', doux: '#e6f7f4' },
  LIVREUR: { accent: '#7c3aed', doux: '#f3edff' },
  ADMIN: { accent: '#b91c1c', doux: '#fdebe9' },
}

/** Le vocabulaire de suivi, différent selon le circuit.
 *
 *  Le client d'un restaurant ne comprendrait pas « expédiée vers l'entrepôt » ;
 *  celui d'une boutique d'électronique ne comprendrait pas « prête à emporter ».
 */
export const ETAPES_SUIVI: Record<TypeService, StatutCommande[]> = {
  EXPRESS: ['PAYEE', 'EN_PREPARATION', 'PRETE', 'EN_LIVRAISON', 'LIVREE'],
  STANDARD: [
    'PAYEE', 'EN_PREPARATION', 'EXPEDIEE_ENTREPOT', 'RECUE_ENTREPOT',
    'EN_TOURNEE', 'LIVREE',
  ],
}

export const LIBELLES_STATUT: Record<StatutCommande, string> = {
  EN_ATTENTE_PAIEMENT: 'En attente de paiement',
  PAYEE: 'Payée',
  EN_PREPARATION: 'En préparation',
  PRETE: 'Prête',
  EXPEDIEE_ENTREPOT: "Vers l'entrepôt",
  RECUE_ENTREPOT: "À l'entrepôt",
  EN_TOURNEE: 'En tournée',
  EN_LIVRAISON: 'En livraison',
  LIVREE: 'Livrée',
  ANNULEE: 'Annulée',
  REMBOURSEE: 'Remboursée',
  ECHEC_LIVRAISON: 'Échec de livraison',
}

/** Où en est une commande sur sa frise, ou -1 si elle en est sortie
 *  (annulée, remboursée, échec). */
export function positionSuivi(service: TypeService, statut: StatutCommande): number {
  return ETAPES_SUIVI[service].indexOf(statut)
}

/** Le ton d'un statut, dans le vocabulaire partagé des deux fronts.
 *
 *  `succes`, `attente`, `cours`, `erreur`, `neutre` : chaque interface les
 *  traduit dans ses propres composants — un `Tag` PrimeVue au web, un
 *  `ion-chip` au mobile — mais la décision « ceci est une erreur » se prend
 *  une seule fois.
 */
export type Ton = 'succes' | 'attente' | 'cours' | 'erreur' | 'neutre'

export function tonDuStatut(statut: string): Ton {
  if (['LIVREE', 'PRETE', 'VALIDE', 'ACTIF', 'ACCEPTEE', 'RESOLU'].includes(statut)) {
    return 'succes'
  }
  if (['ANNULEE', 'ECHEC_LIVRAISON', 'ECHOUEE', 'REJETE', 'SUSPENDU', 'REFUSEE', 'OUVERT']
    .includes(statut)) {
    return 'erreur'
  }
  if (['EN_ATTENTE_PAIEMENT', 'A_PREPARER', 'EN_ATTENTE', 'A_FAIRE', 'BROUILLON']
    .includes(statut)) {
    return 'attente'
  }
  if (['EN_PREPARATION', 'EN_LIVRAISON', 'EN_TOURNEE', 'EN_ROUTE', 'EN_COURS']
    .includes(statut)) {
    return 'cours'
  }
  return 'neutre'
}

/** Le libellé d'une étape, adapté au métier du vendeur (D-81).
 *
 *  Le même statut technique se dit différemment selon qu'on tient un
 *  restaurant ou qu'on expédie des colis.
 */
export function actionSuivante(service: TypeService, statut: string): string {
  const express: Record<string, string> = {
    A_PREPARER: 'Commencer la préparation',
    EN_PREPARATION: 'Signaler prête',
    PRETE: 'Remettre au livreur',
  }
  const standard: Record<string, string> = {
    A_PREPARER: 'Préparer le colis',
    EN_PREPARATION: 'Colis prêt',
    PRETE: "Expédier vers l'entrepôt",
  }
  return (service === 'EXPRESS' ? express : standard)[statut] ?? 'Étape suivante'
}
