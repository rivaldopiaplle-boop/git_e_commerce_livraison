<script setup lang="ts">
// La coquille mobile : cinq onglets en bas, le « + » au milieu.
//
// C'est la structure imposée par la règle d'or n°10, et elle diffère
// volontairement du web : *« ce qui change, c'est la disposition »*. Tout le
// reste — symboles, couleurs de rôle, vocabulaire — vient du même endroit que
// le web, `@partage`.
import {
  IonApp, IonIcon, IonLabel, IonRouterOutlet, IonTabBar, IonTabButton, IonTabs,
} from '@ionic/vue'
import { COULEURS_ROLE } from '@partage/metier'
import { addOutline, closeOutline } from 'ionicons/icons'
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { actionsDepliees, ongletsDuRole } from '@/onglets'
import { useSession } from '@/magasins/session'

const session = useSession()
const route = useRoute()
const routeur = useRouter()

const feuilleOuverte = ref(false)

const onglets = computed(() => ongletsDuRole(session.role, session.modeLivraison))
const actions = computed(() => actionsDepliees(session.role))

// La couleur du rôle, posée sur la racine : les composants Ionic la lisent
// sans rien savoir du rôle connecté (règle d'or n°8).
const couleurs = computed(() => COULEURS_ROLE[session.role ?? 'VISITEUR'])

const surEcranDeConnexion = computed(() => route.name === 'connexion')

function ouvrir(action: { route: string }) {
  feuilleOuverte.value = false
  routeur.push(action.route)
}
</script>

<template>
  <IonApp :style="{ '--accent': couleurs.accent, '--accent-doux': couleurs.doux }">
    <!-- L'écran de connexion n'a pas d'onglets : il n'y a rien à naviguer
         tant qu'on n'est pas entré. -->
    <IonRouterOutlet v-if="surEcranDeConnexion" />

    <IonTabs v-else>
      <IonRouterOutlet />

      <IonTabBar slot="bottom">
        <IonTabButton
          v-for="onglet in onglets"
          :key="onglet.cle"
          :tab="onglet.cle"
          :href="onglet.estLePlus ? undefined : onglet.route"
          :class="onglet.estLePlus ? 'onglet-plus' : ''"
          @click="onglet.estLePlus && (feuilleOuverte = !feuilleOuverte)"
        >
          <!-- Le troisième emplacement, en relief : il ne navigue pas, il
               déplie. C'est la règle d'or n°10, à la lettre. -->
          <span v-if="onglet.estLePlus" class="pastille-plus">
            <IonIcon :icon="feuilleOuverte ? closeOutline : addOutline" size="small" />
          </span>
          <template v-else>
            <IonIcon :icon="onglet.icone" />
            <IonLabel>{{ onglet.libelle }}</IonLabel>
          </template>
        </IonTabButton>
      </IonTabBar>
    </IonTabs>

    <!-- La feuille du « + » : les fonctions de priorité moyenne, cachées les
         unes derrière les autres pour garder une interface dense. -->
    <Transition name="feuille">
      <div v-if="feuilleOuverte" class="voile" @click="feuilleOuverte = false">
        <div class="feuille" @click.stop>
          <span class="poignee" />
          <button
            v-for="action in actions"
            :key="action.libelle"
            type="button"
            class="option"
            @click="ouvrir(action)"
          >
            <span class="icone"><IonIcon :icon="action.icone" /></span>
            <span class="texte">
              <b>{{ action.libelle }}</b>
              <span>{{ action.aide }}</span>
            </span>
          </button>
        </div>
      </div>
    </Transition>
  </IonApp>
</template>

<style scoped>
.voile {
  position: fixed;
  inset: 0;
  z-index: 30;
  background: rgba(10, 12, 18, 0.32);
  display: flex;
  align-items: flex-end;
}
.feuille {
  width: 100%;
  background: #fff;
  border-radius: 20px 20px 0 0;
  padding: 14px 16px calc(20px + 58px + env(safe-area-inset-bottom));
  box-shadow: 0 -8px 24px rgba(0, 0, 0, 0.15);
}
.poignee {
  display: block;
  width: 40px;
  height: 4px;
  margin: 0 auto 14px;
  border-radius: 99px;
  background: var(--rd-trait);
}
.option {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
  padding: 11px 4px;
  border: none;
  background: none;
  text-align: left;
  border-bottom: 1px solid var(--rd-trait-doux);
}
.option:last-child {
  border-bottom: none;
}
.option .icone {
  width: 34px;
  height: 34px;
  border-radius: 10px;
  display: grid;
  place-items: center;
  background: var(--accent-doux);
  color: var(--accent);
  flex-shrink: 0;
}
.option .texte b {
  display: block;
  font-size: 12.8px;
}
.option .texte span {
  font-size: 11px;
  color: var(--rd-encre-douce);
}

.feuille-enter-active,
.feuille-leave-active {
  transition: opacity 0.2s ease;
}
.feuille-enter-active .feuille,
.feuille-leave-active .feuille {
  transition: transform 0.22s ease;
}
.feuille-enter-from,
.feuille-leave-to {
  opacity: 0;
}
.feuille-enter-from .feuille,
.feuille-leave-to .feuille {
  transform: translateY(100%);
}
</style>
