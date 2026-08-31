<script setup lang="ts">
// Le suivi des commandes, côté client mobile.
//
// La frise est verticale et compacte : sur un téléphone, une frise horizontale
// à six étapes devient illisible dès qu'on nomme les étapes.
import { IonBadge, IonIcon } from '@ionic/vue'
import type { Commande } from '@partage/types'
import { ETAPES_SUIVI, LIBELLES_STATUT, euros, jour, positionSuivi, tonDuStatut }
  from '@partage/metier'
import { checkmarkCircle, receiptOutline } from 'ionicons/icons'
import { onMounted, ref } from 'vue'

import Ecran from '@/composants/Ecran.vue'
import { useSession } from '@/magasins/session'

const session = useSession()
const commandes = ref<Commande[]>([])
const chargement = ref(true)

const TONS: Record<string, string> = {
  succes: 'success', erreur: 'danger', cours: 'primary', attente: 'warning', neutre: 'medium',
}

async function charger() {
  chargement.value = true
  try {
    commandes.value = await session.client.get<Commande[]>('/mes-commandes')
  } finally {
    chargement.value = false
  }
}

onMounted(charger)
</script>

<template>
  <Ecran titre="Mes commandes" sous-titre="Espace client" :rafraichir="charger">
    <div v-for="commande in commandes" :key="commande.id" class="carte-mobile">
      <div class="entete">
        <span>
          <b>{{ commande.numero_commande }}</b>
          <span class="sous-titre">
            {{ jour(commande.date_commande) }} · {{ commande.boutiques.join(', ') }}
          </span>
        </span>
        <IonBadge :color="TONS[tonDuStatut(commande.statut_actuel)]">
          {{ LIBELLES_STATUT[commande.statut_actuel] }}
        </IonBadge>
      </div>

      <ol class="frise">
        <li
          v-for="(etape, index) in ETAPES_SUIVI[commande.type_service]"
          :key="etape"
          :class="index <= positionSuivi(commande.type_service, commande.statut_actuel)
            ? 'faite' : ''"
        >
          <span class="point">
            <IonIcon
              v-if="index < positionSuivi(commande.type_service, commande.statut_actuel)"
              :icon="checkmarkCircle"
            />
          </span>
          <span class="libelle">{{ LIBELLES_STATUT[etape] }}</span>
        </li>
      </ol>

      <div class="pied">
        <span class="sous-titre">{{ commande.adresse }}</span>
        <b>{{ euros(commande.montant_total_centimes) }}</b>
      </div>
    </div>

    <div v-if="!chargement && !commandes.length" class="etat-vide">
      <IonIcon :icon="receiptOutline" class="grande-icone" />
      <b>Aucune commande</b>
      <span>Vos commandes apparaîtront ici avec leur suivi, étape par étape.</span>
    </div>
  </Ecran>
</template>

<style scoped>
.entete {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 10px;
}
.entete b {
  font-size: 13.5px;
}
.frise {
  list-style: none;
  margin: 12px 0;
  padding: 0;
}
.frise li {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 3px 0;
  font-size: 12px;
  color: var(--rd-encre-douce);
}
.frise li.faite {
  color: var(--ion-text-color);
  font-weight: 600;
}
.point {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: var(--rd-trait);
  display: grid;
  place-items: center;
  color: #fff;
  font-size: 10px;
  flex-shrink: 0;
}
.frise li.faite .point {
  background: var(--accent);
}
.pied {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  border-top: 1px solid var(--rd-trait-doux);
  padding-top: 10px;
}
.grande-icone {
  font-size: 34px;
  color: var(--rd-trait);
}
</style>
