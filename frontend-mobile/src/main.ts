import { IonicVue } from '@ionic/vue'
import { createPinia } from 'pinia'
import { createApp } from 'vue'

import App from './App.vue'
import { routeur } from './routeur'
import { useSession } from './magasins/session'

/* Le socle d'Ionic : sans ces feuilles, les composants existent mais ne
   ressemblent à rien. */
import '@ionic/vue/css/core.css'
import '@ionic/vue/css/normalize.css'
import '@ionic/vue/css/structure.css'
import '@ionic/vue/css/typography.css'
import '@ionic/vue/css/padding.css'
import '@ionic/vue/css/flex-utils.css'
import './theme.css'

const application = createApp(App)
  .use(createPinia())
  .use(IonicVue, {
    // Le même rendu sur les deux plateformes : on démontre une application,
    // pas deux. `md` (Material) est le plus proche de la maquette web.
    mode: 'md',
  })

// On restaure la session AVANT de brancher le routeur : sinon le garde
// s'exécute sur un état vide et renvoie vers la connexion un livreur déjà
// connecté, le temps d'un clignotement.
const session = useSession()
session.restaurer().finally(() => {
  application.use(routeur)
  routeur.isReady().then(() => application.mount('#app'))
})
