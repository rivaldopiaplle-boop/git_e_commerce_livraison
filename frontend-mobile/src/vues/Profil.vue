<script setup lang="ts">
// Le profil mobile : dense, tout imbriqué sous une seule entrée.
//
// C'est la règle d'or n°10 appliquée — *« toutes les fonctionnalités doivent
// être cachées les unes derrière les autres, pour rendre l'interface dense »*.
// Adresses, sécurité et notifications vivent donc ici, pas en onglets séparés
// qui gaspilleraient un emplacement du bas.
import { IonButton, IonIcon, IonItem, IonLabel, IonList, IonNote, IonToggle } from '@ionic/vue'
import {
  chevronForward, locationOutline, logOutOutline, notificationsOutline, shieldOutline,
} from 'ionicons/icons'
import { computed } from 'vue'
import { useRouter } from 'vue-router'

import Ecran from '@/composants/Ecran.vue'
import { useSession } from '@/magasins/session'

const session = useSession()
const routeur = useRouter()

const initiales = computed(() => {
  const u = session.utilisateur
  return u ? `${u.prenom.charAt(0)}${u.nom.charAt(0)}`.toUpperCase() : '?'
})

function partir() {
  session.deconnecter()
  routeur.replace('/connexion')
}
</script>

<template>
  <Ecran titre="Profil" :sous-titre="session.utilisateur?.role.toLowerCase()">
    <div class="carte-mobile identite">
      <span class="avatar">{{ initiales }}</span>
      <span>
        <b>{{ session.utilisateur?.prenom }} {{ session.utilisateur?.nom }}</b>
        <span class="sous-titre">{{ session.utilisateur?.email }}</span>
      </span>
    </div>

    <IonList inset>
      <IonItem button :detail="false" @click="routeur.push('/adresses')">
        <IonIcon slot="start" :icon="locationOutline" />
        <IonLabel>
          Mes adresses
          <IonNote>Elles décident des boutiques Express visibles</IonNote>
        </IonLabel>
        <IonIcon slot="end" :icon="chevronForward" />
      </IonItem>

      <IonItem>
        <IonIcon slot="start" :icon="notificationsOutline" />
        <IonLabel>
          Notifications poussées
          <IonNote>Statut de commande, courses disponibles</IonNote>
        </IonLabel>
        <IonToggle :checked="true" />
      </IonItem>

      <IonItem button :detail="false" @click="routeur.push('/aide')">
        <IonIcon slot="start" :icon="shieldOutline" />
        <IonLabel>
          Aide et support
          <IonNote>Signaler un problème sur une livraison</IonNote>
        </IonLabel>
        <IonIcon slot="end" :icon="chevronForward" />
      </IonItem>
    </IonList>

    <p class="note">
      Votre identité — nom, prénom, date de naissance — ne se modifie que depuis
      l'application web, par une demande validée. Sur une place de marché, l'identité
      engage.
    </p>

    <IonButton expand="block" fill="outline" color="danger" @click="partir">
      <IonIcon slot="start" :icon="logOutOutline" />
      Se déconnecter
    </IonButton>
  </Ecran>
</template>

<style scoped>
.identite {
  display: flex;
  align-items: center;
  gap: 14px;
}
.avatar {
  width: 50px;
  height: 50px;
  border-radius: 50%;
  background: var(--accent);
  color: #fff;
  display: grid;
  place-items: center;
  font-size: 18px;
  font-weight: 800;
  flex-shrink: 0;
}
.identite b {
  display: block;
  font-size: 15px;
}
.note {
  font-size: 11px;
  line-height: 1.6;
  color: var(--rd-encre-douce);
  padding: 0 4px;
}
</style>
