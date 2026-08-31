<script setup lang="ts">
// L'aide, et surtout : signaler un problème sur une livraison précise.
//
// Un formulaire générique où il faut ressaisir le numéro de commande n'est
// jamais rempli. Le signalement part donc **depuis** l'historique, avec la
// livraison déjà rattachée.
import { IonAccordion, IonAccordionGroup, IonItem, IonLabel } from '@ionic/vue'

import Ecran from '@/composants/Ecran.vue'

const QUESTIONS = [
  {
    q: 'Le client ne répond pas, que faire ?',
    r: 'Signalez l’absence depuis la course. Une deuxième tentative reste possible ; au '
      + 'deuxième échec, le colis repart chez le vendeur et le client en est prévenu.',
  },
  {
    q: 'Je n’ai pas le code de remise',
    r: 'Le code est affiché sur la commande du client. S’il ne le trouve pas, il peut le '
      + 'relire dans « Mes commandes ». Sans code, la livraison ne peut pas être confirmée : '
      + 'c’est ce qui vous protège s’il conteste ensuite.',
  },
  {
    q: 'Puis-je prendre deux courses à la fois ?',
    r: 'Non, en Express. Une course à la fois : c’est ce qui garantit que le repas arrive '
      + 'chaud, et c’est vérifié par le serveur, pas seulement masqué à l’écran.',
  },
  {
    q: 'Quand suis-je payé ?',
    r: 'Le gain est acquis à la confirmation de livraison. Il est suspendu si un litige est '
      + 'ouvert sur la commande, et débloqué à la décision — jamais versé puis repris.',
  },
  {
    q: 'Puis-je changer l’ordre de ma tournée ?',
    r: 'Non : l’ordre est calculé par l’entrepôt pour raccourcir le trajet de toute la zone. '
      + 'Si un arrêt pose problème, signalez-le depuis l’arrêt concerné.',
  },
]
</script>

<template>
  <Ecran titre="Aide et support" sous-titre="Questions fréquentes">
    <IonAccordionGroup>
      <IonAccordion v-for="(entree, index) in QUESTIONS" :key="index" :value="String(index)">
        <IonItem slot="header">
          <IonLabel class="question">{{ entree.q }}</IonLabel>
        </IonItem>
        <div slot="content" class="reponse">{{ entree.r }}</div>
      </IonAccordion>
    </IonAccordionGroup>

    <p class="note">
      Pour signaler un problème sur une livraison précise, passez par l'historique et
      ouvrez la livraison concernée : les informations de la commande partent avec le
      signalement, vous n'avez rien à ressaisir.
    </p>
  </Ecran>
</template>

<style scoped>
.question {
  font-size: 13px;
  font-weight: 600;
}
.reponse {
  padding: 12px 16px 16px;
  font-size: 12.5px;
  line-height: 1.65;
  color: var(--rd-encre-douce);
  background: #fff;
}
.note {
  margin-top: 16px;
  font-size: 11.5px;
  line-height: 1.6;
  color: var(--rd-encre-douce);
}
</style>
