<script setup lang="ts">
// Le profil mobile : dense, tout imbriqué sous une seule entrée.
//
// C'est la règle d'or n°10 appliquée — *« toutes les fonctionnalités doivent
// être cachées les unes derrière les autres, pour rendre l'interface dense »*.
// Adresses, sécurité et notifications vivent donc ici, pas en onglets séparés
// qui gaspilleraient un emplacement du bas.
//
// **Ce qui a été corrigé au bloc N-6** : le commutateur « Notifications
// poussées » était un `:checked="true"` sans gestionnaire. Il ne lisait rien,
// n'enregistrait rien, et donnait à croire qu'on avait réglé quelque chose.
// C'est le pire genre de bouton : celui qui a l'air de marcher. Il parle
// maintenant à `/moi/parametres`, comme le web. Dans la foulée, la liste des
// notifications et le changement de mot de passe — présents sur le web,
// absents ici alors que le téléphone est justement l'appareil qui reçoit les
// notifications.
import {
  IonBadge, IonButton, IonIcon, IonInput, IonItem, IonLabel, IonList, IonModal,
  IonNote, IonSpinner, IonToggle,
} from '@ionic/vue'
import { EchecApi } from '@partage/api'
import {
  chevronForward, keyOutline, locationOutline, logOutOutline, notificationsOutline,
  shieldOutline,
} from 'ionicons/icons'
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'

import Ecran from '@/composants/Ecran.vue'
import { useSession } from '@/magasins/session'
import { useRafraichissement } from '@/rafraichissement'

type Notification = {
  id: number
  titre: string
  contenu: string
  lien: string
  date: string
  lue: boolean
}

type Parametres = {
  notifications_email: boolean
  notifications_push: boolean
  courriels_promotionnels: boolean
  canal_in_app_toujours_actif: boolean
}

const session = useSession()
const routeur = useRouter()

const initiales = computed(() => {
  const u = session.utilisateur
  return u ? `${u.prenom.charAt(0)}${u.nom.charAt(0)}`.toUpperCase() : '?'
})

function message(souci: unknown, defaut: string) {
  return souci instanceof EchecApi ? souci.erreur.message : defaut
}

// ── Les préférences ───────────────────────────────────────────────────────
const parametres = ref<Parametres | null>(null)

async function charger() {
  try {
    parametres.value = await session.client.get<Parametres>('/moi/parametres')
    const boite = await session.client.get<{ notifications: Notification[]; non_lues: number }>(
      '/moi/notifications',
    )
    notifications.value = boite.notifications
    nonLues.value = boite.non_lues
  } catch {
    // Un profil doit rester lisible même si les préférences ne répondent pas :
    // se déconnecter est justement ce qu'on vient y faire quand rien ne marche.
  }
}

useRafraichissement(charger)

/**
 * Enregistrer tout de suite, et remettre le commutateur en place si ça rate.
 *
 * Pas de bouton « Enregistrer » : sur un téléphone, un réglage qu'il faut
 * confirmer est un réglage qu'on croit avoir changé.
 */
async function basculer(champ: keyof Parametres, valeur: boolean) {
  if (!parametres.value) return
  const avant = parametres.value[champ]
  parametres.value = { ...parametres.value, [champ]: valeur }
  try {
    parametres.value = await session.client.patch<Parametres>(
      '/moi/parametres', { [champ]: valeur },
    )
  } catch (souci) {
    parametres.value = { ...parametres.value, [champ]: avant }
    erreur.value = message(souci, "Le réglage n'a pas été enregistré.")
  }
}

// ── La boîte de notifications ─────────────────────────────────────────────
const notifications = ref<Notification[]>([])
const nonLues = ref(0)
const boiteOuverte = ref(false)

