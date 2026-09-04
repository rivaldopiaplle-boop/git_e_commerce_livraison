<script setup lang="ts">
// Le panier mobile.
//
// Il existe AVANT le compte (D-03) : on remplit son panier, et le compte n'est
// exigé qu'au moment de commander. Le panier suit ensuite le visiteur jusqu'à
// son compte — le lui dire évite qu'il croie devoir tout recommencer.
import { IonButton, IonIcon } from '@ionic/vue'
import { euros } from '@partage/metier'
import { addOutline, bagHandleOutline, removeOutline, trashOutline } from 'ionicons/icons'
import { useRouter } from 'vue-router'

import Ecran from '@/composants/Ecran.vue'
import { usePanier } from '@/magasins/panier'
import { useSession } from '@/magasins/session'
import { useRafraichissement } from '@/rafraichissement'

const panier = usePanier()
const session = useSession()
const routeur = useRouter()

useRafraichissement(() => panier.charger())
</script>

<template>
  <Ecran titre="Mon panier" sous-titre="Espace client" :rafraichir="panier.charger">
    <template v-if="panier.contenu.lignes.length">
      <div v-for="ligne in panier.contenu.lignes" :key="ligne.id" class="carte-mobile ligne">
        <img v-if="ligne.produit.image" :src="ligne.produit.image" :alt="ligne.produit.nom" />
        <span class="detail">
          <b>{{ ligne.produit.nom }}</b>
          <span class="sous-titre">{{ ligne.produit.boutique.nom }}</span>
          <span class="quantite">
            <button type="button" @click="panier.changerQuantite(ligne.id, ligne.quantite - 1)">
              <IonIcon :icon="ligne.quantite > 1 ? removeOutline : trashOutline" />
            </button>
            <b>{{ ligne.quantite }}</b>
            <button type="button" @click="panier.changerQuantite(ligne.id, ligne.quantite + 1)">
              <IonIcon :icon="addOutline" />
            </button>
          </span>
        </span>
        <b class="prix">{{ euros(ligne.sous_total_centimes) }}</b>
      </div>

      <p v-if="panier.plusieursBoutiques" class="avertissement">
        Ce panier mélange plusieurs boutiques : il donnera plusieurs commandes, livrées
        séparément — un seul paiement, plusieurs livraisons.
      </p>

      <div class="barre">
        <span>
          <span class="sous-titre">Total</span>
          <b>{{ euros(panier.contenu.total_centimes) }}</b>
        </span>
        <IonButton v-if="session.estConnecte" @click="routeur.push('/commander')">
          Passer commande
        </IonButton>
        <IonButton v-else @click="routeur.push({ path: '/connexion', query: { suite: '/panier' } })">
          Se connecter
        </IonButton>
      </div>
      <p v-if="!session.estConnecte" class="note">
        Votre panier vous suit : vous le retrouverez tel quel après connexion.
      </p>
    </template>

    <div v-else class="etat-vide">
      <IonIcon :icon="bagHandleOutline" class="grande-icone" />
      <b>Votre panier est vide</b>
      <span>Ajoutez des articles depuis le catalogue.</span>
      <IonButton fill="outline" size="small" class="ion-margin-top"
                 @click="routeur.push('/recherche')">
        Voir le catalogue
      </IonButton>
    </div>
  </Ecran>
</template>

<style scoped>
.ligne {
  display: flex;
  align-items: center;
  gap: 12px;
}
.ligne img {
  width: 52px;
  height: 52px;
  border-radius: 10px;
  object-fit: cover;
  flex-shrink: 0;
}
.detail {
  flex: 1;
  min-width: 0;
}
.detail b {
  display: block;
  font-size: 13px;
}
.quantite {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 6px;
}
.quantite button {
  width: 30px;
  height: 30px;
  border-radius: 8px;
  border: 1px solid var(--rd-trait);
  background: #fff;
  display: grid;
  place-items: center;
}
.prix {
  font-size: 13.5px;
}
.avertissement {
  font-size: 11.5px;
  line-height: 1.6;
  color: #7a4a06;
  background: #fff6ea;
  border: 1px solid #ffe2b3;
  border-radius: 10px;
  padding: 10px 12px;
}
.barre {
  position: sticky;
  bottom: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  background: #fff;
  border-top: 1px solid var(--rd-trait);
  margin: 12px -14px -24px;
  padding: 10px 14px calc(10px + var(--rd-marge-basse, 12px));
}
.barre b {
  display: block;
  font-size: 20px;
  font-weight: 800;
  color: var(--accent);
}
.note {
  font-size: 11px;
  color: var(--rd-encre-douce);
  text-align: center;
}
.grande-icone {
  font-size: 34px;
  color: var(--rd-trait);
}
</style>
