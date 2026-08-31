<script setup lang="ts">
// L'enveloppe de tous les écrans mobiles : en-tête coloré, contenu qui défile.
//
// L'en-tête porte la couleur du rôle et rappelle qui on est — un livreur qui
// bascule entre Express et Standard doit le voir sans chercher.
import {
  IonContent, IonHeader, IonPage, IonRefresher, IonRefresherContent, IonTitle, IonToolbar,
} from '@ionic/vue'

defineProps<{
  titre: string
  sousTitre?: string
  /** Sans elle, pas de « tirer pour rafraîchir » : tous les écrans n'ont pas
   *  de données à recharger. */
  rafraichir?: () => Promise<unknown>
}>()
</script>

<template>
  <IonPage>
    <IonHeader class="ion-no-border">
      <IonToolbar class="entete">
        <div class="bloc">
          <span v-if="sousTitre" class="role">{{ sousTitre }}</span>
          <IonTitle class="titre">{{ titre }}</IonTitle>
        </div>
        <div slot="end" class="actions">
          <slot name="actions" />
        </div>
      </IonToolbar>
    </IonHeader>

    <IonContent :fullscreen="true" class="fond">
      <IonRefresher
        v-if="rafraichir"
        slot="fixed"
        @ion-refresh="(e) => rafraichir!().finally(() => e.target.complete())"
      >
        <IonRefresherContent pulling-text="Tirez pour actualiser" />
      </IonRefresher>

      <div class="corps">
        <slot />
      </div>
    </IonContent>
  </IonPage>
</template>

<style scoped>
.entete {
  --background: var(--accent, #16a34a);
  --color: #fff;
  padding-top: env(safe-area-inset-top);
}
.bloc {
  padding: 6px 16px 12px;
}
.role {
  display: block;
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.07em;
  opacity: 0.85;
}
.titre {
  padding: 0;
  font-size: 17px;
  font-weight: 700;
}
.actions {
  padding-right: 12px;
}
.fond {
  --background: var(--rd-atelier, #f4f5f8);
}
.corps {
  padding: 14px 14px 24px;
}
</style>