async function ouvrirBoite() {
  boiteOuverte.value = true
  if (!nonLues.value) return
  try {
    await session.client.post('/moi/notifications/lues', {})
    notifications.value = notifications.value.map((n) => ({ ...n, lue: true }))
    nonLues.value = 0
  } catch {
    // Les marquer lues est un confort : si ça échoue, la liste reste juste.
  }
}

function suivre(notification: Notification) {
  boiteOuverte.value = false
  // Les liens du serveur visent le web (`/espace/...`). Sur le téléphone, on
  // renvoie vers l'écran équivalent quand il existe, sinon on reste ici.
  if (notification.lien.includes('commande')) routeur.push('/commandes')
  else if (notification.lien.includes('course') || notification.lien.includes('tournee')) {
    routeur.push(session.utilisateur?.role === 'LIVREUR' ? '/courses' : '/commandes')
  }
}

// ── Le mot de passe ───────────────────────────────────────────────────────
const mdpOuvert = ref(false)
const ancien = ref('')
const nouveau = ref('')
const confirmation = ref('')
const occupe = ref(false)
const erreur = ref('')
const succes = ref('')

const mdpValide = computed(() =>
  ancien.value.length >= 8 && nouveau.value.length >= 8 && nouveau.value === confirmation.value,
)

function ouvrirMotDePasse() {
  mdpOuvert.value = true
  ancien.value = ''
  nouveau.value = ''
  confirmation.value = ''
  erreur.value = ''
}

async function changerMotDePasse() {
  occupe.value = true
  erreur.value = ''
  try {
    await session.client.post('/moi/mot-de-passe', {
      ancien: ancien.value, nouveau: nouveau.value,
    })
    mdpOuvert.value = false
    succes.value = 'Votre mot de passe est changé.'
  } catch (souci) {
    erreur.value = message(souci, "Le mot de passe n'a pas été changé.")
  } finally {
    occupe.value = false
  }
}

function partir() {
  session.deconnecter()
  routeur.replace('/connexion')
}
</script>

