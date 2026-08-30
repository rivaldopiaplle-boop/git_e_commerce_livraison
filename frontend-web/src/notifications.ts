// L'équivalent de `react-hot-toast` du projet banque, posé sur le service
// Toast de PrimeVue.
//
// Avant lui, chaque écran gardait un `message` et une `erreur` dans son état,
// puis dessinait un bandeau quelque part — souvent hors de vue, parfois oublié
// après une action réussie. Un retour d'action doit être **le même partout** et
// se voir sans avoir à chercher.
import { useToast } from 'primevue/usetoast'

/** Le message d'une erreur d'API, ou un repli lisible. */
export function messageDErreur(echec: unknown, repli = "L'action a échoué.") {
  if (echec && typeof echec === 'object' && 'erreur' in echec) {
    const erreur = (echec as { erreur?: { message?: string } }).erreur
    if (erreur?.message) return erreur.message
  }
  return echec instanceof Error && echec.message ? echec.message : repli
}

export function useNotification() {
  const toast = useToast()

  return {
    /** Une action a abouti. Court : le détail est déjà à l'écran. */
    succes(detail: string, resume = 'C\u2019est fait') {
      toast.add({ severity: 'success', summary: resume, detail, life: 3500 })
    },

    /** Une action a été refusée. Plus long à l'écran : on doit pouvoir lire
     *  pourquoi, et ce qu'il faut faire ensuite. */
    echec(echecOuTexte: unknown, repli?: string) {
      toast.add({
        severity: 'error',
        summary: 'Action refusée',
        detail: typeof echecOuTexte === 'string'
          ? echecOuTexte
          : messageDErreur(echecOuTexte, repli),
        life: 7000,
      })
    },

    /** Une information qui n'attend rien de personne. */
    info(detail: string, resume = 'Information') {
      toast.add({ severity: 'info', summary: resume, detail, life: 4500 })
    },

    /** Ce qui mérite l'œil sans être une erreur : un stock qui descend, un
     *  dossier qui attend. */
    avertir(detail: string, resume = 'À surveiller') {
      toast.add({ severity: 'warn', summary: resume, detail, life: 5500 })
    },
  }
}
