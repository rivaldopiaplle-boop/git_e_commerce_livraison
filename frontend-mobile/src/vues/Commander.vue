<script setup lang="ts">
// Commander et payer, depuis le téléphone — N-6.
//
// **Le trou le plus grave du mobile**, et il ne se voyait pas : le bouton
// « Passer commande » du panier se contentait de **naviguer vers la liste des
// commandes**. On pouvait donc parcourir le catalogue, remplir son panier…
// et s'arrêter là. Une application de livraison où l'on ne peut pas commander
// n'est pas une application de livraison.
//
// Un seul écran plutôt que deux (récapitulatif puis paiement, comme sur le
// web) : sur un téléphone, chaque écran de plus est un abandon de plus. Le
// découpage du panier, l'adresse et le paiement tiennent ici, dans cet ordre —
// celui dans lequel on y pense.
import {
  IonButton, IonIcon, IonModal, IonRadio, IonRadioGroup, IonSpinner,
} from '@ionic/vue'
import { euros } from '@partage/metier'
import type { Commande } from '@partage/types'
import {
  alertCircleOutline, bicycleOutline, cardOutline, cubeOutline, locationOutline,
  shieldCheckmarkOutline,
} from 'ionicons/icons'
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'

import { EchecApi } from '@partage/api'

import Cartes from '@/composants/Cartes.vue'
import Ecran from '@/composants/Ecran.vue'
import { usePanier } from '@/magasins/panier'
import { useSession } from '@/magasins/session'
import { useRafraichissement } from '@/rafraichissement'

type Apercu = {
  type_service: string
  boutiques: string[]
  articles: number
  montant_produits_centimes: number
  montant_livraison_centimes: number
}

type Bloquante = { id_ligne: number; nom: string; message: string }

type Carte = { id: number; libelle: string; expiree: boolean }

type Adresse = {
  id: number
  libelle: string
  rue: string
  code_postal: string
  ville: string
  est_principale: boolean
}

const session = useSession()
const panier = usePanier()
const routeur = useRouter()

const apercu = ref<Apercu[]>([])
const bloquantes = ref<Bloquante[]>([])
const total = ref(0)
const carnet = ref<Adresse[]>([])
const adresseChoisie = ref<number | null>(null)

const chargement = ref(true)
const envoi = ref(false)
const erreur = ref('')
const etape = ref('')

/**
 * La carte, et la reconfirmation — O-5.
 *
 * *« Payer est validé sans carte, pas de demande de carte même la première
 * fois »* et *« l'argent est payé sans reconfirmation »*. Les deux étaient
 * vrais : un appui, et c'était débité.
 *
 * Sur un téléphone, la feuille de confirmation compte encore plus qu'ailleurs :
 * le pouce est déjà sur le bouton quand la page finit de se charger.
 */
const carte = ref<Carte | null>(null)
const confirmation = ref(false)

/** Le message du serveur quand il y en a un : il en sait plus que nous. */
function message(souci: unknown, defaut: string) {
  return souci instanceof EchecApi ? souci.erreur.message : defaut
}

const articles = computed(() =>
  apercu.value.reduce((somme, bloc) => somme + bloc.articles, 0),
)

async function charger() {
  erreur.value = ''
  try {
    const donnees = await session.client.get<{
      commandes: Apercu[]
      total_centimes: number
      lignes_bloquantes: Bloquante[]
    }>('/panier/apercu-commandes')
    apercu.value = donnees.commandes
    total.value = donnees.total_centimes
    bloquantes.value = donnees.lignes_bloquantes ?? []

    carnet.value = await session.client.get<Adresse[]>('/moi/adresses')
    adresseChoisie.value =
      carnet.value.find((a) => a.est_principale)?.id ?? carnet.value[0]?.id ?? null
  } catch (souci) {
    erreur.value = message(souci, 'Panier indisponible.')
  } finally {
    chargement.value = false
  }
}

useRafraichissement(charger)

/** Retirer d'un coup ce qui n'est plus commandable, plutôt que bloquer. */
async function retirerIndisponibles() {
  envoi.value = true
  try {
    await session.client.post('/panier/nettoyer', {})
    await panier.charger()
    await charger()
  } catch (souci) {
    erreur.value = message(souci, 'Nettoyage impossible.')
  } finally {
    envoi.value = false
  }
}

/**
 * Créer les commandes, puis les payer — en une seule action.
 *
 * Sur le web, ce sont deux écrans (D-101) parce qu'un client peut revenir plus
 * tard régler une commande laissée en attente. Sur un téléphone, on paie dans
 * la foulée : c'est ce que font toutes les applications de livraison, et un
 * écran de plus entre le panier et le paiement est un abandon de plus.
 *
 * La réservation de stock rend l'enchaînement sûr : elle est posée à la
 * création (D-99), donc rien ne peut partir entre les deux.
 */
