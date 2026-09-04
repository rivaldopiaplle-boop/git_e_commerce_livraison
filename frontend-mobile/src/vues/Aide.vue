<script setup lang="ts">
// L'aide — refaite au bloc O-4.
//
// **Ton reproche** : *« le support des livreurs chez le client, les questions
// des Standard chez les Express »*.
//
// Il était exact, et c'était la même faute deux fois : une seule liste de
// questions servait tout le monde. Un client lisait *« le client ne répond
// pas, que faire ? »* — une question qu'il ne se posera jamais — et un livreur
// Express lisait *« puis-je changer l'ordre de ma tournée ? »*, alors qu'il
// n'en a pas.
//
// Ce n'est pas seulement inélégant : **une aide qui parle du métier de
// quelqu'un d'autre apprend à ne pas lire l'aide.** Après deux questions hors
// sujet, on referme et on écrit au support.
//
// Les questions sont donc rangées par public, et l'écran ne montre que celles
// du rôle connecté — et, pour un livreur, de son mode.
import { IonAccordion, IonAccordionGroup, IonIcon, IonItem, IonLabel } from '@ionic/vue'
import { helpCircleOutline } from 'ionicons/icons'
import { computed } from 'vue'

import Ecran from '@/composants/Ecran.vue'
import { useSession } from '@/magasins/session'

const session = useSession()

type Question = { q: string; r: string }

/** Ce qu'un CLIENT se demande. Aucune de ces questions n'intéresse un livreur. */
const CLIENT: Question[] = [
  {
    q: 'Où est ma commande ?',
    r: 'Le suivi est sur la commande elle-même, dans « Mes commandes » : chaque étape '
      + 'y figure, de la préparation à la remise. Une commande Express arrive en '
      + 'général en moins de quarante minutes ; une commande Standard passe par un '
      + 'entrepôt et met de vingt-quatre à soixante-douze heures.',
  },
  {
    q: 'Qu’est-ce que le code de remise ?',
    r: 'Quatre chiffres que le livreur vous demandera à la porte. Ils sont affichés sur '
      + 'votre commande, dès qu’elle part en livraison. C’est la preuve que le bon colis '
      + 'est arrivé à la bonne personne — sans photo ni signature.',
  },
  {
    q: 'Pourquoi ma commande est-elle découpée en plusieurs ?',
    r: 'Un panier qui mélange plusieurs boutiques donne plusieurs commandes, livrées '
      + 'séparément — mais un seul paiement. Les boutiques Express sont livrées en '
      + 'direct, les Standard regroupées par un entrepôt.',
  },
  {
    q: 'Où va l’argent que je paie ?',
    r: 'Chaque commande a son détail : ce qui revient à chaque boutique, ce qui revient '
      + 'au livreur, et la commission de la plateforme. Ouvrez « Mon reçu » sur la '
      + 'commande concernée.',
  },
  {
    q: 'J’ai un problème avec une commande reçue',
    r: 'Ouvrez un signalement depuis la commande : la boutique a quarante-huit heures '
      + 'pour donner sa version, puis un administrateur tranche avec les deux récits. '
      + 'Vous suivez le dossier sur la commande elle-même.',
  },
  {
    q: 'Ma carte bancaire est-elle enregistrée ?',
    r: 'Le numéro complet n’est jamais conservé : il est remplacé par un jeton, et seuls '
      + 'la marque, les quatre derniers chiffres et l’échéance restent. Cette '
      + 'démonstration n’accepte d’ailleurs que des cartes d’essai — n’entrez jamais '
      + 'votre vraie carte.',
  },
]

/** Ce qui vaut pour TOUT livreur, quel que soit son mode. */
const LIVREUR: Question[] = [
  {
    q: 'Le client ne répond pas, que faire ?',
    r: 'Signalez l’absence depuis la course. Une deuxième tentative reste possible ; au '
      + 'deuxième échec, le colis repart chez le vendeur et le client en est prévenu.',
  },
  {
    q: 'Je n’ai pas le code de remise',
    r: 'Le code est affiché sur la commande du client. S’il ne le trouve pas, il peut le '
      + 'relire dans « Mes commandes ». Sans code, la livraison ne peut pas être '
      + 'confirmée : c’est ce qui vous protège s’il conteste ensuite.',
  },
  {
    q: 'Comment ma rémunération est-elle calculée ?',
    r: 'Une part fixe, plus un montant au kilomètre, avec un minimum garanti. Le détail '
      + 'du calcul est affiché sur chaque course dans votre historique : vous pouvez '
      + 'vérifier ce qu’on vous doit.',
  },
  {
    q: 'Quand suis-je payé ?',
    r: 'Le gain est acquis à la confirmation de livraison. Il est suspendu si un litige '
      + 'est ouvert sur la commande, et débloqué à la décision — jamais versé puis '
      + 'repris.',
  },
]

