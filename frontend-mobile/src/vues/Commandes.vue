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
  checkmarkCircle, chevronDown, documentTextOutline, printOutline, receiptOutline,
  shieldOutline, star, starOutline,
} from 'ionicons/icons'
import { computed, ref } from 'vue'

import Ecran from '@/composants/Ecran.vue'
import { useSession } from '@/magasins/session'
import { useRafraichissement } from '@/rafraichissement'

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

type Litige = {
  id: number
  libelle_motif: string
  description: string
  statut: string
  libelle_statut: string
  resolution: string
  montant_rembourse_centimes: number
  date_ouverture: string
  date_limite_reponse: string | null
  reponse_vendeur: string
  delai_expire: boolean
  id_commande: number
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

/**
 * Ce qui est déplié — O-5.
 *
 * *« Mes commandes, avec tous les reçus dépliés à la figure. »* Chaque
 * commande montrait sa frise de six étapes, ses boutons et son pied :
 * quatre commandes faisaient un mur où l'on ne trouvait plus rien.
 *
 * La carte repliée garde ce qu'on cherche — numéro, boutique, état, montant,
 * jauge — et le reste s'ouvre d'un appui. **La commande en cours reste
 * ouverte** : c'est celle qu'on vient voir.
 */
const depliees = ref<Set<number>>(new Set())

const TERMINES = ['LIVREE', 'ANNULEE', 'REMBOURSEE', 'ECHEC_LIVRAISON']
const estDepliee = (commande: Commande) =>
  depliees.value.has(commande.id) || !TERMINES.includes(commande.statut_actuel)

function basculer(commande: Commande) {
  const suivant = new Set(depliees.value)
  if (suivant.has(commande.id)) suivant.delete(commande.id)
  else suivant.add(commande.id)
  depliees.value = suivant
}

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

/**
 * Les signalements en cours — O-5.
 *
 * *« Signaler un problème n'a pas de suite, n'est pas synchronisé aux autres
 * rôles, surtout l'admin. »* La suite existait — le vendeur a quarante-huit
 * heures pour donner sa version, puis un administrateur tranche — mais **le
 * client ne la voyait nulle part**. Un signalement dont on n'apprend jamais
 * l'issue est un formulaire, pas un recours.
 *
 * Le dossier s'affiche donc sur la commande concernée, avec ce qui manque
 * pour avancer : la réponse du vendeur, le délai, puis la décision.
 */
const litiges = ref<Record<number, Litige>>({})

const ETAPES_LITIGE: Record<string, string> = {
  OUVERT: 'La boutique a 48 h pour donner sa version.',
  EN_COURS: 'La boutique a répondu. Un administrateur va trancher.',
  RESOLU: 'Dossier tranché en votre faveur.',
  REJETE: 'Dossier tranché : la réclamation n’a pas été retenue.',
}

async function charger() {
  chargement.value = true
  try {
    commandes.value = await session.client.get<Commande[]>('/mes-commandes')
    const dossiers = await session.client.get<Litige[]>('/mes-litiges')
    litiges.value = Object.fromEntries(
      dossiers.map((dossier) => [dossier.id_commande, dossier]),
    )
  } finally {
    chargement.value = false
  }
}

useRafraichissement(charger, { periodique: true })

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

/**
 * Imprimer le reçu, ou l'enregistrer en PDF — O-5.
 *
 * *« Mon reçu, qui n'est pas imprimable. »* Le navigateur sait imprimer et
 * propose lui-même « Enregistrer au format PDF », y compris sur Android et
 * iOS : on ne refait pas son travail, on lui donne une feuille propre. La
 * règle d'impression tient en une phrase, la même que la facture du web
 * (D-78) : **tout ce qui sert à naviguer disparaît**.
 */
function imprimerRecu() {
  document.body.classList.add('impression-recu')
  // Le retrait après coup : sans lui, l'application resterait en mode
  // impression une fois la boîte de dialogue fermée.
  const nettoyer = () => document.body.classList.remove('impression-recu')
  window.addEventListener('afterprint', nettoyer, { once: true })
  window.print()
  setTimeout(nettoyer, 2000)
}

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
    succes.value = 'Signalement enregistré. La boutique a 48 heures pour répondre.'
    // On recharge : le dossier doit apparaître tout de suite sur la commande,
    // sinon on croit que rien ne s'est passé (O-5).
    await charger()
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
      <!-- L'en-tête EST le bouton : sur un téléphone, une petite flèche à
           viser au pouce est une flèche qu'on rate (O-8). -->
      <button type="button" class="entete" @click="basculer(commande)">
        <span class="min">
          <b>{{ commande.numero_commande }}</b>
          <span class="sous-titre">
            {{ jour(commande.date_commande) }} · {{ commande.boutiques.join(', ') }}
          </span>
        </span>
        <span class="droite">
          <IonBadge :color="TONS[tonDuStatut(commande.statut_actuel)]">
            {{ LIBELLES_STATUT[commande.statut_actuel] }}
          </IonBadge>
          <b class="prix">{{ euros(commande.montant_total_centimes) }}</b>
        </span>
        <IonIcon :icon="chevronDown" class="chevron"
                 :class="estDepliee(commande) ? 'ouvert' : ''" />
      </button>

      <!-- Repliée, la carte garde l'essentiel : où en est la commande. -->
      <span v-if="!estDepliee(commande)" class="jauge">
        <span
          v-for="(etape, index) in ETAPES_SUIVI[commande.type_service]"
          :key="etape"
          :class="index <= positionSuivi(commande.type_service, commande.statut_actuel)
            ? 'faite' : ''"
        />
      </span>

      <template v-if="estDepliee(commande)">
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
      <!-- La suite du signalement, là où on l'a ouvert (O-5) -->
      <div v-if="litiges[commande.id]" class="litige">
        <span class="entete-litige">
          <b>Signalement : {{ litiges[commande.id].libelle_motif }}</b>
          <IonBadge :color="litiges[commande.id].statut === 'RESOLU' ? 'success'
            : litiges[commande.id].statut === 'REJETE' ? 'medium' : 'warning'">
            {{ litiges[commande.id].libelle_statut }}
          </IonBadge>
        </span>
        <span class="etape">{{ ETAPES_LITIGE[litiges[commande.id].statut] }}</span>

        <span v-if="litiges[commande.id].reponse_vendeur" class="version">
          <b>La boutique répond</b>
          « {{ litiges[commande.id].reponse_vendeur }} »
        </span>
        <span v-else-if="litiges[commande.id].delai_expire" class="version">
          La boutique n’a pas répondu dans les 48 heures : un administrateur
          tranchera avec ce qu’il a.
        </span>

        <span v-if="litiges[commande.id].resolution" class="version">
          <b>Décision</b>
          {{ litiges[commande.id].resolution }}
          <template v-if="litiges[commande.id].montant_rembourse_centimes">
            — {{ euros(litiges[commande.id].montant_rembourse_centimes) }} remboursés.
          </template>
        </span>
      </div>

      <!-- Trois boutons de largeur inégale qui passent à la ligne donnent une
           rangée bancale — tu l'as dit : « mal positionnés et laids » (O-5).
           Une grille à parts égales, symbole au-dessus du mot : ils font la
           même taille quel que soit le texte, et ils restent sur une ligne. -->
      <div v-if="estContestable(commande) || aUnRecu(commande)" class="actions">
        <button v-if="aUnRecu(commande)" type="button" class="geste"
                @click="ouvrirRecu(commande)">
          <IonIcon :icon="documentTextOutline" />
          <span>Mon reçu</span>
        </button>
        <button v-if="estNotable(commande)" type="button" class="geste"
                @click="ouvrirAvis(commande)">
          <IonIcon :icon="starOutline" />
          <span>Mon avis</span>
        </button>
        <button
          v-if="estContestable(commande) && !litiges[commande.id]"
          type="button"
          class="geste danger"
          @click="ouvrirLitige(commande)"
        >
          <IonIcon :icon="shieldOutline" />
          <span>Un problème</span>
        </button>
      </div>
      </template>
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
            TVA {{ (facture.taux_tva * 100).toFixed(0) }} % incluse.
          </span>

          <!-- « Mon reçu n'est pas imprimable » (O-5). Le navigateur sait
               imprimer ET proposer « Enregistrer en PDF » : on ne refait pas
               son travail, on lui donne une feuille propre. Tout ce qui sert à
               naviguer disparaît à l'impression. -->
          <IonButton size="small" fill="outline" @click="imprimerRecu">
            <IonIcon :icon="printOutline" slot="start" /> Imprimer ou enregistrer
          </IonButton>
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
.litige {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-top: 12px;
  padding: 10px 12px;
  border-radius: 10px;
  background: #fff6ea;
  border: 1px solid #ffe2b3;
  font-size: 11.5px;
  line-height: 1.6;
  color: #7a4a06;
}
.entete-litige {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}
.entete-litige b {
  font-size: 12.5px;
}
.etape {
  font-weight: 600;
}
.version {
  display: block;
  padding-top: 6px;
  border-top: 1px solid #ffe2b3;
}
.version b {
  display: block;
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}
.actions {
  display: grid;
  grid-auto-flow: column;
  grid-auto-columns: 1fr;
  gap: 8px;
  margin-top: 12px;
  border-top: 1px solid var(--rd-trait-doux);
  padding-top: 10px;
}
.geste {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 9px 4px;
  border: 1px solid var(--rd-trait);
  border-radius: 10px;
  background: #fff;
  font-size: 10.5px;
  font-weight: 600;
  color: var(--ion-text-color);
}
.geste ion-icon {
  font-size: 17px;
  color: var(--accent);
}
.geste.danger,
.geste.danger ion-icon {
  color: #9c2116;
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
  align-items: center;
  gap: 10px;
  width: 100%;
  padding: 0;
  border: 0;
  background: none;
  text-align: left;
}
.entete .min {
  flex: 1;
  min-width: 0;
}
.entete b {
  display: block;
  font-size: 13.5px;
}
.entete .droite {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 3px;
  flex-shrink: 0;
}
.entete .prix {
  font-size: 13px;
  color: var(--accent);
}
.chevron {
  font-size: 15px;
  color: var(--rd-encre-douce);
  flex-shrink: 0;
  transition: transform 160ms ease;
}
.chevron.ouvert {
  transform: rotate(180deg);
}
.jauge {
  display: flex;
  gap: 4px;
  margin-top: 10px;
}
.jauge span {
  flex: 1;
  height: 4px;
  border-radius: 99px;
  background: var(--rd-trait);
}
.jauge span.faite {
  background: var(--accent);
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