async function payer() {
  confirmation.value = false
  envoi.value = true
  erreur.value = ''
  try {
    etape.value = 'Création de la commande…'
    const creees = await session.client.post<Commande[]>('/commandes', {
      id_adresse: adresseChoisie.value,
    })

    let payees = 0
    for (const commande of creees) {
      etape.value = `Paiement de ${commande.numero_commande}…`
      const intention = await session.client.post<{ reference: string }>(
        `/commandes/${commande.id}/paiement`, { id_carte: carte.value?.id },
      )
      const resultat = await session.client.post<{ statut: string }>(
        '/paiements/confirmation', { reference: intention.reference },
      )
      if (resultat.statut === 'CAPTURE') payees += 1
    }

    await panier.charger()
    if (payees) {
      routeur.replace({ path: '/commandes', query: { payees } })
    } else {
      erreur.value = 'Le paiement a été refusé. Aucun montant n’a été débité.'
      await charger()
    }
  } catch (souci) {
    erreur.value = message(souci, 'Commande impossible.')
    await charger()
  } finally {
    envoi.value = false
    etape.value = ''
  }
}
</script>

<template>
  <Ecran titre="Commander" sous-titre="Espace client" :rafraichir="charger">
    <div v-if="chargement" class="centre"><IonSpinner /></div>

    <template v-else-if="apercu.length">
      <!-- Ce qui bloque, nommément : sans cela on ne sait pas quoi retirer -->
      <div v-if="bloquantes.length" class="avertissement">
        <b>
          <IonIcon :icon="alertCircleOutline" />
          {{ bloquantes.length }} article{{ bloquantes.length > 1 ? 's' : '' }}
          ne {{ bloquantes.length > 1 ? 'peuvent' : 'peut' }} plus être
          command{{ bloquantes.length > 1 ? 'és' : 'é' }}
        </b>
        <span v-for="ligne in bloquantes" :key="ligne.id_ligne" class="bloquante">
          {{ ligne.nom }} — {{ ligne.message }}
        </span>
        <IonButton size="small" fill="outline" :disabled="envoi"
                   @click="retirerIndisponibles">
          Les retirer et continuer
        </IonButton>
      </div>

      <!-- Le découpage, AVANT de payer : le découvrir après serait une
           mauvaise surprise (D-10). -->
      <p class="explication">
        {{ articles }} article{{ articles > 1 ? 's' : '' }} —
        <b>{{ apercu.length }} commande{{ apercu.length > 1 ? 's' : '' }}</b>
        <template v-if="apercu.length > 1">, livrées séparément, un seul paiement</template>
      </p>

      <div v-for="(bloc, index) in apercu" :key="index" class="carte-mobile bloc">
        <IonIcon :icon="bloc.type_service === 'EXPRESS' ? bicycleOutline : cubeOutline" />
        <span class="detail">
          <b>{{ bloc.type_service === 'EXPRESS' ? 'Livraison Express' : 'Livraison Standard' }}</b>
          <span class="sous-titre">
            {{ bloc.boutiques.join(' · ') }} — {{ bloc.articles }} article{{
              bloc.articles > 1 ? 's' : '' }}
          </span>
        </span>
        <b class="prix">
          {{ euros(bloc.montant_produits_centimes + bloc.montant_livraison_centimes) }}
        </b>
      </div>

      <!-- L'adresse : elle décide aussi des boutiques Express visibles (D-09) -->
      <div class="carte-mobile">
        <b class="titre-carte"><IonIcon :icon="locationOutline" /> Livrer à</b>
        <IonRadioGroup v-if="carnet.length" v-model="adresseChoisie">
          <label v-for="adresse in carnet" :key="adresse.id" class="adresse">
            <IonRadio :value="adresse.id" />
            <span>
              <b>{{ adresse.libelle || 'Adresse' }}</b>
              <span class="sous-titre">
                {{ adresse.rue }}, {{ adresse.code_postal }} {{ adresse.ville }}
              </span>
            </span>
          </label>
        </IonRadioGroup>
        <template v-else>
          <p class="sous-titre">Aucune adresse enregistrée.</p>
          <IonButton size="small" fill="outline" @click="routeur.push('/adresses')">
            Ajouter une adresse
          </IonButton>
        </template>
      </div>

      <!-- La carte, qui n'était jamais demandée (O-5) -->
      <Cartes @choisie="(choisie) => (carte = choisie)" />

      <p class="bandeau-simulation">
        <IonIcon :icon="shieldCheckmarkOutline" />
        <span>
          <b>Paiement en mode simulation.</b> La carte est réellement vérifiée,
          mais aucun montant n’est débité et seules les cartes d’essai sont
          acceptées.
        </span>
      </p>

      <p v-if="erreur" class="erreur">{{ erreur }}</p>

      <div class="barre">
        <span>
          <span class="sous-titre">Total à payer</span>
          <b>{{ euros(total) }}</b>
        </span>
        <IonButton :disabled="envoi || !adresseChoisie || !carte"
                   @click="confirmation = true">
          <IonIcon v-if="!envoi" :icon="cardOutline" slot="start" />
          <IonSpinner v-else name="dots" />
          {{ envoi ? etape || 'Paiement…' : 'Payer' }}
        </IonButton>
      </div>
    </template>

    <!-- La reconfirmation : elle dit le montant ET la carte. Un bouton qui ne
         dit ni combien ni avec quoi n'est pas une confirmation (O-5). -->
    <IonModal :is-open="confirmation" :initial-breakpoint="0.5" :breakpoints="[0, 0.5]"
              @did-dismiss="confirmation = false">
      <div class="feuille">
        <b class="titre">Confirmer le paiement</b>
        <dl class="recap">
          <div><dt>Montant</dt><dd class="gros">{{ euros(total) }}</dd></div>
          <div><dt>Carte</dt><dd>{{ carte?.libelle }}</dd></div>
          <div>
            <dt>Commandes</dt>
            <dd>
              {{ apercu.length }} commande{{ apercu.length > 1 ? 's' : '' }}<template
                v-if="apercu.length > 1">, livrées séparément</template>
            </dd>
          </div>
        </dl>
        <p class="mention">
          Aucun montant n’est réellement débité : cette démonstration tourne en
          mode simulation.
        </p>
        <IonButton expand="block" :disabled="envoi" @click="payer">
          Payer {{ euros(total) }}
        </IonButton>
        <IonButton expand="block" fill="clear" color="medium" @click="confirmation = false">
          Revenir
        </IonButton>
      </div>
    </IonModal>

    <div v-if="!chargement && !apercu.length" class="etat-vide">
      <IonIcon :icon="cubeOutline" class="grande-icone" />
      <b>Rien à commander</b>
      <span>Votre panier est vide.</span>
      <IonButton fill="outline" size="small" class="ion-margin-top"
                 @click="routeur.push('/recherche')">
        Voir le catalogue
      </IonButton>
    </div>
  </Ecran>
