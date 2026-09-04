<script setup lang="ts">
// Le suivi des commandes, côté client mobile.
//
// La frise est verticale et compacte : sur un téléphone, une frise horizontale
// à six étapes devient illisible dès qu'on nomme les étapes.
import {
  IonBadge, IonButton, IonIcon, IonModal, IonRadio, IonRadioGroup, IonTextarea,
} from '@ionic/vue'
import { EchecApi } from '@partage/api'
import type { Commande } from '@partage/types'
import { ETAPES_SUIVI, LIBELLES_STATUT, euros, jour, positionSuivi, tonDuStatut }
  from '@partage/metier'
import {
  checkmarkCircle, documentTextOutline, receiptOutline, shieldOutline, star,
  starOutline,
} from 'ionicons/icons'
import { computed, onMounted, ref } from 'vue'

import Ecran from '@/composants/Ecran.vue'
import { useSession } from '@/magasins/session'

type Facture = {
  numero_facture: string | null
  numero_commande: string
  adresse: string
  montant_produits_centimes: number
  montant_livraison_centimes: number
  montant_total_centimes: number
  montant_ht_centimes: number | null
  taux_tva: number
  lignes: {
    boutique: string
    nom: string
    quantite: number
    prix_unitaire_centimes: number
    sous_total_centimes: number
  }[]
}

type Notable = {
  cible: string
  id_cible: number
  libelle: string
  sous_titre: string
  note: number | null
  commentaire: string
}

const session = useSession()
const commandes = ref<Commande[]>([])
const chargement = ref(true)

const TONS: Record<string, string> = {
  succes: 'success', erreur: 'danger', cours: 'primary', attente: 'warning', neutre: 'medium',
}

/** On ne note et on ne conteste que ce qu'on a recu (R-06, D-94). */
const TERMINEES = ['LIVREE', 'ECHEC_LIVRAISON']
const estNotable = (commande: Commande) => commande.statut_actuel === 'LIVREE'
const estContestable = (commande: Commande) => TERMINEES.includes(commande.statut_actuel)

