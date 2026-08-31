<script setup lang="ts">
// Le carnet d'adresses, côté mobile.
//
// Il compte plus qu'il n'y paraît : c'est l'adresse principale qui décide des
// boutiques Express visibles au catalogue (D-09). Un client qui déménage et ne
// change pas son adresse voit un catalogue faux.
import { IonButton, IonIcon, IonInput, IonModal, IonNote } from '@ionic/vue'
import { addOutline, homeOutline, starOutline } from 'ionicons/icons'
import { onMounted, ref } from 'vue'

import Ecran from '@/composants/Ecran.vue'
import { useSession } from '@/magasins/session'

type Adresse = {
  id: number
  libelle: string
  rue: string
  code_postal: string
  ville: string
  instructions_livraison: string
  est_principale: boolean
}

const session = useSession()
const adresses = ref<Adresse[]>([])
const ajout = ref(false)
const occupe = ref(false)
const nouvelle = ref({ libelle: 'Domicile', rue: '', code_postal: '', ville: '',
                       instructions_livraison: '' })

async function charger() {
  adresses.value = await session.client.get<Adresse[]>('/moi/adresses')
}

onMounted(charger)

async function enregistrer() {
  occupe.value = true
  try {
    adresses.value = await session.client.post<Adresse[]>('/moi/adresses', nouvelle.value)
    ajout.value = false
    nouvelle.value = { libelle: 'Domicile', rue: '', code_postal: '', ville: '',
                       instructions_livraison: '' }
  } finally {
    occupe.value = false
  }
}

async function definirPrincipale(adresse: Adresse) {
  adresses.value = await session.client.patch<Adresse[]>(
    `/moi/adresses/${adresse.id}`, { est_principale: true },
  )
}
</script>

<template>
  <Ecran titre="Mes adresses" sous-titre="Espace client" :rafraichir="charger">
    <template #actions>
      <IonButton fill="clear" @click="ajout = true">
        <IonIcon slot="icon-only" :icon="addOutline" style="color: #fff" />
      </IonButton>
    </template>

    <div v-for="adresse in adresses" :key="adresse.id" class="carte-mobile"
         :style="adresse.est_principale ? { borderColor: 'var(--accent)' } : undefined">
      <div class="entete">
        <span>
          <b>{{ adresse.libelle || 'Adresse' }}</b>
          <span class="sous-titre">
            {{ adresse.rue }}<br />{{ adresse.code_postal }} {{ adresse.ville }}
          </span>
        </span>
        <IonIcon v-if="adresse.est_principale" :icon="starOutline" class="etoile" />
      </div>
      <p v-if="adresse.instructions_livraison" class="consigne">
        « {{ adresse.instructions_livraison }} »
      </p>
      <IonButton v-if="!adresse.est_principale" size="small" fill="clear"
                 @click="definirPrincipale(adresse)">
        En faire mon adresse principale
      </IonButton>
    </div>

    <div v-if="!adresses.length" class="etat-vide">
      <IonIcon :icon="homeOutline" class="grande-icone" />
      <b>Aucune adresse enregistrée</b>
      <span>
        Ajoutez-en une : le catalogue vous montrera alors les boutiques Express qui livrent
        réellement chez vous.
      </span>
    </div>

    <IonModal :is-open="ajout" :initial-breakpoint="0.8" :breakpoints="[0, 0.8]"
              @did-dismiss="ajout = false">
      <div class="feuille">
        <h2>Nouvelle adresse</h2>
        <IonInput v-model="nouvelle.libelle" fill="outline" label="Libellé"
                  label-placement="floating" placeholder="Domicile, Bureau…" />
        <IonInput v-model="nouvelle.rue" fill="outline" label="Rue"
                  label-placement="floating" />
        <IonInput v-model="nouvelle.code_postal" fill="outline" label="Code postal"
                  label-placement="floating" inputmode="numeric" />
        <IonInput v-model="nouvelle.ville" fill="outline" label="Ville"
                  label-placement="floating" />
        <IonInput v-model="nouvelle.instructions_livraison" fill="outline"
                  label="Instructions pour le livreur" label-placement="floating"
                  placeholder="Code portail, étage…" />
        <IonNote class="note">
          Les instructions ne sont visibles que par le livreur qui vient chez vous — ni le
          vendeur ni l'entrepôt n'y ont accès.
        </IonNote>
        <IonButton expand="block" :disabled="occupe || !nouvelle.rue || !nouvelle.ville"
                   @click="enregistrer">
          Enregistrer
        </IonButton>
      </div>
    </IonModal>
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
.etoile {
  color: var(--accent);
  font-size: 18px;
}
.consigne {
  margin: 8px 0 0;
  font-size: 12px;
  color: var(--rd-encre-douce);
}
.grande-icone {
  font-size: 34px;
  color: var(--rd-trait);
}
.feuille {
  padding: 20px 18px calc(20px + env(safe-area-inset-bottom));
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.feuille h2 {
  margin: 0;
  font-size: 16px;
}
.note {
  font-size: 11px;
  line-height: 1.55;
}
</style>