</template>

<style scoped>
.centre {
  display: grid;
  place-items: center;
  padding: 40px 0;
}
.explication {
  font-size: 12.5px;
  color: var(--rd-encre-douce);
}
.bloc {
  display: flex;
  align-items: center;
  gap: 12px;
}
.bloc > ion-icon {
  font-size: 22px;
  color: var(--accent);
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
.prix {
  font-size: 13.5px;
}
.titre-carte {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  margin-bottom: 8px;
}
.adresse {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 8px 0;
  border-top: 1px solid var(--rd-trait);
}
.adresse:first-of-type {
  border-top: 0;
}
.adresse b {
  display: block;
  font-size: 13px;
}
.avertissement,
.bandeau-simulation {
  display: flex;
  flex-direction: column;
  gap: 8px;
  font-size: 11.5px;
  line-height: 1.6;
  border-radius: 10px;
  padding: 10px 12px;
}
.avertissement {
  color: #7a4a06;
  background: #fff6ea;
  border: 1px solid #ffe2b3;
}
.bandeau-simulation {
  flex-direction: row;
  align-items: flex-start;
  gap: 10px;
  color: #26399e;
  background: #eef3ff;
  border: 1px solid #cddaff;
}
.bloquante {
  display: block;
}
.erreur {
  font-size: 12px;
  color: var(--rd-alerte, #9c2116);
  background: #fbe4e2;
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
.grande-icone {
  font-size: 34px;
  color: var(--rd-trait);
}
.feuille {
  padding: 20px 16px calc(20px + var(--rd-marge-basse, 12px));
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.feuille .titre {
  font-size: 17px;
}
.recap {
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.recap > div {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 12px;
  font-size: 13px;
}
.recap dt {
  color: var(--rd-encre-douce);
}
.recap dd {
  margin: 0;
  font-weight: 700;
}
.recap dd.gros {
  font-size: 19px;
  color: var(--accent);
}
.mention {
  margin: 0;
  font-size: 11px;
  line-height: 1.6;
  color: var(--rd-encre-douce);
}
</style>
