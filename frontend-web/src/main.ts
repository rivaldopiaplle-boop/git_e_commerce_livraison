import { VueQueryPlugin } from '@tanstack/vue-query'
import { createPinia } from 'pinia'
import PrimeVue from 'primevue/config'
import ConfirmationService from 'primevue/confirmationservice'
import ToastService from 'primevue/toastservice'
import { createApp } from 'vue'

import App from './App.vue'
import { routeur } from './routeur'
import { useAuthentification } from './stores/authentification'
import { usePanier } from './stores/panier'
import { usePosition } from './stores/position'
import { optionsPrimeVue } from './theme'
import './style.css'

const application = createApp(App)
application.use(createPinia())

// ── La stack, alignee sur celle du projet banque (regles d'or n°5 et n°12) ──
//
// Le projet banque repose sur MUI, TanStack Query, react-hot-toast et
// react-hook-form + zod. Les equivalents Vue sont branches ici :
//
//   MUI                  -> PrimeVue          (deja impose par D-26)
//   @tanstack/react-query-> @tanstack/vue-query (meme API)
//   react-hot-toast      -> le service Toast de PrimeVue
//   react-hook-form+zod  -> vee-validate + zod
//   react-router-dom     -> vue-router
//
// J'avais laisse PrimeVue installe mais NON enregistre, en arguant du poids
// de son theme. C'etait une decision prise contre D-26, qui l'impose
// justement « pour ne pas redessiner a la main les tableaux, fenetres,
// tiroirs et notifications que la regle d'or n°6 impose ». Redessiner les
// quatre a la main a coute plus cher que le theme, et le resultat ne
// ressemblait a rien de connu.
application.use(PrimeVue, optionsPrimeVue)
application.use(ToastService)
application.use(ConfirmationService)

// Le cache de requetes : plus de `onMounted` + `ref` + `try/finally` recopies
// dans chaque ecran. Memes reglages que le projet banque — on ne rejoue pas
// une requete a chaque retour d'onglet, et une erreur reseau se retente une
// fois avant d'etre montree.
application.use(VueQueryPlugin, {
  queryClientConfig: {
    defaultOptions: {
      queries: {
        retry: 1,
        refetchOnWindowFocus: false,
        staleTime: 30_000,
      },
    },
  },
})

// Une erreur de rendu non rattrapee laisse l'application muette : les clics
// ne font plus rien et rien ne l'explique. On la rend au moins visible dans
// la console, avec le nom du composant fautif.
application.config.errorHandler = (erreur, _instance, information) => {
  console.error('[RivDinde] erreur de rendu —', information, erreur)
}

usePosition().restaurer()
usePanier().demarrer()

// On restaure la session AVANT de brancher le routeur : sinon le garde
// s'execute sur un etat vide et renvoie un utilisateur deja connecte vers
// l'ecran de connexion, le temps d'un clignotement.
const session = useAuthentification()
session.restaurer().finally(() => {
  application.use(routeur)
  application.mount('#app')
})