<template>
  <Ecran titre="Profil" :sous-titre="session.utilisateur?.role.toLowerCase()"
         :rafraichir="charger">
    <div class="carte-mobile identite">
      <span class="avatar">{{ initiales }}</span>
      <span>
        <b>{{ session.utilisateur?.prenom }} {{ session.utilisateur?.nom }}</b>
        <span class="sous-titre">{{ session.utilisateur?.email }}</span>
      </span>
    </div>

    <p v-if="succes" class="succes">{{ succes }}</p>
    <p v-if="erreur" class="erreur">{{ erreur }}</p>

    <IonList inset>
      <IonItem button :detail="false" @click="routeur.push('/adresses')">
        <IonIcon slot="start" :icon="locationOutline" />
        <IonLabel>
          Mes adresses
          <IonNote>Elles décident des boutiques Express visibles</IonNote>
        </IonLabel>
        <IonIcon slot="end" :icon="chevronForward" />
      </IonItem>

      <IonItem button :detail="false" @click="ouvrirBoite">
        <IonIcon slot="start" :icon="notificationsOutline" />
        <IonLabel>
          Mes notifications
          <IonNote>Statut de commande, courses, litiges</IonNote>
        </IonLabel>
        <IonBadge v-if="nonLues" slot="end" color="danger">{{ nonLues }}</IonBadge>
        <IonIcon v-else slot="end" :icon="chevronForward" />
      </IonItem>

      <IonItem>
        <IonIcon slot="start" :icon="notificationsOutline" />
        <IonLabel>
          Notifications poussées
          <IonNote>Statut de commande, courses disponibles</IonNote>
        </IonLabel>
        <IonSpinner v-if="!parametres" slot="end" name="dots" />
        <IonToggle
          v-else
          slot="end"
          :checked="parametres.notifications_push"
          @ion-change="basculer('notifications_push', $event.detail.checked)"
        />
      </IonItem>

      <IonItem v-if="parametres">
        <IonIcon slot="start" :icon="notificationsOutline" />
        <IonLabel>
          Courriels de suivi
          <IonNote>Confirmations de commande et de livraison</IonNote>
        </IonLabel>
        <IonToggle
          slot="end"
          :checked="parametres.notifications_email"
          @ion-change="basculer('notifications_email', $event.detail.checked)"
        />
      </IonItem>

      <IonItem button :detail="false" @click="ouvrirMotDePasse">
        <IonIcon slot="start" :icon="keyOutline" />
        <IonLabel>
          Changer mon mot de passe
          <IonNote>L'ancien vous sera demandé</IonNote>
        </IonLabel>
        <IonIcon slot="end" :icon="chevronForward" />
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
      Les notifications dans l'application ne se coupent pas : une information
      critique n'a jamais un canal unique. Les deux réglages ci-dessus portent sur
      ce qui vous est envoyé en plus, sur le téléphone et par courriel.
    </p>

    <p class="note">
      Votre identité — nom, prénom, date de naissance — ne se modifie que depuis
      l'application web, par une demande validée. Sur une place de marché, l'identité
      engage.
    </p>

    <IonButton expand="block" fill="outline" color="danger" @click="partir">
      <IonIcon slot="start" :icon="logOutOutline" />
      Se déconnecter
    </IonButton>

    <!-- La boîte : ouvrir la liste vaut lecture, comme la cloche du web -->
    <IonModal :is-open="boiteOuverte" @did-dismiss="boiteOuverte = false">
      <div class="feuille">
        <b class="titre">Mes notifications</b>
        <div v-for="notification in notifications" :key="notification.id"
             class="carte-mobile avis-ligne" @click="suivre(notification)">
          <b>{{ notification.titre }}</b>
          <span class="sous-titre">{{ notification.contenu }}</span>
        </div>
        <p v-if="!notifications.length" class="note">
          Rien pour l'instant. Les changements de statut de vos commandes
          apparaîtront ici.
        </p>
        <IonButton expand="block" fill="outline" @click="boiteOuverte = false">
          Fermer
        </IonButton>
      </div>
    </IonModal>

    <!-- Le mot de passe : l'ancien est exigé, une session ouverte ne suffit pas -->
    <IonModal :is-open="mdpOuvert" @did-dismiss="mdpOuvert = false">
      <div class="feuille">
        <b class="titre">Changer mon mot de passe</b>
        <IonInput v-model="ancien" type="password" fill="outline"
                  label="Mot de passe actuel" label-placement="floating" />
        <IonInput v-model="nouveau" type="password" fill="outline"
                  label="Nouveau mot de passe" label-placement="floating" />
        <IonInput v-model="confirmation" type="password" fill="outline"
                  label="Confirmer" label-placement="floating" />
        <span v-if="nouveau && confirmation && nouveau !== confirmation" class="note">
          Les deux saisies diffèrent.
        </span>
        <p v-if="erreur" class="erreur">{{ erreur }}</p>
        <div class="boutons">
          <IonButton fill="outline" @click="mdpOuvert = false">Annuler</IonButton>
          <IonButton :disabled="occupe || !mdpValide" @click="changerMotDePasse">
            Changer
          </IonButton>
        </div>
      </div>
    </IonModal>
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
.feuille {
  padding: 20px 16px calc(20px + var(--rd-marge-basse, 12px));
  display: flex;
  flex-direction: column;
  gap: 12px;
  overflow-y: auto;
}
.feuille .titre {
  font-size: 17px;
}
.avis-ligne b {
  display: block;
  font-size: 13px;
  margin-bottom: 3px;
}
.boutons {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}
.erreur,
.succes {
  font-size: 11.5px;
  line-height: 1.6;
  border-radius: 10px;
  padding: 10px 12px;
}
.erreur {
  color: #9c2116;
  background: #fbe4e2;
}
.succes {
  color: #116b34;
  background: #e2f7ea;
  text-align: center;
}
</style>