/** Express seulement : une course à la fois, prise à la volée. */
const EXPRESS: Question[] = [
  {
    q: 'Puis-je prendre deux courses à la fois ?',
    r: 'Non. Une course à la fois : c’est ce qui garantit que le repas arrive chaud, et '
      + 'c’est vérifié par le serveur, pas seulement masqué à l’écran.',
  },
  {
    q: 'Je suis disponible mais aucune course ne s’affiche',
    r: 'L’écran « À proximité » vous dit pourquoi : vous avez déjà une course en route, '
      + 'vous êtes hors ligne, ou rien n’attend dans votre rayon. Il ne vous laisse plus '
      + 'deviner.',
  },
]

/** Standard seulement : une tournée préparée par l'entrepôt. */
const STANDARD: Question[] = [
  {
    q: 'Puis-je changer l’ordre de ma tournée ?',
    r: 'Non : l’ordre est calculé par l’entrepôt pour raccourcir le trajet de toute la '
      + 'zone. Si un arrêt pose problème, signalez-le depuis l’arrêt concerné.',
  },
  {
    q: 'D’où vient ma tournée ?',
    r: 'Le gestionnaire de l’entrepôt confirme la réception des colis, demande le calcul '
      + 'd’une tournée, puis vous l’attribue. Il peut la recalculer tant qu’elle n’est '
      + 'pas partie — après le départ, l’ordre ne bouge plus.',
  },
  {
    q: 'Un client est absent : je perds mon arrêt ?',
    r: 'Non. Au premier passage sans réponse, l’arrêt repart en fin de tournée : vous '
      + 'continuez, et vous y revenez. C’est au deuxième passage que le colis repart '
      + 'chez le vendeur.',
  },
]

const questions = computed<Question[]>(() => {
  if (session.role !== 'LIVREUR') return CLIENT
  return [
    ...LIVREUR,
    ...(session.modeLivraison === 'STANDARD' ? STANDARD : EXPRESS),
  ]
})

const pour = computed(() =>
  session.role !== 'LIVREUR'
    ? 'Espace client'
    : `Livreur · ${session.modeLivraison === 'STANDARD' ? 'Standard' : 'Express'}`,
)
</script>

<template>
  <Ecran titre="Aide et support" :sous-titre="pour">
    <p class="intro">
      <IonIcon :icon="helpCircleOutline" />
      <span>
        Ces questions sont celles de <b>{{ pour.toLowerCase() }}</b>.
        Une aide qui parle du métier de quelqu'un d'autre n'est pas lue.
      </span>
    </p>

    <IonAccordionGroup>
      <IonAccordion v-for="(entree, index) in questions" :key="index" :value="String(index)">
        <IonItem slot="header">
          <IonLabel class="question">{{ entree.q }}</IonLabel>
        </IonItem>
        <div slot="content" class="reponse">{{ entree.r }}</div>
      </IonAccordion>
    </IonAccordionGroup>

    <p class="note">
      <template v-if="session.role === 'LIVREUR'">
        Pour signaler un problème sur une livraison précise, passez par l'historique et
        ouvrez la livraison concernée : les informations de la commande partent avec le
        signalement, vous n'avez rien à ressaisir.
      </template>
      <template v-else>
        Pour un problème sur une commande précise, passez par « Mes commandes » et
        ouvrez la commande concernée : le signalement part avec tout son contexte, et
        vous en suivez la réponse au même endroit.
      </template>
    </p>
  </Ecran>
</template>

<style scoped>
.intro {
  display: flex;
  align-items: flex-start;
  gap: 9px;
  margin: 0 0 14px;
  padding: 10px 12px;
  border-radius: 10px;
  background: var(--accent-doux);
  font-size: 11.5px;
  line-height: 1.6;
  color: var(--rd-encre-douce);
}
.intro ion-icon {
  font-size: 16px;
  color: var(--accent);
  flex-shrink: 0;
}
.intro b {
  color: var(--ion-text-color);
}
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