function message(souci: unknown, defaut: string) {
  return souci instanceof EchecApi ? souci.erreur.message : defaut
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

// ── Le recu ──────────────────────────────────────────────────────────────
const facture = ref<Facture | null>(null)
const recuOuvert = ref(false)

/**
 * Une commande n'a de recu qu'une fois payee.
 *
 * On liste ce qui N'EN A PAS plutot que ce qui en a : la premiere version
 * enumerait les statuts payes et en avait oublie trois — un statut ajoute
 * demain aurait fait disparaitre le bouton sans que personne ne le remarque.
 * Une commande remboursee garde son recu : c'est meme la qu'on veut le relire.
 */
const SANS_RECU = ['EN_ATTENTE_PAIEMENT', 'ANNULEE']
const aUnRecu = (commande: Commande) => !SANS_RECU.includes(commande.statut_actuel)

async function ouvrirRecu(commande: Commande) {
  erreur.value = ''
  recuOuvert.value = true
  facture.value = null
  try {
    facture.value = await session.client.get<Facture>(`/commandes/${commande.id}/facture`)
  } catch (souci) {
    erreur.value = message(souci, 'Reçu indisponible.')
  }
}

// ── L'avis ───────────────────────────────────────────────────────────────
const avisPour = ref<Commande | null>(null)
const notables = ref<Notable[]>([])
const choisi = ref<Notable | null>(null)
const note = ref(5)
const commentaire = ref('')
const occupe = ref(false)
const erreur = ref('')
const succes = ref('')

/**
 * Les cibles, regroupees par nature.
 *
 * A plat, on lisait « Julien » entre deux produits sans comprendre pourquoi :
 * c'est le livreur. Le titre de groupe le dit.
 */
const groupes = computed(() => [
  { titre: 'La boutique', elements: notables.value.filter((e) => e.cible === 'VENDEUR') },
  { titre: 'Les produits recus', elements: notables.value.filter((e) => e.cible === 'PRODUIT') },
  { titre: 'La livraison', elements: notables.value.filter((e) => e.cible === 'LIVREUR') },
].filter((groupe) => groupe.elements.length))

async function ouvrirAvis(commande: Commande) {
  erreur.value = ''
  succes.value = ''
  avisPour.value = commande
  try {
    const donnees = await session.client.get<{ elements: Notable[] }>(
      `/commandes/${commande.id}/avis`,
    )
    notables.value = donnees.elements
    choisir(donnees.elements[0] ?? null)
  } catch (souci) {
    erreur.value = message(souci, 'Impossible de charger ce qui est notable.')
  }
}

function choisir(element: Notable | null) {
  choisi.value = element
  note.value = element?.note ?? 5
  commentaire.value = element?.commentaire ?? ''
}

async function envoyerAvis() {
  if (!avisPour.value || !choisi.value) return
  occupe.value = true
  erreur.value = ''
  try {
    const donnees = await session.client.post<{ elements: Notable[] }>(
      `/commandes/${avisPour.value.id}/avis`,
      {
        cible: choisi.value.cible,
        id_cible: choisi.value.id_cible,
        note: note.value,
        commentaire: commentaire.value,
      },
    )
    notables.value = donnees.elements
    succes.value = 'Merci, votre avis est enregistre.'
    // On enchaine sur ce qui reste a noter : c'est le geste utile suivant.
    const suivant = donnees.elements.find((element) => element.note === null)
    if (suivant) choisir(suivant)
  } catch (souci) {
    erreur.value = message(souci, "L'avis n'a pas ete pris.")
  } finally {
    occupe.value = false
  }
}

// ── Le signalement ───────────────────────────────────────────────────────
const litigePour = ref<Commande | null>(null)
const motif = ref('INCOMPLET')
const recit = ref('')

const MOTIFS = [
  { cle: 'NON_RECU', libelle: 'Je n\u2019ai jamais recu ma commande' },
  { cle: 'INCOMPLET', libelle: 'Il manque des articles' },
  { cle: 'ENDOMMAGE', libelle: 'Un produit est arrive abime' },
  { cle: 'NON_CONFORME', libelle: 'Ce n\u2019est pas ce que j\u2019avais commande' },
]

function ouvrirLitige(commande: Commande) {
  litigePour.value = commande
  motif.value = 'INCOMPLET'
  recit.value = ''
  erreur.value = ''
  succes.value = ''
}

async function envoyerLitige() {
  if (!litigePour.value) return
  occupe.value = true
  erreur.value = ''
  try {
    await session.client.post(`/commandes/${litigePour.value.id}/litiges`, {
      motif: motif.value,
      description: recit.value,
    })
    litigePour.value = null
    succes.value = 'Signalement enregistre. La boutique a 48 heures pour repondre.'
  } catch (souci) {
    erreur.value = message(souci, "Le signalement n'a pas ete pris.")
  } finally {
    occupe.value = false
  }
}
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

      <!-- Noter et signaler, la ou l'on est quand le colis arrive : sur son
           telephone. Les deux gestes manquaient (N-6). -->
      <div v-if="estContestable(commande) || aUnRecu(commande)" class="actions">
        <IonButton v-if="aUnRecu(commande)" size="small" fill="outline"
                   @click="ouvrirRecu(commande)">
          <IonIcon :icon="documentTextOutline" slot="start" /> Mon reçu
        </IonButton>
        <IonButton v-if="estNotable(commande)" size="small" fill="outline"
                   @click="ouvrirAvis(commande)">
          <IonIcon :icon="starOutline" slot="start" /> Donner mon avis
        </IonButton>
        <IonButton size="small" fill="outline" color="danger"
                   @click="ouvrirLitige(commande)">
          <IonIcon :icon="shieldOutline" slot="start" /> Signaler un probleme
        </IonButton>
      </div>
    </div>

    <div v-if="!chargement && !commandes.length" class="etat-vide">
      <IonIcon :icon="receiptOutline" class="grande-icone" />
      <b>Aucune commande</b>
      <span>Vos commandes apparaîtront ici avec leur suivi, étape par étape.</span>
    </div>

    <p v-if="succes" class="succes">{{ succes }}</p>

    <!-- Le recu : les memes chiffres que la facture du web, au pouce -->
    <IonModal :is-open="recuOuvert" @did-dismiss="recuOuvert = false">
      <div class="feuille">
        <b class="titre">Mon reçu</b>
        <template v-if="facture">
          <p class="sous-titre">
            {{ facture.numero_facture || facture.numero_commande }} — {{ facture.adresse }}
          </p>
          <div v-for="(ligne, index) in facture.lignes" :key="index" class="ligne-recu">
            <span>
              <b>{{ ligne.nom }}</b>
              <span class="sous-titre">
                {{ ligne.boutique }} · {{ ligne.quantite }} ×
                {{ euros(ligne.prix_unitaire_centimes) }}
              </span>
            </span>
            <b>{{ euros(ligne.sous_total_centimes) }}</b>
          </div>
          <div class="ligne-recu total">
            <span class="sous-titre">Produits</span>
            <span>{{ euros(facture.montant_produits_centimes) }}</span>
          </div>
          <div class="ligne-recu total">
            <span class="sous-titre">Livraison</span>
            <span>{{ euros(facture.montant_livraison_centimes) }}</span>
          </div>
          <div class="ligne-recu total gros">
            <b>Total payé</b>
            <b>{{ euros(facture.montant_total_centimes) }}</b>
          </div>
          <span class="aide">
            TVA {{ (facture.taux_tva * 100).toFixed(0) }} % incluse. La facture
            imprimable est dans l'espace web.
          </span>
        </template>
        <p v-else-if="!erreur" class="aide">Chargement…</p>
        <p v-if="erreur" class="erreur">{{ erreur }}</p>
        <IonButton expand="block" fill="outline" @click="recuOuvert = false">Fermer</IonButton>
      </div>
    </IonModal>

    <!-- L'avis : on note la boutique, chaque produit recu, et le livreur -->
    <IonModal :is-open="!!avisPour" @did-dismiss="avisPour = null">
      <div class="feuille">
        <b class="titre">Donner mon avis</b>
        <p class="sous-titre">{{ avisPour?.numero_commande }}</p>

        <div v-for="groupe in groupes" :key="groupe.titre" class="groupe">
          <span class="etiquette">{{ groupe.titre }}</span>
          <div class="puces">
            <button
              v-for="element in groupe.elements"
              :key="`${element.cible}-${element.id_cible}`"
              type="button"
              class="puce"
              :class="choisi?.cible === element.cible
                && choisi?.id_cible === element.id_cible ? 'active' : ''"
              @click="choisir(element)"
            >
              {{ element.libelle }}
              <IonIcon v-if="element.note" :icon="star" />
            </button>
          </div>
        </div>

        <template v-if="choisi">
          <div class="etoiles">
            <button v-for="valeur in 5" :key="valeur" type="button" @click="note = valeur">
              <IonIcon :icon="valeur <= note ? star : starOutline" />
            </button>
            <b>{{ note }} / 5</b>
          </div>
          <IonTextarea v-model="commentaire" :rows="3" fill="outline"
                       placeholder="Ce qui vous a plu, ou pas." />
        </template>

        <p v-if="erreur" class="erreur">{{ erreur }}</p>

        <div class="boutons">
          <IonButton fill="outline" @click="avisPour = null">Fermer</IonButton>
          <IonButton :disabled="occupe || !choisi" @click="envoyerAvis">
            {{ choisi?.note ? 'Modifier mon avis' : 'Publier mon avis' }}
          </IonButton>
        </div>
      </div>
    </IonModal>

    <!-- Le signalement : la boutique repond, puis un administrateur tranche -->
    <IonModal :is-open="!!litigePour" @did-dismiss="litigePour = null">
      <div class="feuille">
        <b class="titre">Signaler un probleme</b>
        <p class="sous-titre">
          La boutique aura 48 heures pour donner sa version, puis un administrateur
          tranchera avec les deux recits.
        </p>

        <IonRadioGroup v-model="motif">
          <label v-for="choix in MOTIFS" :key="choix.cle" class="motif">
            <IonRadio :value="choix.cle" />
            <span>{{ choix.libelle }}</span>
          </label>
        </IonRadioGroup>

        <IonTextarea v-model="recit" :rows="4" fill="outline"
                     placeholder="Ce que vous avez recu, ce qui manquait, dans quel etat." />
        <span class="aide">
          C'est ce texte que la boutique et l'administrateur liront pour trancher.
        </span>

        <p v-if="erreur" class="erreur">{{ erreur }}</p>

        <div class="boutons">
          <IonButton fill="outline" @click="litigePour = null">Annuler</IonButton>
          <IonButton color="danger" :disabled="occupe || recit.trim().length < 20"
                     @click="envoyerLitige">
            Envoyer
          </IonButton>
        </div>
      </div>
    </IonModal>
  </Ecran>
</template>

<style scoped>
.actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-top: 10px;
}
.feuille {
  padding: 20px 16px calc(20px + env(safe-area-inset-bottom));
  display: flex;
  flex-direction: column;
  gap: 12px;
  overflow-y: auto;
}
.feuille .titre {
  font-size: 17px;
}
.etiquette {
  font-size: 10.5px;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--rd-encre-douce);
}
.puces {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 6px;
}
.puce {
  border: 1px solid var(--rd-trait);
  background: #fff;
  border-radius: 999px;
  padding: 6px 12px;
  font-size: 12px;
}
.puce.active {
  border-color: var(--accent);
  color: var(--accent);
  font-weight: 700;
}
.etoiles {
  display: flex;
  align-items: center;
  gap: 6px;
}
.etoiles button {
  background: none;
  border: 0;
  font-size: 24px;
  color: var(--accent);
  padding: 0;
}
.motif {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 0;
  border-top: 1px solid var(--rd-trait);
  font-size: 13px;
}
.motif:first-of-type {
  border-top: 0;
}
.ligne-recu {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  font-size: 12.5px;
  border-bottom: 1px solid var(--rd-trait-doux);
  padding-bottom: 8px;
}
.ligne-recu b {
  display: block;
  font-size: 13px;
}
.ligne-recu.total {
  border-bottom: 0;
  padding-bottom: 0;
}
.ligne-recu.gros {
  border-top: 1px solid var(--rd-trait);
  padding-top: 10px;
  font-size: 15px;
}
.ligne-recu.gros b:last-child {
  font-size: 17px;
  color: var(--accent);
}
.boutons {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 4px;
}
.aide,
.erreur,
.succes {
  font-size: 11.5px;
  line-height: 1.6;
}
.aide {
  color: var(--rd-encre-douce);
}
.erreur {
  color: #9c2116;
  background: #fbe4e2;
  border-radius: 10px;
  padding: 10px 12px;
}
.succes {
  color: #116b34;
  background: #e2f7ea;
  border-radius: 10px;
  padding: 10px 12px;
  text-align: center;
}
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
